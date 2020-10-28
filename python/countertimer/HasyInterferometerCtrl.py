import PyTango
from sardana.pool.controller import CounterTimerController
# import time

from sardana import DataAccess
# from sardana import State, DataAccess
# from sardana.pool.controller import MotorController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class HasyInterferometerCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller " + \
        "for the Interferometers"

    axis_attributes = {'TangoDevice': {Type: str, Access: ReadOnly}, }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The name of the Interferometer Tango device'
        },
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the device'
        },
    }

    gender = "CounterTimer"
    model = "Interferometer"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        if self.TangoHost is not None:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find(':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int(lst[1])
        self.started = False
        self.time_to_set = 0
        proxy_name = self.RootDeviceName
        if self.TangoHost is not None:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(proxy_name)
        self.proxy = PyTango.DeviceProxy(proxy_name)

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)

    def DeleteDevice(self, ind):
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy = None

    def StateOne(self, ind):
        sta = self.proxy.command_inout("State")
        if sta == PyTango.DevState.RUNNING:
            sta = PyTango.DevState.MOVING
        tup = (sta, "Status from connected tango device")
        return tup

    def PreReadAll(self):
        pass

    def ReadAll(self):
        pass

    def StartOne(self, ind, value):
        pass

    def ReadOne(self, ind):
        value = -1
        return value

    def AbortOne(self, ind):
        pass

    def PreStartAll(self):
        self.wantedCT = []

    def PreStartOne(self, ind, pos):
        return True

    # def PreStartOne(self, ind):
    #     pass

    def StartAll(self):
        self.proxy.command_inout("CollectDataTime", self.time_to_set)

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.time_to_set = value * 1000  # in ms

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            tango_device = self.node + ":" + str(self.port) + "/" + \
                self.proxy.name()
            return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> HasyInterferometerCtrl dying")
