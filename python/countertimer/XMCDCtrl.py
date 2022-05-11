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

global last_sta


class XMCDCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the XMCD"

    axis_attributes = {
        'TangoDevice': {Type: str, Access: ReadOnly},
        'TangoAttribute': {Type: str, Access: ReadWrite},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The name of the XMCD Tango device'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "CounterTimer"
    model = "XMCD"
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
        self.dft_Offset = 0
        self.Offset = []
        self.AttributeNames = []
        proxy_name = self.RootDeviceName
        if self.TangoHost is not None:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(proxy_name)
        self.proxy = PyTango.DeviceProxy(proxy_name)
        global last_sta
        last_sta = PyTango.DevState.ON

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)
        self.Offset.append(self.dft_Offset)
        self.AttributeNames.append("")

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
            status_string = "XMCD is in ON state"
        elif sta == PyTango.DevState.MOVING:
            status_string = "XMCD is busy"
        sta = PyTango.DevState.ON
        status_string = "XMCD is in ON state"
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
        try:
            value = self.proxy.read_attribute(
                self.AttributeNames[ind - 1]).value
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
        pass

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            tango_device = self.node + ":" + str(self.port) + "/" + \
                self.proxy.name()
            return tango_device
        if name == "TangoAttribute":
            return self.AttributeNames[ind - 1]

    def SetAxisExtraPar(self, ind, name, value):
        if name == "TangoAttribute":
            self.AttributeNames[ind - 1] = value

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> XMCDCtrl dying ")
