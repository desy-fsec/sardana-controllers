#
# 4.9.2019 TN modified ReadOne() to use the elapsed time trick
#
import PyTango
from sardana.pool.controller import CounterTimerController
import time


from sardana import State, DataAccess
# from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import  DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class SIS3820Ctrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the SIS3820"
    axis_attributes = {
        'Offset': {Type: float, Access: ReadWrite},
        'TangoDevice': {Type: str, Access: ReadOnly},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the SIS3820 Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "CounterTimer"
    model = "SIS3820"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        CounterTimerController.__init__(
            self, inst, props, *args, **kwargs)
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
            value = None
            try:
                value = self.proxy[ind - 1].read_attribute("Counts").value
            except Exception:
                self.intern_sta[ind - 1] = State.Fault
                return value
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
            return value

    def AbortOne(self, ind):
        pass

    def PreStartAll(self):
        self.wantedCT = []

    def PreStartOne(self, ind, value):
        if self.device_available[ind - 1] == 1:
            self.proxy[ind - 1].command_inout("Reset")
            self.intern_sta[ind - 1] = State.Moving
            return True
        else:
            raise RuntimeError("Ctrl Tango's proxy null!!!")
            return False

    def StartOne(self, ind, value):
        self.wantedCT.append(ind)

    def StartAll(self):
        self.started = True
        self._start_time = time.time()

    def LoadOne(self, ind, value, repetitions, latency_time):
        self._integ_time = value

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "Offset":
                return float(
                    self.proxy[ind - 1].read_attribute("Offset").value)
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" \
                    + self.proxy[ind - 1].name()
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        if name == "Offset":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("Offset", value)

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def start_acquisition(self, value=None):
        pass

    def __del__(self):
        print("Deleting SIS3820Ctrl controller")


if __name__ == "__main__":
    obj = SIS3820Ctrl('test')
