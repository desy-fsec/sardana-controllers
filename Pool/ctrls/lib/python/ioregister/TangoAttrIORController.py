from PyTango import DevState
from pool import IORegisterController
from pool import PoolUtil

TANGO_ATTR = 'TangoAttribute'
DEVICE = 'Device'
ATTRIBUTE = 'Attribute'


class TangoAttrIORController(IORegisterController):
    """This controller offers as many channels as the user wants.
    Each channel has two _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the counter
    As examples you could have:
    ch1.TangoExtraAttribute = 'my/tango/device/attribute1'
    ch2.TangoExtraAttribute = 'my/tango/device/attribute2'
    ch3.TangoExtraAttribute = 'my_other/tango/device/attribute1'
    """
                 
    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"
                     
    ctrl_extra_attributes ={TANGO_ATTR:
                            {'Type':'PyTango.DevString'
                             ,'Description':'The first Tango Attribute to read (e.g. my/tango/dev/attr)'
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            }
    MaxDevice = 1024

    def __init__(self, inst, props):
        IORegisterController.__init__(self, inst, props)
        self.devsExtraAttributes = {}

    def AddDevice(self, axis):
        self._log.debug('AddDevice %d' % axis)
        self.devsExtraAttributes[axis] = {}
        self.devsExtraAttributes[axis][TANGO_ATTR] = None

    def DeleteDevice(self, axis):
        del self.devsExtraAttributes[axis]

    def StateOne(self, axis):
        return (DevState.ON, 'Always ON, just reading external Tango Attribute')

    def ReadOne(self, axis):
        dev = self.devsExtraAttributes[axis][DEVICE]
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        dev_proxy = PoolUtil().get_device(self.inst_name, dev)
        try:
            value = dev_proxy.read_attribute(attr).value
            return int(value)
        except Exception,e:
            self._log.error('Exception reading attribute:%s.%s' % (dev,attr))

    def WriteOne(self, axis, value):
        dev = self.devsExtraAttributes[axis][DEVICE]
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        dev_proxy = PoolUtil().get_device(self.inst_name, dev)
        try:
            dev_proxy.write_attribute(attr, value)
        except Exception, e:
            self._log.error('Exception writing attribute:%s.%s' % (dev,attr))

    def GetExtraAttributePar(self, axis, name):
        return self.devsExtraAttributes[axis][name]

    def SetExtraAttributePar(self,axis, name, value):
        self._log.info('SetExtraAttributePar [%d] %s = %s' % (axis, name, value))
        self.devsExtraAttributes[axis][name] = value
        if name == TANGO_ATTR:
            idx = value.rfind("/")
            dev = value[:idx]
            attr = value[idx+1:]
            self.devsExtraAttributes[axis][DEVICE] = dev
            self.devsExtraAttributes[axis][ATTRIBUTE] = attr
        
    def SendToCtrl(self,in_data):
        return ""
