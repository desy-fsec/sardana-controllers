import PyTango
from sardana.pool.controller import CounterTimerController
# import time

# from sardana import State
from sardana import DataAccess
# from sardana.pool.controller import MotorController
# from sardana.pool.controller import DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


# This controller has to be used with another controller
# for the sis3302 in the MG
# It only reads the counts.


class KromoRoIsCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller " + \
        "for the SIS3302 RoIs"

    axis_attributes = {
        'TangoDevice': {Type: str, Access: ReadOnly},
        'RoIAttributeName': {Type: str, Access: ReadWrite},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the KromoRoIs Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "CounterTimer"
    model = "KromoRoIs"
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
        self.RoIAttributeName = []
        proxy_name = self.RootDeviceName
        if self.TangoHost is not None:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(proxy_name)
        self.proxy = PyTango.DeviceProxy(proxy_name)

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)
        self.RoIAttributeName.append("")

    def DeleteDevice(self, ind):
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy = None

    def StateOne(self, ind):
        sta = self.proxy.command_inout("State")
        if sta == PyTango.DevState.ON:
            status_string = "Device in ON state"
        elif sta == PyTango.DevState.MOVING:
            sta = PyTango.DevState.MOVING
            status_string = "Device MOVING"
        elif sta == PyTango.DevState.OFF:
            sta = PyTango.DevState.FAULT
            status_string = "Error detected"
        tup = (sta, status_string)
        return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def StartOne(self, ind, value):
        return True

    def ReadOne(self, ind):
        value = self.proxy.read_attribute(self.RoIAttributeName[ind - 1]).value
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
        if name == "RoIAttributeName":
            return self.RoIAttributeName[ind - 1]

    def SetAxisExtraPar(self, ind, name, value):
        if name == "RoIAttributeName":
            self.RoIAttributeName[ind - 1] = value

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> KromoRoIsCtrl dying")
