#from pool import PseudoCounterController, PoolUtil
import time
import array
import math
import PyTango

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController

from sardana.pool.controller import MemorizedNoInit, NotMemorized, Memorized

class PseudoCoTwoTangoAtt(PseudoCounterController):
    """ A pseudo counter which value is a formula from two tango
    device attributes.  The 'Formula' that allows the user to define
    an expression that will be evaluated e.g. 'VALUE1 / VALUE2'."""

    # NO COUNTERS NEEDED
    counter_roles = ()

    # THE EXTRA ATTRIBUTES EXTERNALATTRIBUTE AND FORMULA FOR THE PSEUDO COUNTER
    ctrl_extra_attributes ={'ExternalAttribute1':
                            {'Type':'PyTango.DevString'
                             ,'Description':'The first Tango Attribute to read (e.g. my/tango/dev/attr)'
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            ,'ExternalAttribute2':
                            {'Type':'PyTango.DevString'
                             ,'Description':'The second Tango Attribute to read (e.g. my/tango/dev/attr)'
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            ,'Formula':
                            {'Type':'PyTango.DevString'
                             ,'Description':'The Formula to get the REAL VALUE.\ne.g. "VALUE1/VALUE2"'
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            }

    FORMULA = 'Formula'
    EXTERNALATTRIBUTE1 = 'ExternalAttribute1'
    EXTERNALATTRIBUTE2 = 'ExternalAttribute2'
    ATTRIBUTE1 = 'Attribute1'
    ATTRIBUTE2 = 'Attribute2'
    
    
    def __init__(self,inst,props,*args,**kwargs):
        
        PseudoCounterController.__init__(self,inst,props,*args,**kwargs)
        self.counterExtraAttributes = {}
        self.counterExtraAttributes[0] = {self.FORMULA:"VALUE1/VALUE2",
                                self.EXTERNALATTRIBUTE1:"",self.ATTRIBUTE1:"",
                                self.EXTERNALATTRIBUTE2:"",self.ATTRIBUTE2:""}
        self.device_proxy1 = None
        self.device_proxy2 = None

    def calc(self,counter_values):
        """ Ignore counter values and return the evaluation of the formula"""
        try:
            attribute1 = self.counterExtraAttributes[0][self.ATTRIBUTE1]
            attribute2 = self.counterExtraAttributes[0][self.ATTRIBUTE2]
            VALUE1 = self.device_proxy1.read_attribute(attribute1).value
            VALUE2 = self.device_proxy2.read_attribute(attribute2).value
            return eval(self.counterExtraAttributes[0][self.FORMULA])
        except PyTango.DevFailed, df:
            print "error in  %s.calc: %s" % (self.inst_name, str(df[-1]))
        except Exception, e:
            print "error in  %s.calc: %s" % (self.inst_name, str(e))
        return -1

    def GetExtraAttributePar(self,counter,name):
        # IMPLEMENTED THE EXTRA ATTRIBUTE 'Formula','ExternalAttribute1','ExternalAttribute2'
        return self.counterExtraAttributes[counter][name]


    def SetExtraAttributePar(self,counter,name,value):
        # IMPLEMENTED THE EXTRA ATTRIBUTE 'Formula','ExternalAttribute1','ExternalAttribute2'
        self.counterExtraAttributes[counter][name] = value
        try:
            if name == self.EXTERNALATTRIBUTE1 or name == self.EXTERNALATTRIBUTE2:
                idx = value.rfind("/")
                device =  value[:idx]
                attribute = value[idx+1:]
                if name == self.EXTERNALATTRIBUTE1:
                    self.counterExtraAttributes[counter][self.ATTRIBUTE1] = attribute
                    self.device_proxy1 = PoolUtil().get_device(self.inst_name,device)
                else:
                    self.counterExtraAttributes[counter][self.ATTRIBUTE2] = attribute
                    self.device_proxy2 = PoolUtil().get_device(self.inst_name,device)
        except PyTango.DevFailed, df:
            print "error in  %s.SetExtraAttributePar: %s" % (self.inst_name, str(df[-1]))
        except Exception, e:
            print "error in  %s.SetExtraAttributePar: %s" % (self.inst_name, str(e))


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
                   'hc':{'Type':'PyTango.DevDouble',
                         'Description':'hc',
                         'DefaultValue':12398.41856
                        },
                   'DiffrOrder':{'Type':'PyTango.DevDouble',
                              'Description':'Diffraction order',
                              'DefaultValue':1.0
                        },
                   'gr_ior':{'Type':'PyTango.DevString',
                              'Description':'Gr_x ioregister',
                        },
                   'm3_ior':{'Type':'PyTango.DevString',
                              'Description':'M3_x ioregister',
                        },
                  }
    ctrl_extra_attributes = { 
                             "offsetGrxLE":
                                  {'Type':'PyTango.DevDouble',
                                   'Description':'Offset for gr_x in LE (mrad)',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMxLE":
                                  {'Type':'PyTango.DevDouble',
                                   'Description':'Offset for m_x in LE (mrad)',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetGrxHE":
                                  {'Type':'PyTango.DevDouble',
                                   'Description':'Offset for gr_x in HE (mrad)',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMxHE":
                                  {'Type':'PyTango.DevDouble',
                                   'Description':'Offset for m_x in HE (mrad)',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "grSign":
                                  {'Type':'PyTango.DevInt',
                                   'Description':'Sign for gr pitch',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "mSign":
                                  {'Type':'PyTango.DevInt',
                                   'Description':'Sign for m3 pitch',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                            }

    counter_roles = ()
    pseudo_counter_roles = ('Energy','Cff')
    
    def __init__(self,inst,props, *args, **kwargs):
        PseudoCounterController.__init__(self,inst,props, *args, **kwargs)
        
        self.grPitch = PyTango.DeviceProxy(self.ik220_grPitch)
        self.mPitch = PyTango.DeviceProxy(self.ik220_mPitch)

        self.iorDP = PyTango.DeviceProxy(self.gr_ior)
        self.iorDP2 = PyTango.DeviceProxy(self.m3_ior)

        self.offsetGrxLE = 0.0
        self.offsetMxLE = 0.0
        self.offsetGrxHE = 0.0
        self.offsetMxHE = 0.0
        self.grSign = -1
        self.mSign = 1
        
        self.EnergyDP = PyTango.DeviceProxy('pm/energycff_ctrl/1')
        
    def calc(self,index,counter_values):
        """
        Return the energy and the Cff
        """
        gr = self.grSign * self.grPitch['Value'].value
        m = self.mSign * self.mPitch['Value'].value
        
        offsetG,offsetM = self.checkOffset()
        beta = self.toRadians(gr) - (math.pi/2.0) - offsetG
        theta = (math.pi/2.0) - (self.toRadians(m)) - offsetM
        alpha = (2.0*theta) + beta
        numerator = (math.sin(alpha) + math.sin(beta))
        denominator = (self.DiffrOrder * self.look_at_grx())
        wavelength = numerator / denominator
        
        if wavelength == 0.0:
            energy_physicalmot = 0.0
        else:
            energy_physicalmot = self.hc / wavelength
        #if self.FixedM2Pit: 
        Cff = math.cos(beta)/math.cos(alpha)
        if energy_physicalmot < 0 :
            #warning: wavelength se vuelve negativo ... ??????
            energy_physicalmot = energy_physicalmot *(-1) 
        
        # Real Energy is equal to the energy calculated by the encoders
        # minus an offset that depends on the same energy calculated by the 
        # encoders:
        # E_physicalmot = Ereal + offset
        # with offset = a*Ereal + b
        # This implies that: Ereal = (Ephysicalmot - b)/(1+a) 
        a_coeff = self.EnergyDP.a_offset_coeff
        b_coeff = self.EnergyDP.b_offset_coeff
        numerator = energy_physicalmot - b_coeff
        denominator = 1 + a_coeff
        energy = numerator / denominator
        
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
            
        return 600.0 * 1E-7

    def GetExtraAttributePar(self,axis,name):
        #self._log.debug("GetExtraAttributePar(%d,%s): Entering ...", axis, name)
        if name.lower() == "offsetgrxle":
            return self.offsetGrxLE
        if name.lower() == "offsetmxle":
            return self.offsetMxLE
        if name.lower() == "offsetgrxhe":
            return self.offsetGrxHE
        if name.lower() == "offsetmxhe":
            return self.offsetMxHE
        if name.lower() == "grsign":
            return self.grSign
        if name.lower() == "msign":
            return self.mSign

    def SetExtraAttributePar(self,axis,name,value):
        #self._log.debug("SetExtraAttributePar(%d,%s,%f): Entering ...", axis, name, value)
        if name.lower() == "offsetgrxle":
            self.offsetGrxLE = value
        if name.lower() == "offsetmxle":
            self.offsetMxLE = value
        if name.lower() == "offsetgrxhe":
            self.offsetGrxHE = value
        if name.lower() == "offsetmxhe":
            self.offsetMxHE = value
        if name.lower() == "grsign":
            self.grSign = value
        if name.lower() == "msign":
            self.mSign = value

    def checkOffset(self):
        offsetGrating,offsetMirror = 0.0,0.0
        if self.iorDP['Value'].value == 0:
            offsetGrating = self.offsetGrxLE/1000.0
        elif self.iorDP['Value'].value == 2:
            offsetGrating = self.offsetGrxHE/1000.0
        
        if self.iorDP2['Value'].value == 0:
            offsetMirror = self.offsetMxLE/1000.0
        elif self.iorDP2['Value'].value == 2:
            offsetMirror = self.offsetMxHE/1000.0

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
                return sum(angles[:3])/3.0
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

