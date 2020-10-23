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


class MarCCDCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the MarCCD"

    axis_attributes = {
        'FilePrefix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FilePostfix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FileDir': {Type: 'PyTango.DevString', Access: ReadWrite},
        'ReadMode': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly},
        'ExposureTime': {Type: 'PyTango.DevDouble', Access: ReadWrite}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the MarCCD Tango devices'},
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
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FilePostfix = ""
        self.FilePostfix = []
        self.dft_FileDir = ""
        self.FileDir = []
        self.dft_ReadMode = 0
        self.ReadMode = []
        self.dft_ExposureTime = 0
        self.ExposureTime = []

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
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FilePostfix.append(self.dft_FilePostfix)
        self.FileDir.append(self.dft_FileDir)
        self.ReadMode.append(self.dft_ReadMode)
        self.ExposureTime.append(self.dft_ExposureTime)

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
        # The MarCCD return an Image in type encoded
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value

    def PreStartAll(self):
        pass

    def StartOne(self, ind, position=None):
        file_name_tmp = self.proxy[ind - 1].read_attribute(
            "SavingPrefix").value
        if file_name_tmp.find('_') != -1:
            file_name_split = file_name_tmp.split('_')
            file_name_last = file_name_split[len(file_name_split)-1]
            try:
                last_nb = int(file_name_last)
                last_nb = last_nb + 1
                new_file_name = ""
                file_name_tmp = file_name_tmp.rsplit("_", 1)[0]
            except Exception:
                last_nb = 0
        else:
            last_nb = 0
        if last_nb < 10:
            new_file_name = file_name_tmp + "_000" + str(last_nb)
        elif last_nb < 100:
            new_file_name = file_name_tmp + "_00" + str(last_nb)
        elif last_nb < 1000:
            new_file_name = file_name_tmp + "_0" + str(last_nb)
        else:
            new_file_name = file_name_tmp + "_" + str(last_nb)
        self.proxy[ind - 1].write_attribute("SavingPrefix", new_file_name)
        self.proxy[ind - 1].command_inout("StartExposing")

    def AbortOne(self, ind):
        try:
            self.proxy[ind - 1].command_inout("StopExposing")
        except Exception:
            print(
                "AbortOne: StopExposing can not be called if ExposureTime > 0")

    def LoadOne(self, ind, value, repetitions, latency_time):
        if self.device_available[ind - 1]:
            self.proxy[ind - 1].write_attribute("ExposureTime", value)

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "FilePrefix":
                return self.proxy[ind - 1].read_attribute("SavingPrefix").value
            elif name == "FilePostfix":
                return self.proxy[ind - 1].read_attribute(
                    "SavingPostfix").value
            elif name == "FileDir":
                return self.proxy[ind - 1].read_attribute(
                    "SavingDirectory").value
            elif name == "ReadMode":
                return self.proxy[ind - 1].read_attribute("ReadMode").value
            elif name == "ExposureTime":
                return self.proxy[ind - 1].read_attribute("ExposureTime").value
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "FilePrefix":
                self.proxy[ind - 1].write_attribute("SavingPrefix", value)
            elif name == "FilePostfix":
                self.proxy[ind - 1].write_attribute("SavingPostfix", value)
            elif name == "FileDir":
                self.proxy[ind - 1].write_attribute("SavingDirectory", value)
            elif name == "ReadMode":
                self.proxy[ind - 1].write_attribute("ReadMode", value)
            elif name == "ExposureTime":
                self.proxy[ind - 1].write_attribute("ExposureTime", value)

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> MarCCDCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
