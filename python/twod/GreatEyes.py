import PyTango
# import time, os

from sardana import DataAccess
# from sardana import State, DataAccess
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class GreatEyesCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the GreatEyes"

    axis_attributes = {
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the GreatEyes Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    MaxDevice = 97

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        TwoDController.__init__(self, inst, props, *args, **kwargs)

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
        self.started = False

    def AddDevice(self, ind):
        TwoDController.AddDevice(self, ind)
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

    def DeleteDevice(self, ind):
        TwoDController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta, "Camera ready")
            elif sta == PyTango.DevState.MOVING:
                tup = (sta, "Camera busy")
            elif sta == PyTango.DevState.RUNNING:
                sta = PyTango.DevState.MOVING
                tup = (sta, "Camera busy")
            elif sta == PyTango.DevState.FAULT:
                tup = (sta, "Camera in FAULT state")
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, value):
        self.proxy[ind - 1].command_inout("PrepareAcq")
        return True

    def StartOne(self, ind, position=None):
        self.proxy[ind - 1].command_inout("StartAcq")

    def AbortOne(self, ind):
        pass

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.proxy[ind - 1].write_attribute("ExposureTime", value)

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            if self.device_available[ind - 1]:
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> GreatEyesCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
