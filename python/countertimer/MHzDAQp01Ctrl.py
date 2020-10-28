import PyTango
from sardana.pool.controller import CounterTimerController
# import time

# from sardana import State, DataAccess
from sardana import DataAccess
# from sardana.pool.controller import MotorController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

global last_sta


class MHzDAQp01Ctrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller " + \
        "for the Mythen RoIs"

    axis_attributes = {
        'TangoDevice': {Type: str, Access: ReadOnly},
        'FilePrefix': {Type: 'PyTango.DevString', Access: ReadWrite},
        'FileNum': {Type: 'PyTango.DevLong', Access: ReadWrite},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the MHzDAQp01 Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "CounterTimer"
    model = "MHzDAQp01"
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
        proxy_name = self.RootDeviceName
        if self.TangoHost is not None:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(proxy_name)
        self.proxy = PyTango.DeviceProxy(proxy_name)
        global last_sta
        last_sta = PyTango.DevState.ON

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)

    def DeleteDevice(self, ind):
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy = None

    def StateOne(self, ind):
        global last_sta
        try:
            sta = self.proxy.command_inout("State")
            last_sta = sta
        except Exception:
            sta = last_sta
        if sta == PyTango.DevState.ON:
            status_string = "MHzDAQp01 is in ON state"
        elif sta == PyTango.DevState.MOVING:
            status_string = "MHzDAQp01 is busy"
        tup = (sta, status_string)
        return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def StartOne(self, ind, value):
        try:
            sta = self.proxy.command_inout("State")
        except Exception:
            sta = PyTango.DevState.ON
        if sta == PyTango.DevState.ON:
            self.proxy.command_inout("Start")

    def ReadOne(self, ind):
        try:
            if ind == 1:
                value = self.proxy.read_attribute("MeanValue").value
            else:
                value = self.proxy.read_attribute("StdDevValue").value

        except Exception:
            value = -999
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
        pass

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.proxy.write_attribute("NbTriggers", value)

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            tango_device = self.node + ":" + str(self.port) + "/" + \
                self.proxy.name()
            return tango_device
        elif name == "FilePrefix":
            return self.proxy.read_attribute("FilePrefix").value
        elif name == "FileNum":
            return self.proxy.read_attribute("FileNum").value

    def SetAxisExtraPar(self, ind, name, value):
        if name == "FilePrefix":
            self.proxy.write_attribute("FilePrefix", value)
        elif name == "FileNum":
            self.proxy.write_attribute("FileStartNum", value)

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> MHzDAQp01CtrlCtrl dying")
