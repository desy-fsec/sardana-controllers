from PyTango import DevState, AttrQuality
from sardana import pool
from sardana.pool.controller import IORegisterController
import taurus

class BL13EHFastshutterIORController(IORegisterController):

    axis_attributes ={'Labels':
                          {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarStringArray',
                           'Description':'String list with the meaning of each discrete position',
                           'R/W Type':'PyTango.READ_WRITE'},
                      }
    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        self.labels = 'OPEN:0 CLOSE:1'
        self.fake_value = 0

    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def StateOne(self, axis):
        state = DevState.ALARM
        return (state, 'Device is STILL NOT WORKING: %s state.' % state)

    def ReadOne(self, axis):
        return self.fake_value

    def WriteOne(self, axis, value):
        self.fake_value = value
        
    def GetAxisExtraPar(self, axis, name):
        if name == 'Labels':
            return self.labels
        return None

    def SetAxisExtraPar(self, axis, name, value):
        if name == 'Labels':
            self.labels = value
