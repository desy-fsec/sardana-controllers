import PyTango
from sardana.pool.controller import CounterTimerController
import time

# from sardana import State, DataAccess
from sardana import DataAccess
# from sardana.pool.controller import MotorController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class MCAroisCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the MCA RoIs"

    axis_attributes = {
        'TangoDevice': {Type: str, Access: ReadOnly},
        'TangoAttribute': {Type: str, Access: ReadWrite},
        'FlagClear': {Type: int, Access: ReadWrite},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the MCArois Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "CounterTimer"
    model = "MCArois"
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
        self.AttributeNames = []
        self.flag_clear = 0
        proxy_name = self.RootDeviceName
        if self.TangoHost is not None:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(proxy_name)
        self.proxy = PyTango.DeviceProxy(proxy_name)
        self.start_time = time.time()
        self.exp_time = 0
        self.scanning = 0

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)
        self.AttributeNames.append("")

    def DeleteDevice(self, ind):
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy = None

    def StateOne(self, ind):
        if time.time() - self.start_time < self.exp_time:
            sta = PyTango.DevState.MOVING
            status_string = "MCA is busy"
        else:
            if self.scanning == 1:
                self.proxy.command_inout("Stop")
                self.proxy.command_inout("Read")
                self.scanning = 0
            sta = PyTango.DevState.ON
            status_string = "MCA is in ON state"
        tup = (sta, status_string)
        return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def StartOne(self, ind, value):
        pass

    def ReadOne(self, ind):
        value = self.proxy.read_attribute(self.AttributeNames[ind - 1]).value
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
        # the state may be ON but one bank can be active
        self.proxy.command_inout("Stop")
        if self.flag_clear:
            self.proxy.command_inout("Clear")
        self.proxy.command_inout("Start")
        self.start_time = time.time()
        self.scanning = 1

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.exp_time = value

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            tango_device = self.node + ":" + str(self.port) + "/" + \
                self.proxy.name()
            return tango_device
        if name == "TangoAttribute":
            return self.AttributeNames[ind - 1]
        if name == "FlagClear":
            return self.flag_clear

    def SetAxisExtraPar(self, ind, name, value):
        if name == "TangoAttribute":
            self.AttributeNames[ind - 1] = value
        if name == "FlagClear":
            self.flag_clear = value

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> MCAroisCtrl dying")
