import math

from sardana.macroserver.macro import Type, Macro, Hookable
from sardana.macroserver.scan import SScan
from sardana.macroserver.macros.scan import ascan, getCallable, UNCONSTRAINED

EV2REVA = 0.2624682843

class constKscan(Macro, Hookable):
    """"""

    param_def = [
       ['motor',            Type.Moveable,   None, 'Motor to move'],
       ['start_pos',        Type.Float,   None, 'Scan start position'],
       ['final_pos',        Type.Float,   None, 'Scan final position'],
       ['edge_pos',         Type.Float,   None, 'Edge position'],
       ['step_size_k',      Type.Float,   None, 'Scan step size k'],
       ['start_integ_time', Type.Float,   None, 'Start integration time'],
       ['pow_integ_time',   Type.Float,   None, 'Power integration time']
    ]
    
    def __calc_pos(self, i, edge_pos, step_size_k):
        pos = edge_pos + (i * step_size_k) ** 2 / EV2REVA
        return pos

    def prepare(self, *args, **opts):                        
        motor = args[0]
        start_pos = args[1]
        final_pos = args[2]
        edge_pos = args[3]
        step_size_k = args[4]

        #precalculate positions to get know nr of scan points
        self.nr_points,i = 0,1
        while True:
            pos = self.__calc_pos(i,edge_pos,step_size_k)
            i += 1
            if pos < start_pos:
                continue
            elif pos > final_pos:
                break
            self.nr_points += 1

        generator=self._generator
        moveables=[motor]
        env=opts.get('env',{})
        constrains=[getCallable(cns) for cns in opts.get('constrains',[UNCONSTRAINED])]
        
        self.pre_scan_hooks = self.getHooks('pre-scan')
        self.post_scan_hooks = self.getHooks('post-scan')
        self._gScan=SScan(self, generator, moveables, env, constrains)
        
    def _generator(self):
        args = self.getParameters()
        start_pos = args[1]
        final_pos = args[2]
        edge_pos = args[3]
        step_size_k = args[4]
        start_integ_time = args[5]
        pow_integ_time = args[6]

        step = {}
        step["pre-move-hooks"] = self.getHooks('pre-move')
        step["post-move-hooks"] = self.getHooks('post-move')
        step["pre-acq-hooks"] = self.getHooks('pre-acq')
        step["post-acq-hooks"] = self.getHooks('post-acq') + self.getHooks('_NOHINTS_')
        step["post-step-hooks"] = self.getHooks('post-step')
        
        step["check_func"] = []

        point_id,i = 0,1
        while True:
            pos = self.__calc_pos(i,edge_pos,step_size_k)
            i += 1
            if pos < start_pos:
                continue
            elif pos > final_pos:
                break
            if point_id == 0: first_pos = pos
            t = start_integ_time * ((pos - edge_pos)/(first_pos - edge_pos)) ** (pow_integ_time * 0.5)
            step["positions"] = [pos]
            step["integ_time"] = t
            step["point_id"] = point_id
            yield step
            point_id += 1
    
    def run(self,*args):
        for step in self._gScan.step_scan():
            yield step

    @property
    def data(self):
        return self._gScan.data

#class rscan(ascan): 
    #"""Do an absolute scan of the specified motor.
    #ascan scans one motor, as specified by motor. The motor starts at the
    #position given by start_pos and ends at the position given by final_pos.
    #The step size is given by a step_size parameter. The number of data points collected
    #will be floor((final_pos - start_pos)/step_size) + 1. Count time is given by time which if positive,
    #specifies seconds and if negative, specifies monitor counts. """

    #param_def = [
       #['motor',      Type.Motor,   None, 'Motor to move'],
       #['start_pos',  Type.Float,   None, 'Scan start position'],
       #['final_pos',  Type.Float,   None, 'Scan final position'],
       #['step_size',  Type.Float, None, 'Scan step size'],
       #['integ_time', Type.Float,   None, 'Integration time']
    #]

    #def prepare(self, motor, start_pos, final_pos, step_size, integ_time,
                #**opts):
        #nr_interv = math.floor(abs(final_pos - start_pos)/step_size)
        #final_pos = start_pos + step_size * nr_interv
        #self._prepare([motor], [start_pos], [final_pos], nr_interv, integ_time, **opts)
        
        
#class xxx(Macro):
    
    #param_def = [
       #['motor',      Type.Motor,   None, 'Motor check pos']
    #]
    
##    def #prepare(self, motor, **opts):
        
    
    #def run(self, motor, **opts):
        #self.execMacro("lsenv")
    