import math
import PyTango

from sardana import State, DataAccess
from sardana.pool.controller import ZeroDController
from sardana.pool.controller import Type, Access, Description
from sardana.pool import PoolUtil

TANGO_ATTR = 'TangoAttribute'
FORMULA = 'Formula'
DEVICE = 'Device'
ATTRIBUTE = 'Attribute'
EVALUATED_VALUE = 'Evaluated_value'
INDEX_READ_ALL = 'Index_read_all'


class ReadTangoAttributes():
    """ Generic class that has as many devices as the user wants.
    Each device has a Tango attribute and a formula and the 'hardware' Tango
    calls are optimized in the sense that only one call per Tango device is
    issued.
    """
    axis_attributes = {
        TANGO_ATTR: {
            Type: str,
            Description: 'The first Tango Attribute to read'\
                ' (e.g. my/tango/dev/attr)',
            Access: DataAccess.ReadWrite
        },
        FORMULA:{
            Type: str,
            Description: 'The Formula to get the desired value.\n'\
                ' e.g. "math.sqrt(VALUE)"',
            Access: DataAccess.ReadWrite
        }
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
        return (State.On, 'Always ON, just reading external Tango Attribute')

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
            except PyTango.DevFailed, e:
                for attr in attributes:
                    axis = self.axis_by_tango_attribute[dev + '/' + attr]
                    self.devsExtraAttributes[axis][EVALUATED_VALUE] = e
            except Exception, e:
                self._log.error('Exception reading attributes:%s.%s' %
                                (dev, str(attributes)))
            for attr in attributes:
                axis = self.axis_by_tango_attribute[dev + '/' + attr]
                formula = self.devsExtraAttributes[axis][FORMULA]
                index = attributes.index(attr)
                dev_attr_value = values[index]
                if dev_attr_value.has_failed:
                    VALUE = PyTango.DevFailed(*dev_attr_value.get_err_stack())
                    self.devsExtraAttributes[axis][EVALUATED_VALUE] = VALUE
                else:
                    VALUE = float(dev_attr_value.value)
                    # just in case 'VALUE' has been written in lowercase...
                    value = VALUE
                    self.devsExtraAttributes[axis][
                        EVALUATED_VALUE] = eval(formula)

    def read_one(self, axis):
        value = self.devsExtraAttributes[axis][EVALUATED_VALUE]
        if isinstance(value, PyTango.DevFailed):
            raise value
        return value

    def get_axis_extra_par(self, axis, name):
        return self.devsExtraAttributes[axis][name]

    def set_axis_extra_par(self, axis, name, value):
        self._log.debug(
            'set_axis_extra_par [%d] %s = %s' % (axis, name, value))
        self.devsExtraAttributes[axis][name] = value
        if name == TANGO_ATTR:
            idx = value.rfind("/")
            dev = value[:idx]
            attr = value[idx + 1:]
            self.devsExtraAttributes[axis][DEVICE] = dev
            self.devsExtraAttributes[axis][ATTRIBUTE] = attr
            self.axis_by_tango_attribute[value] = axis


class TangoAttrZeroDController(ZeroDController, ReadTangoAttributes):
    """This controller offers as many channels as the user wants.

    Each channel has two _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the 0D
    +) Formula - Formula to evaluate using 'VALUE' as the Tango attribute value

    As examples you could have:
        ch1.TangoAttribute = 'my/tango/device/attribute1'
        ch1.Formula = '-1 * VALUE'
        ch2.TangoAttribute = 'my/tango/device/attribute2'
        ch2.Formula = 'math.sqrt(VALUE)'
        ch3.TangoAttribute = 'my_other/tango/device/attribute1'
        ch3.Formula = 'math.cos(VALUE)'
    """

    gender = ""
    model = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    MaxDevice = 1024

    axis_attributes = ReadTangoAttributes.axis_attributes

    def __init__(self, inst, props, *args, **kwargs):
        ZeroDController.__init__(self, inst, props, *args, **kwargs)
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

    def GetAxisExtraPar(self, axis, name):
        return self.get_axis_extra_par(axis, name)

    def SetAxisExtraPar(self, axis, name, value):
        self.set_axis_extra_par(axis, name, value)

    def SendToCtrl(self, in_data):
        return ""
