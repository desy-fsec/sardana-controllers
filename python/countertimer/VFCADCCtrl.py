
import PyTango

import time

# from sardana import State, DataAccess
from sardana import DataAccess
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class VFCADCCtrl(CounterTimerController):
    "This class is the Tango Sardana Zero D controller for the VFCADC"

    axis_attributes = {
        'Gain': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'Offset': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'Polarity': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'FlagReadVoltage': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TangoDevice': {Type: str, Access: ReadOnly},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: 'PyTango.DevString',
            Description: 'The root name of the VFCADC Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    MaxDevice = 97

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
#        print "PYTHON -> CounterTimerController ctor for instance", inst

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
        self.started = False
        self.dft_Offset = 0
        self.Offset = []
        self.dft_Gain = 0
        self.Gain = []
        self.dft_Polarity = 0
        self.Polarity = []
        self.dft_FlagReadVoltage = 0
        self.FlagReadVoltage = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.max_device = self.max_device + 1
            self.Offset.append(self.dft_Offset)
            self.Gain.append(self.dft_Gain)
            self.Polarity.append(self.dft_Polarity)
            self.FlagReadVoltage.append(self.dft_FlagReadVoltage)

    def AddDevice(self, ind):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        #  In AddDevice method for index", ind
        CounterTimerController.AddDevice(self, ind)
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
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        # In DeleteDevice method for index", ind
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        #    In StateOne method for index", ind
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            tup = (sta, "State from connected Tango device")
            return tup

    def PreReadAll(self):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        #     In PreReadAll method"
        pass

    def PreReadOne(self, ind):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        # In PreReadOne method for index", ind
        pass

    def ReadAll(self):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        #     In ReadAll method"
        pass

    def ReadOne(self, ind):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        # In ReadOne method for index", ind
        if self.device_available[ind - 1] == 1:
            if self.FlagReadVoltage[ind - 1] == 1:
                return self.proxy[ind - 1].read_attribute("Value").value
            else:
                return self.proxy[ind - 1].read_attribute("Counts").value

    def PreStartAll(self):
        #  print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        #     In PreStartAll method"
        self.wanted = []

    def PreStartOne(self, ind, value):
        if self.device_available[ind - 1] == 1:
            self.proxy[ind - 1].command_inout("Reset")
            return True
        else:
            raise RuntimeError("Ctrl Tango's proxy null!!!")
            return False

    def StartOne(self, ind, value):
        # print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        # In StartOne method for index", ind
        self.wanted.append(ind)

    def StartAll(self):
        self.started = True
        self.start_time = time.time()

    def LoadOne(self, ind, value, repetitions, latency_time):
        pass

    def AbortOne(self, ind):
        pass

    def GetAxisExtraPar(self, ind, name):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        # In GetExtraFeaturePar method for index", ind," name=", name
        if name == "Offset":
            if self.device_available[ind - 1]:
                return float(
                    self.proxy[ind - 1].read_attribute("Offset").value)
        elif name == "Gain":
            if self.device_available[ind - 1]:
                return float(
                    self.proxy[ind - 1].read_attribute("Gain").value)
        elif name == "Polarity":
            if self.device_available[ind - 1]:
                return int(
                    self.proxy[ind - 1].read_attribute("Polarity").value)
        elif name == "FlagReadVoltage":
            if self.device_available[ind - 1]:
                return int(self.FlagReadVoltage[ind - 1])
        elif name == "TangoDevice":
            if self.device_available[ind - 1]:
                tango_device = self.node + ":" + str(self.port) + \
                    "/" + self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        #        print "PYTHON -> VFCADCCtrl/", self.inst_name,": \
        # In SetExtraFeaturePar method for index", ind," name=", name," \
        # value=", value
        if name == "Offset":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("Offset", value)
                self.proxy[ind - 1].command_inout("SetOffset")
        if name == "Gain":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("Gain", value)
                self.proxy[ind - 1].command_inout("SetGain")
        if name == "Polarity":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("Polarity", value)
                self.proxy[ind - 1].command_inout("SetPolarity")
        if name == "FlagReadVoltage":
            if self.device_available[ind - 1]:
                self.FlagReadVoltage[ind - 1] = value

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def start_acquisition(self, value=None):
        pass

    def __del__(self):
        print("PYTHON -> VFCADCCtrl dying")


if __name__ == "__main__":
    obj = CounterTimerController('test')
    #    obj.AddDevice(2)
    #    obj.DeleteDevice(2)
