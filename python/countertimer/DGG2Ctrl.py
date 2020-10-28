#
# 4.9.2019 TN modified ReadOne() to use the elapsed time trick
#
import PyTango
from sardana.pool.controller import CounterTimerController
import time

from sardana import State, DataAccess
# from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class DGG2Ctrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller " \
        + "for the DGG2 timer"

    axis_attributes = {
        'TangoDevice': {Type: str, Access: ReadOnly},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the DGG2 timer Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "CounterTimer"
    model = "DGG2"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
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
        self.intern_sta = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.max_device = self.max_device + 1
            self.intern_sta.append(State.On)
        self.started = False
        self.preset_mode = 0  # Trigger with counts
        self._integ_time = None
        self._start_time = None

    def AddDevice(self, ind):
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
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        if self.device_available[ind - 1] == 1:
            tup = (self.intern_sta[ind - 1], "State from ReadOne")
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        if self.device_available[ind - 1] == 1:
            v = None
            try:
                sample_time = \
                    self.proxy[ind - 1].read_attribute("SampleTime").value
                remaining_time = \
                    self.proxy[ind - 1].read_attribute("RemainingTime").value
                v = sample_time - remaining_time
            except Exception:
                self.intern_sta[ind - 1] = State.Fault
                return v
            now = time.time()
            if self._start_time is not None:
                elapsed_time = now - self._start_time
            else:
                elapsed_time = 9999999999.
            if elapsed_time < self._integ_time:
                self.intern_sta[ind - 1] = State.Moving
            else:
                self.intern_sta[ind - 1] = \
                    self.proxy[ind - 1].command_inout("State")
            return v

    def AbortOne(self, ind):
        if self.device_available[ind - 1] == 1:
            self.proxy[ind - 1].command_inout("Stop")

    def PreStartAll(self):
        self.wantedCT = []

    def PreStartOne(self, ind, pos):
        return True

    # def PreStartOne(self, ind):
    #     pass

    def StartOne(self, ind, value):
        if self.device_available[ind - 1] == 1:
            self.wantedCT.append(ind)

    def StartAll(self):
        for index in self.wantedCT:
            if self.preset_mode:
                self.proxy[index-1].command_inout("StartPreset")
            else:
                self.proxy[index-1].command_inout("Start")
            self._start_time = time.time()
            self.intern_sta[index-1] = State.Moving

    def LoadOne(self, ind, value, repetitions, latency_time):
        if self.device_available[ind - 1] == 1:
            if value < 0:
                self.preset_mode = 1
                value = -1. * value
            else:
                self.preset_mode = 0
            self._integ_time = value
            self.proxy[ind - 1].write_attribute("SampleTime", value)

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> DGG2Ctrl dying")
