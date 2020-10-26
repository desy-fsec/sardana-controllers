import PyTango
# import time, os

# from sardana import State, DataAccess
from sardana import DataAccess
from sardana.pool.controller import TwoDController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class EigerDectrisCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the EigerDectris"

    axis_attributes = {
        'CountTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'CountTimeInte': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'NbTriggers': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TriggerMode': {Type: 'PyTango.DevString', Access: ReadWrite},
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the EigerDectris Tango devices'},
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
        self.dft_CountTime = 0
        self.CountTime = []
        self.dft_CountTimeInte = 0
        self.CountTimeInte = []
        self.dft_TriggerMode = ""
        self.TriggerMode = []
        self.dft_NbTriggers = 0
        self.NbTriggers = []

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
        self.CountTime.append(self.dft_CountTime)
        self.CountTimeInte.append(self.dft_CountTimeInte)
        self.TriggerMode.append(self.dft_TriggerMode)
        self.NbTriggers.append(self.dft_NbTriggers)

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
                tup = (sta, "Camera taking images")
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
        # The EigerDectris return an Image in type encoded
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, value):
        return True

    def StartOne(self, ind, position=None):
        self.proxy[ind - 1].command_inout("Trigger")

    def AbortOne(self, ind):
        pass

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.proxy[ind - 1].write_attribute("CountTime", value)
        self.proxy[ind - 1].write_attribute("CountTimeInte", value)

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "CountTime":
                return self.proxy[ind - 1].read_attribute("CountTime").value
            elif name == "CountTimeInte":
                return self.proxy[ind - 1].read_attribute(
                    "CountTimeInte").value
            elif name == "NbTriggers":
                return self.proxy[ind - 1].read_attribute("NbTriggers").value
            elif name == "TriggerMode":
                return self.proxy[ind - 1].read_attribute("TriggerMode").value
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device
            elif name == "SettleTime":
                return self.SettleTime[ind - 1]

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "CountTime":
                self.proxy[ind - 1].write_attribute("CountTime", value)
            elif name == "CountTimeInte":
                self.proxy[ind - 1].write_attribute("CountTimeInte", value)
            elif name == "NbTriggers":
                self.proxy[ind - 1].write_attribute("NbTriggers", value)
            elif name == "TriggerMode":
                self.proxy[ind - 1].write_attribute("TriggerMode", value)

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> EigerDectrisCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
