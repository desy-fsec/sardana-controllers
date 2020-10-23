import PyTango

# import time

from sardana import DataAccess
# from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class HasyDACCtrl(MotorController):
    """This class is the Tango Sardana Motor controller
    for standard Hasylab DACs"""

    axis_attributes = {
        'VoltageMax': {Type: float, Access: ReadWrite},
        'VoltageMin': {Type: float, Access: ReadWrite},
        'TangoDevice': {Type: str, Access: ReadOnly},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the Motor Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "Motor"
    model = "Hasylab DAC"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        MotorController.__init__(self, inst, props, *args, **kwargs)

        if self.TangoHost is None:
            self.db = PyTango.Database()
        else:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find(':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int(lst[1])
            self.db = PyTango.Database(self.node, self.port)

        name_dev_ask = self.RootDeviceName + "*"
        self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.device_available = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.max_device = self.max_device + 1
        self.dft_VoltageMax = 0
        self.VoltageMax = []
        self.dft_VoltageMin = 0
        self.VoltageMin = []

    def AddDevice(self, ind):
        MotorController.AddDevice(self, ind)
        if ind > self.max_device:
            print("False index")
            return
        proxy_name = self.tango_device[ind - 1]
        if self.TangoHost is None:
            proxy_name = self.tango_device[ind - 1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(self.tango_device[ind - 1])
        self.proxy[ind - 1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind - 1] = 1
        self.VoltageMax.append(self.dft_VoltageMax)
        self.VoltageMin.append(self.dft_VoltageMin)

    def DeleteDevice(self, ind):
        MotorController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        status_template = "STATE(%s) LIM+(%s) LIM-(%s)"
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            switchstate = 0
            if sta == PyTango.DevState.ON:
                status_template = "DAC is iddle"
            else:
                status_template = "DAC is in error"
            status_string = status_template
            tup = (sta, status_string, switchstate)
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        if self.device_available[ind - 1] == 1:
            return self.proxy[ind - 1].read_attribute("Voltage").value

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, pos):
        return True

    def StartOne(self, ind, pos):
        if self.device_available[ind - 1] == 1:
            self.proxy[ind - 1].write_attribute("Voltage", pos)

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "VoltageMax":
                return float(self.proxy[ind - 1].read_attribute(
                    "VoltageMax").value)
            elif name == "VoltageMin":
                return float(self.proxy[ind - 1].read_attribute(
                    "VoltageMin").value)
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "VoltageMax":
                self.proxy[ind - 1].write_attribute("VoltageMax", value)
            elif name == "VoltageMin":
                self.proxy[ind - 1].write_attribute("VoltageMin", value)

    def StartAll(self):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def AbortOne(self, ind):
        pass

    def DefinePosition(self, ind, position):
        pass

    def __del__(self):
        print("PYTHON -> HasyDACCtrl dying")
