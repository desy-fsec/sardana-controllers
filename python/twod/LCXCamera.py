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


class LCXCameraCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the LCXCamera"

    axis_attributes = {
        'DelayTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'ExposureTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'FileStartNum': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'FilePrefix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FileDir': {Type: 'PyTango.DevString', Access: ReadWrite},
        'NbFrames': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'Reset': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the LCXCamera Tango devices'},
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
        self.dft_DelayTime = 0
        self.DelayTime = []
        self.dft_ExposureTime = 0
        self.ExposureTime = []
        self.dft_ExposurePeriod = 0
        self.ExposurePeriod = []
        self.dft_FileStartNum = 0
        self.FileStartNum = []
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FileDir = ""
        self.FileDir = []
        self.dft_NbFrames = 0
        self.NbFrames = []
        self.dft_Reset = 0
        self.Reset = []

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
        self.DelayTime.append(self.dft_DelayTime)
        self.ExposureTime.append(self.dft_ExposureTime)
        self.FileStartNum.append(self.dft_FileStartNum)
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FileDir.append(self.dft_FileDir)
        self.NbFrames.append(self.dft_NbFrames)
        self.Reset.append(self.dft_Reset)

    def DeleteDevice(self, ind):
        TwoDController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta, "Camera ready")
            elif sta == PyTango.DevState.RUNNING:
                sta = PyTango.DevState.MOVING
                tup = (sta, "Camera taking images")
            elif sta == PyTango.DevState.FAULT:
                tup = (sta, "Camera in FAULT state")
            elif sta == PyTango.DevState.DISABLE:
                sta = PyTango.DevState.FAULT
                tup = (sta, "Device disconnected from camserver")
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

    def StartOne(self, ind, position=None):
        self.proxy[ind - 1].command_inout("StartAcquisition")

    def AbortOne(self, ind):
        pass

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.proxy[ind - 1].write_attribute("ExposureTime", value)

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "DelayTime":
                return self.proxy[ind - 1].read_attribute("DelayTime").value
            elif name == "ExposureTime":
                return self.proxy[ind - 1].read_attribute("ExposureTime").value
            elif name == "FileStartNum":
                return self.proxy[ind - 1].read_attribute("FileStartNum").value
            elif name == "FilePrefix":
                return self.proxy[ind - 1].read_attribute("FilePrefix").value
            elif name == "FileDir":
                return self.proxy[ind - 1].read_attribute("FileDir").value
            elif name == "NbFrames":
                return self.proxy[ind - 1].read_attribute("NbFrames").value
            elif name == "Reset":
                if self.device_available[ind - 1]:
                    return 0
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "DelayTime":
                self.proxy[ind - 1].write_attribute("DelayTime", value)
            elif name == "ExposureTime":
                self.proxy[ind - 1].write_attribute("ExposureTime", value)
            elif name == "FileStartNum":
                self.proxy[ind - 1].write_attribute("FileStartNum", value)
            elif name == "FilePrefix":
                self.proxy[ind - 1].write_attribute("FilePrefix", value)
            elif name == "FileDir":
                self.proxy[ind - 1].write_attribute("FileDir", value)
            elif name == "NbFrames":
                self.proxy[ind - 1].write_attribute("NbFrames", value)
            elif name == "Reset":
                if self.device_available[ind - 1]:
                    self.proxy[ind - 1].command_inout("Reset")

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> LCXCameraCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
