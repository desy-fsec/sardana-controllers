from PyTango import DevState
from pool import CounterTimerController
from pool import ZeroDController
from pool import PoolUtil
import math

import tau

TANGO_ATTR = 'TangoAttribute'
FORMULA = 'Formula'
DEVICE = 'Device'
ATTRIBUTE = 'Attribute'
EVALUATED_VALUE = 'Evaluated_value'

TAU_ATTR = 'TauAttr'

class TangoAttrCTController(CounterTimerController):
    """This controller offers as many channels as the user wants.
    Each channel has two _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the counter
    +) Formula - Formula to evaluate using 'VALUE' as the tango attribute value
    As examples you could have:
    ch1.TangoExtraAttribute = 'my/tango/device/attribute1'
    ch1.Formula = '-1 * VALUE'
    ch2.TangoExtraAttribute = 'my/tango/device/attribute2'
    ch2.Formula = 'math.sqrt(VALUE)'
    ch3.TangoExtraAttribute = 'my_other/tango/device/attribute1'
    ch3.Formula = 'math.cos(VALUE)'
    """
                 
    ctrl_extra_attributes ={TANGO_ATTR:
                            {'Type':'PyTango.DevString'
                             ,'Description':'The first Tango Attribute to read (e.g. my/tango/dev/attr)'
                             ,'R/W Type':'PyTango.READ_WRITE'},
                            FORMULA:
                            {'Type':'PyTango.DevString'
                             ,'Description':'The Formula to get the desired value.\ne.g. "math.sqrt(VALUE)"'
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            }

    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"
                     
    MaxDevice = 1024

    def __init__(self, inst, props):
        CounterTimerController.__init__(self, inst, props)
        self.devsExtraAttributes = {}

    def AddDevice(self, axis):
        self._log.debug('AddDevice %d' % axis)
        self.devsExtraAttributes[axis] = {}
        self.devsExtraAttributes[axis][TANGO_ATTR] = None
        self.devsExtraAttributes[axis][FORMULA] = 'VALUE'
        self.devsExtraAttributes[axis][DEVICE] = None
        self.devsExtraAttributes[axis][ATTRIBUTE] = None
        self.devsExtraAttributes[axis][TAU_ATTR] = None
        
    def DeleteDevice(self, axis): 
        del self.devsExtraAttributes[axis]

    def PreStateAll(self):
        pass

    def StateAll(self):
        pass
            
    def StateOne(self, axis):
        return (DevState.ON, 'Always ON, just reading external Tango Attribute')

    def PreReadAll(self):
        #self.pre_read_all()
        pass
        
    def PreReadOne(self, axis):
        #self.pre_read_one(axis)
        pass

    def ReadAll(self):
        #self.read_all()
        pass

    def ReadOne(self, axis):
        dev = self.devsExtraAttributes[axis][DEVICE]
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        formula = self.devsExtraAttributes[axis][FORMULA]
        tau_attr = self.devsExtraAttributes[axis][TAU_ATTR]
        try:
            tango_read = tau_attr.read().value
            VALUE = tango_read
            value = VALUE # just in case 'VALUE' has been written in lowercase...
            evaluated_value = eval(formula)
            return evaluated_value
        except Exception,e:
            self._log.error('Exception reading attribute: %s.%s\n%s' % (dev,str(attr),str(e)))

        return value


    def AbortOne(self, axis):
        pass
        
    def PreStartAllCT(self):
        pass
    
    def StartOneCT(self, axis):
        pass
    
    def StartAllCT(self):
        pass
                 
    def LoadOne(self, axis, value):
        pass
    
    def GetExtraAttributePar(self, axis, name):
        return self.devsExtraAttributes[axis][name]

    def SetExtraAttributePar(self,axis, name, value):
        self._log.debug('SetExtraAttributePar [%d] %s = %s' % (axis, name, value))
        self.devsExtraAttributes[axis][name] = value
        if name == TANGO_ATTR:
            idx = value.rfind("/")
            dev = value[:idx]
            attr = value[idx+1:]
            self.devsExtraAttributes[axis][DEVICE] = dev
            self.devsExtraAttributes[axis][ATTRIBUTE] = attr
            try:
                self.devsExtraAttributes[axis][TAU_ATTR] = tau.Attribute(value)
            except Exception,e:
                self._log.error('Exception accessing the tango attribute: %s'%str(e))
        
    def SendToCtrl(self,in_data):
        return ""

