from PyTango import DevState, AttrQuality
from sardana import pool
from sardana.pool.controller import IORegisterController
import taurus

class BL13EHCryoIORController(IORegisterController):

    axis_attributes ={'Labels':
                          {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarStringArray',
                           'Description':'String list with the meaning of each discrete position',
                           'R/W Type':'PyTango.READ_WRITE'},
                      }
    MaxDevice = 2

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        #self.eps_dev = taurus.Device('bl13/ct/eps-plc-01')
        self.labels = ['FAR:0 OUT:1 IN:2', 'OUT:0 IN:1']

    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def StateOne(self, axis):
        state = DevState.ALARM
        return (state, 'Device is STILL NOT WORKING: %s state.' % state)

    def ReadOne(self, axis):
        return 0
        if axis == 1:
            # Read cryopos
            pass
        elif axis == 2:
            # Read cryoshutter
            pass
            
        return -1

    def WriteOne(self, axis, value):
        if axis == 1:
            # Change cryopos
            pass
        elif axis == 2:
            # Change cryoshutter
            pass
        
    def GetAxisExtraPar(self, axis, name):
        if name == 'Labels':
            return self.labels[axis - 1]
        return None

    def SetAxisExtraPar(self, axis, name, value):
        if name == 'Labels':
            self.labels[axis - 1] = value
