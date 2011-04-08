import time
from macro import Macro, ParamRepeat, Type
from macro import SScan
import tau
import traceback

class cycle_magnets(Macro):
    """ This macro is intended to be used for cycling the magnets.  It
    receives as parameters the number of cycles, the integration time
    after each change in the set point and a list of pool magnet names.

    For each magnet, it will retrive the min and max values of the
    CurrentSetPoint Tango Attribute.
    If min and max are set:
    +) abs(min) == max -> Bipolar cycling
    +) min == 0        -> Unipolar cycling
    +) any other condition will raise an exception providing enough
       info to fix the problem.
       
    WARNING: This macro will not set waveforms so do not use it with
    BO-PC-BEND or BO-PC-QUADS.
    """
    
    hints = { 'scan' : 'cycle_magnets' }
    env = ('ActiveMntGrp',)
    
    param_def = [
        ['nr_cycles', Type.Integer, None, 'Number of cycles for all magnets'],
        ['integ_time', Type.Float, None, 'Integration time'],
        ['magnets_list',
         ParamRepeat(['motor', Type.Motor, None, 'Magnet to cycle']),
         None, 'List of magnets to cycle']
    ]

    def prepare(self, *args, **opts):
        self.nr_cycles = args[0]
        self.integ_time = args[1]
        self.magnets = args[2:]
        
        self.name = opts.get('name','cycle_magnets')

        self.magnets_motion_group = self.getManager().getMotion(self.magnets)
        self.magnets_start_positions = []

        self.magnets_info = {}

        if self._get_magnets_info():
            
            self.info('Saving magnet currents: '+str(self.magnets_start_positions))

            generator = self._generator
            moveables = self.magnets
            env = opts.get('env',{})
            self._sScan = SScan(self, generator, moveables, env, [])
        else:
            raise Exception('Sorry, it is not possible to cycle these magnets')

    def _get_magnets_info(self):
        for magnet in self.magnets:
            magnet_name = magnet.getName()
            if magnet_name.upper() in ['BO_PC_BEND', 'BO_PC_QH01', 'BO_PC_QH02', 'BO_PC_QV01', 'BO_PC_QV02']:
                self.error("This macro is not intended to cycle using waveforms ('%s' magnet needs a waveform for cycling)." % magnet_name)
                return False
            try:
                # TO ACCESS TO SPECIFIC INFORMATION FOR CYCLING
                # WE NEED TO READ THE _REAL_ DEVICE THE MOTOR IS INTERFACING
                # AND GET IT'S CONFIGURATION
                tango_dev = magnet.getAttribute('TangoDevice').read().value
                
                tango_attr_name = tango_dev+'/CurrentSetpoint'
                tau_attr = tau.Attribute(tango_attr_name)
                
                min_value = float(tau_attr.getMinValue())
                max_value = float(tau_attr.getMaxValue()) 
                setpoint = float(tau_attr.getValueObj().w_value)
                
                self.magnets_info[magnet_name] = {}
                self.magnets_info[magnet_name]['ICMIN'] = min_value
                self.magnets_info[magnet_name]['ICMAX'] = max_value
                self.magnets_info[magnet_name]['SETPOINT'] = setpoint
                self.magnets_start_positions.append(setpoint)        
                self.info('%s: ICMAX = %f ; SETPOINT = (%s)' %
                          (magnet_name,
                           self.magnets_info[magnet_name]['ICMAX'],
                           self.magnets_info[magnet_name]['SETPOINT']))
            except Exception,e:
                e_str = str(e)
                msg = "An error occurred getting info for %s: %s" %(magnet_name, e_str)
                self.error(msg)
                return False 
        return True

    def _restore_magnet_positions(self):
        self.info('Restoring magnet currents: '+str(self.magnets_start_positions))
        self.magnets_motion_group.move(self.magnets_start_positions)
        
    def on_abort(self):
        self._restore_magnet_positions()

    def _generator0(self):
        step = {}
        step["integ_time"] =  self.integ_time
        step['hooks'] = []
        cycles = 0
        while cycles < self.nr_cycles:
            sign = 1.0
            if cycles % 2 == 1:
                sign = -1.0
            step["positions"] = []
            for magnet in self.magnets:
                magnet_name = magnet.getName()
                i_cycle_max = self.magnets_info[magnet_name]['ICMAX']
                cycle_polarity = self.magnets_info[magnet_name]['CYCLE_POLARITY']
                next_magnet_position = sign * i_cycle_max
                if cycle_polarity == 'UNIPOLAR' and sign == -1.0:
                    next_magnet_position = 0
                step['positions'].append(next_magnet_position)
            cycles += 1 
            yield step
    
    def _generator(self):
        step = {}
        step["integ_time"] =  self.integ_time
        cycles = 0
        while cycles < self.nr_cycles:
	    step["positions"] = []
            for magnet in self.magnets:
                magnet_name = magnet.getName()
                mi = self.magnets_info[magnet_name]
                i_min = mi['ICMIN']
                i_max = mi['ICMAX']
                i_next = i_min if cycles % 2 == 0 else i_max    
                step['positions'].append(i_next)
            cycles += 1
            self.debug(repr(step))
            yield step
	      

    def run(self,*args):
        # This allows to have a progress status integrated in a GUI
        self.nr_points = self.nr_cycles
        #for s in self._sScan.scan():
        #    yield s
        self._sScan.scan()
        self._restore_magnet_positions()

    @property
    def data(self):
        return self._sScan.data
