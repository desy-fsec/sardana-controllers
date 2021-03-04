import math  # noqa: F401
import tango
from sardana.pool import PoolUtil
from sardana.pool.controller import CounterTimerController, Type, \
    Description, Access, DataAccess
from sardana import State


TANGO_ATTR = 'TangoAttribute'
FORMULA = 'Formula'
DEVICE = 'Device'
ATTRIBUTE = 'Attribute'
EVALUATED_VALUE = 'Evaluated_value'
INDEX_READ_ALL = 'Index_read_all'


class ReadTangoAttributes:
    """
    Generic class that has as many devices as the user wants.
    Each device has a tango attribute and a formula and the 'hardware' tango
    calls are optimized in the sense that only one call per tango device is
    issued.
    """
    axis_attributes = {
        TANGO_ATTR: {Type: str,
                     Description: 'The first Tango Attribute to read (e.g. '
                                  'my/tango/dev/attr)',
                     Access: DataAccess.ReadWrite},
        FORMULA: {Type: str,
                  Description: 'The Formula to get the desired value.\ne.g. '
                               '"math.sqrt(VALUE)"',
                  Access: DataAccess.ReadWrite}
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
        return State.On, 'Always ON, just reading external Tango Attribute'

    def pre_read_all(self):
        self.devices_to_read = {}

    def pre_read_one(self, axis):
        dev = self.devsExtraAttributes[axis][DEVICE]
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        if dev not in self.devices_to_read:
            self.devices_to_read[dev] = []
        self.devices_to_read[dev].append(attr)
        index = self.devices_to_read[dev].index(attr)
        self.devsExtraAttributes[axis][INDEX_READ_ALL] = index

    def read_all(self):
        try:
            for dev in self.devices_to_read:
                attributes = self.devices_to_read[dev]
                values = {}
                try:
                    dev_proxy = PoolUtil().get_device(self.GetName(), dev)
                    # Set the list to prevent duplicated attr names
                    # Tango raise exception on read_attributes if there are
                    # duplicated attributes
                    attrs = list(set(attributes))
                    r_values = dev_proxy.read_attributes(attrs)
                    values = dict(list(zip(attrs, r_values)))
                except tango.DevFailed as e:
                    # In case of DeviceServer error
                    for attr in attributes:
                        axis = self.axis_by_tango_attribute[dev + '/' + attr]
                        self.devsExtraAttributes[axis][EVALUATED_VALUE] = e
                    self._log.debug("Exception on read the attribute:%r" % e)
                except Exception:
                    self._log.error(
                        'Exception reading attributes:%s.%s' % (
                            dev, str(attributes)))
            for attr in attributes:
                axies = []
                for axis, dic in self.devsExtraAttributes.items():
                    if dic[TANGO_ATTR] == dev + '/' + attr:
                        axies.append(axis)
                for axis in axies:
                    if len(values) > 0:
                        dev_attr_value = values[attr]
                        if dev_attr_value.has_failed:
                            # In case of Attribute error
                            VALUE = tango.DevFailed(
                                *dev_attr_value.get_err_stack())
                            self.devsExtraAttributes[axis][EVALUATED_VALUE] = \
                                VALUE
                        else:
                            formula = self.devsExtraAttributes[axis][FORMULA]
                            VALUE = float(dev_attr_value.value)
                            # just in case 'VALUE' has been written
                            # in lowercase...
                            value = VALUE  # noqa: F841
                            v = eval(formula)
                            self.devsExtraAttributes[axis][EVALUATED_VALUE] = v
        except Exception as e:
            self._log.error('Exception on read_all: %r' % e)

    def read_one(self, axis):
        value = self.devsExtraAttributes[axis][EVALUATED_VALUE]
        if isinstance(value, tango.DevFailed):
            raise value
        return value

    def get_extra_attribute_par(self, axis, name):
        return self.devsExtraAttributes[axis][name]

    def set_extra_attribute_par(self, axis, name, value):
        value = value.lower()
        self._log.debug('SetExtraAttributePar [%d] %s = %s' % (
            axis, name, value))
        self.devsExtraAttributes[axis][name] = value
        if name == TANGO_ATTR:
            idx = value.rfind("/")
            dev = value[:idx]
            attr = value[idx+1:]
            self.devsExtraAttributes[axis][DEVICE] = dev
            self.devsExtraAttributes[axis][ATTRIBUTE] = attr
            self.axis_by_tango_attribute[value] = axis


class TangoAttrCTController(ReadTangoAttributes, CounterTimerController):
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
    model = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    MaxDevice = 1024

    def __init__(self, inst, props, *args, **kwargs):
        ReadTangoAttributes.__init__(self)
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)

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
        return self.get_extra_attribute_par(axis, name)

    def SetAxisExtraPar(self, axis, name, value):
        self.set_extra_attribute_par(axis, name, value)

    def SendToCtrl(self, in_data):
        return ""

    def AbortOne(self, axis):
        pass

    def PreStartAll(self):
        pass

    def StartOne(self, axis, value):
        pass

    def StartAll(self):
        pass

    def LoadOne(self, axis, value, repetitions, latency):
        pass
