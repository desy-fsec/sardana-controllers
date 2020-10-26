import PyTango
# import os
import time

from sardana import DataAccess
# from sardana import State, DataAccess
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class PCOCtrl(TwoDController):
    "This class is the Tango Sardana Zero D controller for the PCO"

    axis_attributes = {
        'DelayTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'ExposureTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'ADCs': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'FileStartNum': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'FilePrefix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FileDir': {Type: 'PyTango.DevString', Access: ReadWrite},
        'TangoDevice': {Type: str, Access: ReadOnly},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the PCO Tango devices'},
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
        self.dft_ADCs = 0
        self.ADCs = []
        self.dft_FileStartNum = 0
        self.FileStartNum = []
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FileDir = ""
        self.FileDir = []

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
        self.ADCs.append(self.dft_ADCs)
        self.FileStartNum.append(self.dft_FileStartNum)
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FileDir.append(self.dft_FileDir)

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
            elif sta == PyTango.DevState.UNKNOWN:
                sta = PyTango.DevState.FAULT
                tup = (sta, "Camera in UNKNOWN state")
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        # The PCO return an Image in type encoded
        while self.proxy[ind - 1].state() != PyTango.DevState.ON:
            time.sleep(0.001)
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value

    def PreStartAll(self):
        pass

    def StartOne(self, ind, position=None):
        # Need it because the PCO goes to DISABLE after MOVING
        while self.proxy[ind - 1].state() != PyTango.DevState.ON:
            time.sleep(0.001)
        self.proxy[ind - 1].command_inout("StartStandardAcq")

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.proxy[ind - 1].write_attribute("ExposureTime", value)

    def GetAxisPar(self, ind, par_name):
        if par_name == "XDim":
            if self.device_available[ind - 1]:
                return int(self.proxy[ind - 1].read_attribute("Width").value)
        elif par_name == "YDim":
            if self.device_available[ind - 1]:
                return int(self.proxy[ind - 1].read_attribute("Heigth").value)

    def SetAxisPar(self, ind, par_name, value):
        if par_name == "XDim":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("Width", value)
        elif par_name == "YDim":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("Heigth", value)

    def GetAxisExtraPar(self, ind, name):
        if name == "DelayTime":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute("DelayTime").value
        if name == "ExposureTime":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute("ExposureTime").value
        if name == "ADCs":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute("ADCs").value
        if name == "FileStartNum":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute("FileStartNum").value
        if name == "FilePrefix":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute("FilePrefix").value
        if name == "FileDir":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute("FileDir").value
        if name == "TangoDevice":
            if self.device_available[ind - 1]:
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        if name == "DelayTime":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("DelayTime", value)
        if name == "ExposureTime":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("ExposureTime", value)
        if name == "ADCs":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("ADCs", value)
        if name == "FileStartNum":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("FileStartNum", value)
        if name == "FilePrefix":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("FilePrefix", value)
        if name == "FileDir":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("FileDir", value)

    def SendToCtrl(self, in_data):
        # print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> PCOCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
    #  obj.AddDevice(2)
    #  obj.DeleteDevice(2)
