from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController
from sardana.pool.controller import MemorizedNoInit, NotMemorized, Memorized

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
    ctrl_extra_attributes = { 
                             "offsetGrLE":
                                        {'Type':'PyTango.DevDouble',
                                         'memorized': Memorized,
                                         'R/W Type':'PyTango.READ_WRITE',
                                        },
                             "offsetMLE":
                                        {'Type':'PyTango.DevDouble',
                                         'memorized': Memorized,
                                         'R/W Type':'PyTango.READ_WRITE',
                                        },
                             "offsetGrME":
                                        {'Type':'PyTango.DevDouble',
                                         'memorized': Memorized,
                                         'R/W Type':'PyTango.READ_WRITE',
                                        },
                             "offsetMME":
                                        {'Type':'PyTango.DevDouble',
                                         'memorized': Memorized,
                                         'R/W Type':'PyTango.READ_WRITE',
                                        },
                             "offsetGrHE":
                                        {'Type':'PyTango.DevDouble',
                                         'memorized': Memorized,
                                         'R/W Type':'PyTango.READ_WRITE',
                                        },
                             "offsetMHE":
                                        {'Type':'PyTango.DevDouble',
                                         'memorized': Memorized,
                                         'R/W Type':'PyTango.READ_WRITE',
                                        },
                            }

    counter_roles = ()
    pseudo_counter_roles = ('Energy','Cff')
    
    def __init__(self,inst,props, *args, **kwargs):
        PseudoCounterController.__init__(self,inst, props, *args, **kwargs)
        
        self.grPitch = PyTango.DeviceProxy(self.ik220_grPitch)
        self.mPitch = PyTango.DeviceProxy(self.ik220_mPitch)
        self.ior = PyTango.DeviceProxy(self.iorGrx)
        #self.offsetGr = 2.42#mrad
        #self.offsetM2 = 1.4406#mrad
        
        self.offsetGrLE = 0.0
        self.offsetMLE = 0.0
        self.offsetGrHE = 0.0
        self.offsetMHE = 0.0
        self.offsetGrME = 0.0
        self.offsetMME = 0.0
        
    def calc(self,index,counter_values):
        """
        Return the energy and the Cff
        """
        gr = self.grPitch['Value'].value
        m = self.mPitch['Value'].value
        
        offsetG,offsetM = self.checkOffset()
        
        beta = self.toRadians(gr) - (math.pi/2.0) - offsetG
        theta = (math.pi/2.0) - (self.toRadians(m)) + offsetM
        alpha = (2.0*theta) + beta
        wavelength = (math.sin(alpha) + math.sin(beta)) / (self.DiffrOrder * self.look_at_grx())
        
        if wavelength == 0.0:
            energy = 0.0
        else:
            energy = self.hc / wavelength
        
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
            
        if name.lower() == "offsetgrle":
            return self.offsetGrLE 
        
        if name.lower() == "offsetmle":
            return self.offsetMLE 

        if name.lower() == "offsetgrme":
            return self.offsetGrME 
        
        if name.lower() == "offsetmme":
            return self.offsetMME
        
        if name.lower() == "offsetgrhe":
            return self.offsetGrHE 
        
        if name.lower() == "offsetmhe":
            return self.offsetMHE

    def SetExtraAttributePar(self,axis,name,value):
        #self._log.debug("SetExtraAttributePar(%d,%s,%f): Entering ...", axis, name, value)
            
        if name.lower() == "offsetgrle":
            self.offsetGrLE = value
        
        if name.lower() == "offsetmle":
            self.offsetMLE = value

        if name.lower() == "offsetgrme":
            self.offsetGrME = value
        
        if name.lower() == "offsetmme":
            self.offsetMME = value
             
        if name.lower() == "offsetgrhe":
            self.offsetGrHE = value
        
        if name.lower() == "offsetmhe":
            self.offsetMHE = value
            
    def checkOffset(self):
        offsetGrating,offsetMirror = 0.0, 0.0
        
        if self.ior['Value'].value == 4:
            offsetGrating = self.offsetGrLE/1000.0
            offsetMirror = self.offsetMLE/1000.0
        
        elif self.ior['Value'].value == 3:
            offsetGrating = self.offsetGrME/1000.0
            offsetMirror = self.offsetMME/1000.0
        
        if self.ior['Value'].value == 2:
            offsetGrating = self.offsetGrHE/1000.0
            offsetMirror = self.offsetMHE/1000.0
        
        return offsetGrating, offsetMirror


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
                return sum(angles[:4])/4.0
            elif index == 10:
                return sum(angles[4:8])/4.0
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
                return sum(chans)/2.0
            else:
                return chans[index - 1]
        except Exception,e:
            print "Some exception found while getting values from nd287",e
            return 1e-100           

