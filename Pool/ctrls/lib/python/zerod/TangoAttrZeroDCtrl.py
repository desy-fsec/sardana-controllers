from PyTango import DevState
from pool import CounterTimerController
from pool import ZeroDController
from pool import PoolUtil

TANGO_ATTR = 'TangoAttribute'
FORMULA = 'Formula'
DEVICE = 'Device'
ATTRIBUTE = 'Attribute'
EVALUATED_VALUE = 'Evaluated_value'
INDEX_READ_ALL = 'Index_read_all'


class ReadTangoAttributes():
    """ Generic class that has as many devices as the user wants.
    Each device has a tango attribute and a formula and the 'hardware' tango calls
    are optimized in the sense that only one call per tango device is issued.
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
    
    def __init__(self):
        self.devsExtraAttributes = {}
        self.axis_by_tango_attribute = {}
        self.devices_to_read = {}
        self.axis_to_update = {}
        self.devs_values = []

    def add_device(self, axis):
        self._log.debug('AddDevice %d' % axis)
        self.devsExtraAttributes[axis] = {}
        self.devsExtraAttributes[axis][FORMULA] = 'VALUE'
        self.devsExtraAttributes[axis][TANGO_ATTR] = None
        self.devsExtraAttributes[axis][EVALUATED_VALUE] = None

    def delete_device(self, axis):
        del self.devsExtraAttributes[axis]

    def state_one(self, axis):
        return (DevState.ON, 'Always ON, just reading external Tango Attribute')


    def pre_read_all(self):
        self.devices_to_read = {}

    def pre_read_one(self, axis):
        dev = self.devsExtraAttributes[axis][DEVICE]
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        if not self.devices_to_read.has_key(dev):
            self.devices_to_read[dev] = []
        self.devices_to_read[dev].append(attr)
        index = self.devices_to_read[dev].index(attr)
        self.devsExtraAttributes[axis][INDEX_READ_ALL] = index

    def read_all(self):
        for dev in self.devices_to_read.keys():
            attributes = self.devices_to_read[dev]
            dev_proxy = PoolUtil().get_device(self.inst_name, dev)
            try:
                values = dev_proxy.read_attributes(attributes)
            except Exception,e:
                self._log.error('Exception reading attributes:%s.%s' % (dev,str(attributes)))
            for attr in attributes:
                axis = self.axis_by_tango_attribute[dev+'/'+attr]
                formula = self.devsExtraAttributes[axis][FORMULA]
                index = attributes.index(attr)
                VALUE = float(values[index].value)
                value = VALUE # just in case 'VALUE' has been written in lowercase...
                self.devsExtraAttributes[axis][EVALUATED_VALUE] = eval(formula)


    def read_one(self, axis):
        value = self.devsExtraAttributes[axis][EVALUATED_VALUE]
        return value

    def get_extra_attribute_par(self, axis, name):
        return self.devsExtraAttributes[axis][name]

    def set_extra_attribute_par(self,axis, name, value):
        self._log.debug('SetExtraAttributePar [%d] %s = %s' % (axis, name, value))
        self.devsExtraAttributes[axis][name] = value
        if name == TANGO_ATTR:
            idx = value.rfind("/")
            dev = value[:idx]
            attr = value[idx+1:]
            self.devsExtraAttributes[axis][DEVICE] = dev
            self.devsExtraAttributes[axis][ATTRIBUTE] = attr
            self.axis_by_tango_attribute[value] = axis


class TangoAttrZeroDController(ZeroDController, ReadTangoAttributes):
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
                 
    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"
                     
    MaxDevice = 1024

    def __init__(self, inst, props):
        ZeroDController.__init__(self, inst, props)
        ReadTangoAttributes.__init__(self)

    def AddDevice(self, axis):
        self.add_device(axis)

    def DeleteDevice(self, axis):
        self.delete_device(axis)

    def StateOne(self, axis):
        return self.state_one(axis)

    def PreReadAll(self):
        self.pre_read_all()
        
    def PreReadOne(self, axis):
        self.pre_read_one(axis)

    def ReadAll(self):
        self.read_all()

    def ReadOne(self, axis):
        return self.read_one(axis)

    def GetExtraAttributePar(self, axis, name):
        return self.get_extra_attribute_par(axis, name)

    def SetExtraAttributePar(self,axis, name, value):
        self.set_extra_attribute_par(axis, name, value)
        
    def SendToCtrl(self,in_data):
        return ""
