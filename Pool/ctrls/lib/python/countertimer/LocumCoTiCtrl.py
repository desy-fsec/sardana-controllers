import logging
import numpy
import PyTango
#from pool import CounterTimerController
from AdlinkAICoTiCtrl import *


def evalState(state):
    """This function converts Adlink device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return PyTango.DevState.MOVING
    elif state == PyTango.DevState.STANDBY:
        return PyTango.DevState.ON
    else:
        return state

class LocumCoTiCtrl(AdlinkAICoTiCtrl):
    """This class is the Sardana CounterTimer controller for the LoCum4.
    """
    
    MaxDevice = 5
    class_prop = {'AdlinkAIDeviceName':{'Description' : 'AdlinkAI Tango device', 'Type' : 'PyTango.DevString'},
                  'LoCum4DeviceName':{'Description':'LoCum4 Tango device', 'Type':'PyTango.DevString'},
                  'SampleRate':{'Description':'SampleRate set for AIDevice','Type':'PyTango.DevLong'}}

    
    #ctrl_extra_attributes ={ "SD": {'Type':'PyTango.DevDouble','Description':'Standard deviation','R/W Type':'PyTango.READ'}}
                             #"SampleRate":{'Type':'PyTango.DevLong','Description':'SampleRate set for AIDevice','R/W Type':'PyTango.READ'}}
    
    def __init__(self, inst, props):

        AdlinkAICoTiCtrl.__init__(self,inst,props)
        #        self._log.setLevel(logging.DEBUG)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst), repr(props))

        try:
            self.Locum = PyTango.DeviceProxy(self.LoCum4DeviceName)
        except PyTango.DevFailed, e:
            pass
            self._log.error("__init__(): Could not create a device proxy from following device name: %s.\nException: %s",
                            self.LoCum4DeviceName, e)
            raise
        
    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        stateAd = self.AIDevice.state() 
        stateLoc = self.Locum.state() 
        mean = 1e-100
        if axis == 1:
            return self.integrationTime
        if stateAd == PyTango.DevState.ON and stateLoc == PyTango.DevState.ON: 
            mean = self.Locum["I%s"%(axis-1)].value
            #self.sd[axis] = float(self.Locum["BufferCh%sStdDesv"%(axis-1)].value)
            self._log.debug("ReadOne(%d): mean=%f",axis, mean)
        return mean
            
        
