from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController

import time
import array
import math
import PyTango


class EnergyFromIK220(PseudoCounterController):
    """
    Pseudo counter controller for obtain the energy and cff using IK220
    positions intead of the motor positions.
    It's needed because we have detected that we are losing steps
    """
    
    class_prop = {'ik220_grPitch':{'Description':'The channel with the mean of IK220 values for grpitch',
                                   'Type':'PyTango.DevString'},
                  'ik220_mPitch':{'Description':'The channel with the mean of IK220 values for mpitch',
                                   'Type':'PyTango.DevString'},
                  'iorGrx':{'Type':'PyTango.DevString',
                             'Description':'IORegister for GRX: server/device/name'
                                },
                   'hc':{'Type':'PyTango.DevDouble',
                         'Description':'hc',
                         'DefaultValue':12398.41856
                        },
                   'DiffrOrder':{'Type':'PyTango.DevDouble',
                              'Description':'Offset to apply in the calculation of tetha',
                              'DefaultValue':1.0
                        },
                  }
    ctrl_extra_attributes = { 'offsetGr':
                                        {'Type':'PyTango.DevDouble',
                                         'Description':'Offset for Gr in mrad',
                                         'R/W Type':'PyTango.READ_WRITE'
                                        },
                              'offsetM2':
                                        {'Type':'PyTango.DevDouble',
                                         'Description':'Offset for M2 in mrad',
                                         'R/W Type':'PyTango.READ_WRITE'
                                        },
                            }

    counter_roles = ()
    pseudo_counter_roles = ('Energy','Cff')
    
    def __init__(self,inst,props, *args, **kwargs):
        PseudoCounterController.__init__(self,inst, props, *args, **kwargs)
        
        self.grPitch = PyTango.DeviceProxy(self.ik220_grPitch)
        self.mPitch = PyTango.DeviceProxy(self.ik220_mPitch)
        self.ior = PyTango.DeviceProxy(self.iorGrx)
        self.offsetGr = 2.42#mrad
        self.offsetM2 = 1.4406#mrad
        
    def calc(self,index,counter_values):
        """
        Return the energy and the Cff
        """
        gr = self.grPitch['Value'].value
        m = self.mPitch['Value'].value
        
        beta = self.toRadians(gr) - (math.pi/2.0) - (self.offsetGr/1000)
        theta = (math.pi/2.0) - (self.toRadians(m)) - (self.offsetM2/1000)
        alpha = (2.0*theta) + beta
        wavelength = (math.sin(alpha) + math.sin(beta)) / (self.DiffrOrder * self.look_at_grx())
        
        if wavelength == 0.0:
            energy = 0.0
        else:
            energy = self.hc / wavelength
        #if self.FixedM2Pit: 
        Cff = math.cos(beta)/math.cos(alpha)
        if energy < 0 : energy = energy *(-1) #warning: wavelength se vuelve negativo ... ??????
        
        if index == 1:
            return energy
        elif index == 2:
            return Cff
        
    def toRadians(self,degrees):
        """
        Function for pass the readings of the IKs in degrees to radians
        """
        rad = degrees * (math.pi/180.0)
        return rad
    
    def look_at_grx(self):
            
        iorPos = self.ior['Value'].value
        #@todo: this will change the offsets too
        if iorPos == 4:
            return 700.0 * 1E-7
        elif iorPos == 3:
            return 900.0 * 1E-7
        elif iorPos == 2:
            return 1200.0 * 1E-7
        else:
            return 0.0

    def GetExtraAttributePar(self,axis,name):
        #self._log.debug("GetExtraAttributePar(%d,%s): Entering ...", axis, name)
        if name.lower() == "offsetgr":
            return self.offsetGr
        if name.lower() == "offsetm2":
            return self.offsetM2

    def SetExtraAttributePar(self,axis,name,value):
        #self._log.debug("SetExtraAttributePar(%d,%s,%f): Entering ...", axis, name, value)
        if name.lower() == "offsetgr":
            self.offsetGr = value
        if name.lower() == "offsetm2":
            self.offsetM2 = value


class IK220_channels(PseudoCounterController):
    """ A pseudo counter ctrl with all IK220 channels."""

    class_prop = {'ik220_devname':{'Description':'The IK220 Tango Device.',
                               'Type' : 'PyTango.DevString'}
                  }
                                                              
    counter_roles = ()
    pseudo_counter_roles = ('chan1', 'chan2', 'chan3', 'chan4','chan5', 'chan6', 'chan7', 'chan8', 'mean1', 'mean2')

    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        util = PoolUtil()
        self.ik220_dev = util.get_device(self.inst_name,self.ik220_devname)


    def calc(self,index, counter_values):
        """ Return the corresponding value for the given index. """
        try:
            angles = self.ik220_dev.read_attribute('Angles').value
            if index == 9:
                return sum(angles[:4])/4
            elif index == 10:
                return sum(angles[4:8])/4
            else:
                return angles[index - 1]
        except:
            return 1e-100
                    

class ND287_channels(PseudoCounterController):
    """ A pseudo counter ctrl with all ND287 channels. """

    
    class_prop = {'serial_devname':{'Description':'The PySerial Tango Device.',
                               'Type' : 'PyTango.DevString'}
                  }
                                                              
    counter_roles = ()
    pseudo_counter_roles = ('chan1', 'chan2', 'mean')
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        util = PoolUtil()
        self.serial_dev = util.get_device(self.inst_name,self.serial_devname)
        try:
            self.serial_dev.open()
        except:
            pass
    
    def calc(self, index, counter_values):
        try:
            commands = ['A0100','T0107','A0100','T0107','T0107','T0107','T0107']
            sequence = '\x1b'+'\r\x1b'.join(commands)+'\r'
            cmd_list = array.array('B',sequence).tolist()
            self.serial_dev.write(cmd_list)
            time.sleep(0.5)
            ans_list = self.serial_dev.readline()
            values = array.array('B',ans_list).tostring()
            values = values.replace('\x00','')
            values = values.replace('\x02','')
            values = values.replace('\x06','')
            
            splitted = values.split('\r\n')
            chans = [float(splitted[0]), float(splitted[1]) ]
            
            if index == 3 :
                return sum(chans)/2
            else:
                return chans[index - 1]
        except Exception,e:
            print "Some exception found while getting values from nd287",e
            return 1e-100           

