import PyTango
# from sardana import pool
from sardana.pool.controller import CounterTimerController, Type, \
    Description, DefaultValue
import time
# import datetime
# import sys
# from HasyVirtualCounterLib import *
from sardana.PoolController.countertimer.HasyVirtualCounterLib import \
    reset, myread


class HasyVirtualCounterCtrl(CounterTimerController):
    "This class is a Tango Sardana CounterTimer controller " + \
        "for defined virtual counters"

    ctrl_properties = {
        'LibId': {Type: 'PyTango.DevLong',
                  Description: 'Id for the functions argument',
                  DefaultValue: 1}
    }

    gender = "VirtualCounter"
    model = "Best"
    organization = "DESY"
    image = "dummy_ct_ctrl.png"
    icon = ""
    logo = "ALBA_logo.png"

    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)

    def AddDevice(self, axis):
        CounterTimerController.AddDevice(self, axis)
        if axis > self.MaxDevice:
            raise Exception("Only one axis ist allowed")

    def DeleteDevice(self, axis):
        CounterTimerController.DeleteDevice(self, axis)

    def PreStateAll(self):
        pass

    def StateAll(self):
        pass

    def StateOne(self, axis):
        state, status = PyTango.DevState.ON, "On"
        return (state, status)

    def PreReadAll(self):
        pass

    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        return myread(self.LibId)

    def AbortOne(self, axis):
        pass

    def PreStartAll(self):
        pass

    def StartOne(self, axis, value):
        reset(self.LibId)
        pass

    def StartAll(self):
        self._started = True
        self._start_time = time.time()

    def LoadOne(self, axis, value, repetitions, latency_time):
        pass

    def GetAxisExtraPar(self, axis, name):
        pass

    def SetAxisExtraPar(self, ind, name, value):
        pass

    def SendToCtrl(self, in_data):
        return "Adios"
