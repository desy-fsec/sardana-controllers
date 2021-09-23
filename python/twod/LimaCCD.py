import PyTango
# import time, os

from sardana import DataAccess
# from sardana import State, DataAccess
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class LimaCCDCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the LimaCCD"

    axis_attributes = {
        'LatencyTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'ExposureTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'FilePrefix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FileSuffix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FileDir': {Type: 'PyTango.DevString', Access: ReadWrite},
        'SavingMode': {Type: 'PyTango.DevString', Access: ReadWrite},
        'SavingCommondHeader': {Type: 'PyTango.DevString', Access: ReadWrite},
        'SavingHeaderDelimiter': {
            Type: 'PyTango.DevString', Access: ReadWrite},
        'SavingNextNumber': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'LastImageReady': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'NbFrames': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TriggerMode': {Type: 'PyTango.DevString', Access: ReadWrite},
        'CameraType': {Type: 'PyTango.DevString', Access: ReadOnly},
        'Reset': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the LimaCCD Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
        'FlagMode': {
            Type: 'PyTango.DevLong',
            Description:
            '0 -> one file per image, 1 -> all images in one file',
            DefaultValue: 0},
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
        self.dft_LatencyTime = 0
        self.LatencyTime = []
        self.dft_ExposureTime = 0
        self.ExposureTime = []
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FileSuffix = ""
        self.FileSuffix = []
        self.dft_FileDir = ""
        self.FileDir = []
        self.dft_SavingMode = ""
        self.SavingMode = []
        self.dft_SavingCommonHeader = ""
        self.SavingCommonHeader = []
        self.dft_SavingHeaderDelimiter = ""
        self.SavingHeaderDelimiter = []
        self.dft_SavingNextNumber = 0
        self.SavingNextNumber = []
        self.dft_LastImageReady = 0
        self.LastImageReady = []
        self.dft_NbFrames = 0
        self.NbFrames = []
        self.dft_TriggerMode = 0
        self.TriggerMode = []
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
        self.LatencyTime.append(self.dft_LatencyTime)
        self.ExposureTime.append(self.dft_ExposureTime)
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FileSuffix.append(self.dft_FileSuffix)
        self.FileDir.append(self.dft_FileDir)
        self.SavingMode.append(self.dft_SavingMode)
        self.SavingCommonHeader.append(self.dft_SavingCommonHeader)
        self.SavingHeaderDelimiter.append(self.dft_SavingHeaderDelimiter)
        self.SavingNextNumber.append(self.dft_SavingNextNumber)
        self.LastImageReady.append(self.dft_LastImageReady)
        self.NbFrames.append(self.dft_NbFrames)
        self.TriggerMode.append(self.dft_TriggerMode)
        self.Reset.append(self.dft_Reset)

    def DeleteDevice(self, ind):
        TwoDController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        if self.device_available[ind - 1] == 1:
            if self.FlagMode == 1:
                tup = (PyTango.DevState.ON, "Camera ready")
            else:
                sta = self.proxy[ind - 1].read_attribute("acq_status").value
                if sta == "Ready":
                    tup = (PyTango.DevState.ON, "Camera ready")
                elif sta == "Running":
                    tup = (PyTango.DevState.MOVING, "Camera taking images")
                elif sta == "Fault":
                    tup = (PyTango.DevState.FAULT, "Camera in FAULT state")
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        # The LimaCCD return an Image in type encoded
        # Fill an ouput for avoiding reaout errors
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value

    def PreStartAll(self):
        pass

    def StartOne(self, ind, value):
        # +++ 5.7.2021
        if self.FlagMode != 1:
            self.proxy[ind - 1].write_attribute("acq_nb_frames", 1)
            self.proxy[ind - 1].command_inout("prepareAcq")
        self.proxy[ind - 1].command_inout("startAcq")

    def AbortOne(self, ind):
        self.proxy[ind - 1].command_inout("stopAcq")

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.proxy[ind - 1].write_attribute('acq_expo_time', value)

    def GetAxisPar(self, ind, par_name):
        if par_name == "XDim":
            if self.device_available[ind - 1]:
                return int(self.proxy[ind - 1].read_attribute(
                    "image_width").value)
        elif par_name == "YDim":
            if self.device_available[ind - 1]:
                return int(self.proxy[ind - 1].read_attribute(
                    "image_height").value)
        elif par_name == "IFormat":
            # ULong
            return 3

    def GetAxisExtraPar(self, ind, name):
        if name == "LatencyTime":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "latency_time").value
        if name == "ExposureTime":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "acq_expo_time").value
        if name == "FilePrefix":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "saving_prefix").value
        if name == "FileSuffix":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "saving_suffix").value
        if name == "FileDir":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "saving_directory").value
        if name == "SavingMode":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "saving_mode").value
        if name == "SavingCommonHeader":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "saving_common_header").value
        if name == "SavingHeaderDelimiter":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "saving_header_delimiter").value
        if name == "SavingNextNumber":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "saving_next_number").value
        if name == "LastImageReady":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "last_image_ready").value
        if name == "NbFrames":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "acq_nb_frames").value
        if name == "TriggerMode":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "acq_trigger_mode").value
        if name == "CameraType":
            if self.device_available[ind - 1]:
                return self.proxy[ind - 1].read_attribute(
                    "camera_type").value
        if name == "Reset":
            if self.device_available[ind - 1]:
                return 0
        if name == "TangoDevice":
            tango_device = self.node + ":" + str(self.port) + "/" + \
                self.proxy[ind - 1].name()
            return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        if name == "LatencyTime":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("latency_time", value)
        if name == "ExposureTime":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("acq_expo_time", value)
        if name == "FilePrefix":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("saving_prefix", value)
        if name == "FileSuffix":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("saving_suffix", value)
        if name == "FileDir":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("saving_directory", value)
        if name == "SavingMode":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("saving_mode", value)
        if name == "SavingCommonHeader":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute(
                    "saving_common_header", value)
        if name == "SavingHeaderDelimiter":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute(
                    "saving_header_delimiter", value)
        if name == "SavingNextNumber":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute(
                    "saving_next_number", value)
        if name == "NbFrames":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("acq_nb_frames", value)
        if name == "TriggerMode":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("acq_trigger_mode", value)
        if name == "Reset":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].command_inout("Reset")

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> LimaCCDCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
