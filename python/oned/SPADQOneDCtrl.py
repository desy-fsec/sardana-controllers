import time
# import time, os

import PyTango
from sardana import DataAccess
# from sardana import State, DataAccess
from sardana.pool.controller import OneDController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class SPADQOneDCtrl(OneDController):
    "This class is the One D controller for SPADQDigitizer"

    axis_attributes = {
        'DataLength': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly},
        'SpectrumName': {Type: 'PyTango.DevString', Access: ReadWrite},
        'RoI1Start': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'RoI1End': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'CountsRoI1': {Type: 'PyTango.DevDouble', Access: ReadOnly},
        'RoI2Start': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'RoI2End': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'CountsRoI2': {Type: 'PyTango.DevDouble', Access: ReadOnly},
        'RoI3Start': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'RoI3End': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'CountsRoI3': {Type: 'PyTango.DevDouble', Access: ReadOnly},
        'RoI4Start': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'RoI4End': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'CountsRoI4': {Type: 'PyTango.DevDouble', Access: ReadOnly},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: 'PyTango.DevString',
            Description: 'The root name of the MCA Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    MaxDevice = 97

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        OneDController.__init__(self, inst, props, *args, **kwargs)
        if self.TangoHost is None:
            self.db = PyTango.Database()
        else:
            #
            # TangoHost can be hasgksspp07eh3:10000
            #
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
        self.RoI1_start = []
        self.RoI1_end = []
        self.Counts_RoI1 = []
        self.RoI2_start = []
        self.RoI2_end = []
        self.Counts_RoI2 = []
        self.RoI3_start = []
        self.RoI3_end = []
        self.Counts_RoI3 = []
        self.RoI4_start = []
        self.RoI4_end = []
        self.Counts_RoI4 = []
        self.SpectrumName = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(False)
            self.RoI1_start.append(0)
            self.RoI1_end.append(0)
            self.Counts_RoI1.append(0)
            self.RoI2_start.append(0)
            self.RoI2_end.append(0)
            self.Counts_RoI2.append(0)
            self.RoI3_start.append(0)
            self.RoI3_end.append(0)
            self.Counts_RoI3.append(0)
            self.RoI4_start.append(0)
            self.RoI4_end.append(0)
            self.Counts_RoI4.append(0)
            self.SpectrumName.append("")
            self.max_device = self.max_device + 1
        self.started = False
        self.acqTime = 0
        self.acqStartTime = None

    def AddDevice(self, ind):
        OneDController.AddDevice(self, ind)
        if ind > self.max_device:
            return
        proxy_name = self.tango_device[ind - 1]
        if self.TangoHost is None:
            proxy_name = self.tango_device[ind - 1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(self.tango_device[ind - 1])
        self.proxy[ind - 1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind - 1] = True

    def DeleteDevice(self, ind):
        OneDController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        if self.device_available[ind - 1] is True:
            sta = self.proxy[ind - 1].command_inout("State")
            status = self.proxy[ind - 1].command_inout("Status")
            tup = (sta, status)
        else:
            sta = PyTango.DevState.FAULT
            tup = (sta, "Device not available")

        return tup

    def LoadOne(self, ind, value, repetitions, latency_time):
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        self.acqTime = value

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        data = self.proxy[ind - 1].read_attribute(
            self.SpectrumName[ind - 1]).value
        self.Counts_RoI1[ind - 1] = data[
            self.RoI1_start[ind - 1]:self.RoI1_end[ind - 1]].sum()
        self.Counts_RoI2[ind - 1] = data[
            self.RoI2_start[ind - 1]:self.RoI2_end[ind - 1]].sum()
        self.Counts_RoI3[ind - 1] = data[
            self.RoI3_start[ind - 1]:self.RoI3_end[ind - 1]].sum()
        self.Counts_RoI4[ind - 1] = data[
            self.RoI4_start[ind - 1]:self.RoI4_end[ind - 1]].sum()
        return data

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, value):
        return True

    def StartOne(self, ind, value):
        sta = self.proxy[ind - 1].command_inout("State")
        if sta == PyTango.DevState.ON:
            self.proxy[ind - 1].command_inout("Start")
            self.started = True
            self.acqStartTime = time.time()

    def AbortOne(self, ind):
        self.proxy[ind - 1].command_inout("Stop")

    def GetAxisAttributes(self, axis):
        # change the default max shape for 'value'
        attrs = super().GetAxisAttributes(axis)
        attrs['Value']['maxdimsize'] = (100000,)
        return attrs

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            if self.device_available[ind - 1]:
                tango_device = self.node + ":" + str(self.port) + \
                    "/" + self.proxy[ind - 1].name()
                return tango_device
        elif name == "DataLength":
            if self.device_available[ind - 1]:
                if self.flagIsKromo[ind - 1] is False and \
                   self.flagIsAvantes[ind - 1] is False:
                    if self.flagIsXIA[ind - 1]:
                        datalength = int(self.proxy[ind - 1].read_attribute(
                            "McaLength").value)
                    elif self.flagIsSPADQ[ind - 1]:
                        datalength = int(self.proxy[ind - 1].read_attribute(
                            "ATDRecordLength").value)
                    else:
                        datalength = int(self.proxy[ind - 1].read_attribute(
                            "DataLength").value)
                elif self.flagIsAvantes[ind - 1] is True:
                    datalength = 4096
                else:
                    datalength = 255
                return datalength
        elif name == "RoI1Start":
            return self.RoI1_start[ind - 1]
        elif name == "RoI1End":
            return self.RoI1_end[ind - 1]
        elif name == "CountsRoI1":
            return self.Counts_RoI1[ind - 1]
        elif name == "RoI2Start":
            return self.RoI2_start[ind - 1]
        elif name == "RoI2End":
            return self.RoI2_end[ind - 1]
        elif name == "CountsRoI2":
            return self.Counts_RoI2[ind - 1]
        elif name == "RoI3Start":
            return self.RoI3_start[ind - 1]
        elif name == "RoI3End":
            return self.RoI3_end[ind - 1]
        elif name == "CountsRoI3":
            return self.Counts_RoI3[ind - 1]
        elif name == "RoI4Start":
            return self.RoI4_start[ind - 1]
        elif name == "RoI4End":
            return self.RoI4_end[ind - 1]
        elif name == "CountsRoI4":
            return self.Counts_RoI4[ind - 1]
        elif name == "SpectrumName":
            return self.SpectrumName[ind - 1]

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "DataLength":
                if self.flagIsKromo[ind - 1] is False and \
                   self.flagIsAvantes[ind - 1] is False:
                    if self.flagIsXIA[ind - 1]:
                        self.proxy[ind - 1].write_attribute("McaLength", value)
                    elif self.flagIsKromo[ind - 1] is True:
                        self.proxy[ind - 1].write_attribute(
                            "DataLength", value)
            elif name == "RoI1Start":
                self.RoI1_start[ind - 1] = value
            elif name == "RoI1End":
                self.RoI1_end[ind - 1] = value
            elif name == "RoI2Start":
                self.RoI2_start[ind - 1] = value
            elif name == "RoI2End":
                self.RoI2_end[ind - 1] = value
            elif name == "RoI3Start":
                self.RoI3_start[ind - 1] = value
            elif name == "RoI3End":
                self.RoI3_end[ind - 1] = value
            elif name == "RoI4Start":
                self.RoI4_start[ind - 1] = value
            elif name == "RoI4End":
                self.RoI4_end[ind - 1] = value
            elif name == "SpectrumName":
                self.SpectrumName[ind - 1] = value

    def GetAxisPar(self, axis, par):
        if par == "shape":
            return [100]

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("SPADQOneDCtrl dying")


if __name__ == "__main__":
    obj = OneDController('test')
    #    obj.AddDevice(2)
    #    obj.DeleteDevice(2)
