import PyTango
import time
# import time, os

from sardana import DataAccess
# from sardana import State, DataAccess
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class PilatusCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the Pilatus"

    axis_attributes = {
        'DelayTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'ExposureTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'ExposurePeriod': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'FileStartNum': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'FilePrefix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FilePostfix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FileDir': {Type: 'PyTango.DevString', Access: ReadWrite},
        'LastImageTaken': {Type: 'PyTango.DevString', Access: ReadWrite},
        'NbFrames': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'NbExposures': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'ShutterEnable': {Type: 'PyTango.DevBoolean', Access: ReadWrite},
        'TriggerMode': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'Threshold': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'Gain': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'Reset': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'SettleTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the Pilatus Tango devices'},
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
        self.dft_FilePostfix = ""
        self.FilePostfix = []
        self.dft_FileDir = ""
        self.FileDir = []
        self.dft_LastImageTaken = ""
        self.LastImageTaken = []
        self.dft_NbFrames = 0
        self.NbFrames = []
        self.dft_NbExposures = 0
        self.NbExposures = []
        self.dft_ShutterEnable = 0
        self.ShutterEnable = []
        self.dft_TriggerMode = 0
        self.TriggerMode = []
        self.dft_Threshold = 0
        self.Threshold = []
        self.dft_Gain = 0
        self.Gain = []
        self.dft_Reset = 0
        self.Reset = []
        self.dft_SettleTime = 0.4
        self.SettleTime = []

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
        self.ExposurePeriod.append(self.dft_ExposurePeriod)
        self.FileStartNum.append(self.dft_FileStartNum)
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FilePostfix.append(self.dft_FilePostfix)
        self.FileDir.append(self.dft_FileDir)
        self.LastImageTaken.append(self.dft_LastImageTaken)
        self.NbFrames.append(self.dft_NbFrames)
        self.NbExposures.append(self.dft_NbExposures)
        self.ShutterEnable.append(self.dft_ShutterEnable)
        self.TriggerMode.append(self.dft_TriggerMode)
        self.Threshold.append(self.dft_Threshold)
        self.Gain.append(self.dft_Gain)
        self.Reset.append(self.dft_Reset)
        self.SettleTime.append(self.dft_SettleTime)

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
        # The Pilatus return an Image in type encoded
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, value):
        if self.proxy[ind - 1].read_attribute("TriggerMode").value > 0:
            self.proxy[ind - 1].command_inout("StartStandardAcq")
            time.sleep(self.SettleTime[ind - 1])
        return True

    def StartOne(self, ind, position=None):
        if self.proxy[ind - 1].read_attribute("TriggerMode").value == 0:
            self.proxy[ind - 1].command_inout("StartStandardAcq")

    def AbortOne(self, ind):
        self.proxy[ind - 1].command_inout("StopAcq")

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.proxy[ind - 1].write_attribute("ExposureTime", value)

    def GetAxisPar(self, ind, par_name):
        if par_name == "data_source":
            data_source = str(self.tango_device[ind - 1]) + "/LastImageTaken"
            return data_source

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "DelayTime":
                return self.proxy[ind - 1].read_attribute("DelayTime").value
            elif name == "ExposureTime":
                return self.proxy[ind - 1].read_attribute("ExposureTime").value
            elif name == "ExposurePeriod":
                return self.proxy[ind - 1].read_attribute(
                    "ExposurePeriod").value
            elif name == "FileStartNum":
                return self.proxy[ind - 1].read_attribute("FileStartNum").value
            elif name == "FilePrefix":
                return self.proxy[ind - 1].read_attribute("FilePrefix").value
            elif name == "FilePostfix":
                return self.proxy[ind - 1].read_attribute("FilePostfix").value
            elif name == "FileDir":
                return self.proxy[ind - 1].read_attribute("FileDir").value
            elif name == "LastImageTaken":
                return self.proxy[ind - 1].read_attribute(
                    "LastImageTaken").value
            elif name == "NbFrames":
                return self.proxy[ind - 1].read_attribute("NbFrames").value
            elif name == "NbExposures":
                return self.proxy[ind - 1].read_attribute("NbExposures").value
            elif name == "TriggerMode":
                return self.proxy[ind - 1].read_attribute("TriggerMode").value
            elif name == "Threshold":
                return self.proxy[ind - 1].read_attribute("Threshold").value
            elif name == "Gain":
                return self.proxy[ind - 1].read_attribute("Gain").value
            elif name == "Reset":
                if self.device_available[ind - 1]:
                    return 0
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device
            elif name == "SettleTime":
                return self.SettleTime[ind - 1]

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "DelayTime":
                self.proxy[ind - 1].write_attribute("DelayTime", value)
            elif name == "ExposureTime":
                self.proxy[ind - 1].write_attribute("ExposureTime", value)
            elif name == "ExposurePeriod":
                self.proxy[ind - 1].write_attribute("ExposurePeriod", value)
            elif name == "FileStartNum":
                self.proxy[ind - 1].write_attribute("FileStartNum", value)
            elif name == "FilePrefix":
                self.proxy[ind - 1].write_attribute("FilePrefix", value)
            elif name == "FilePostfix":
                self.proxy[ind - 1].write_attribute("FilePostfix", value)
            elif name == "FileDir":
                self.proxy[ind - 1].write_attribute("FileDir", value)
            elif name == "LastImageTaken":
                self.proxy[ind - 1].write_attribute("LastImageTaken", value)
            elif name == "NbFrames":
                self.proxy[ind - 1].write_attribute("NbFrames", value)
            elif name == "NbExposures":
                self.proxy[ind - 1].write_attribute("NbExposures", value)
            elif name == "ShutterEnable":
                self.proxy[ind - 1].write_attribute("ShutterEnable", value)
            elif name == "TriggerMode":
                self.proxy[ind - 1].write_attribute("TriggerMode", value)
            elif name == "Threshold":
                self.proxy[ind - 1].write_attribute("Threshold", value)
            elif name == "Gain":
                self.proxy[ind - 1].write_attribute("Gain", value)
            elif name == "Reset":
                if self.device_available[ind - 1]:
                    self.proxy[ind - 1].command_inout("Reset")
            elif name == "SettleTime":
                if self.device_available[ind - 1]:
                    self.SettleTime[ind - 1] = value

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> PilatusCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
