import logging
import numpy
import PyTango
from pool import CounterTimerController

class MythenCoTiCtrl(CounterTimerController):
    """TODO"""
    
    MaxDevice = 1
    class_prop = {'MythenDeviceName':{'Description' : 'Mythen Tango device', 'Type' : 'PyTango.DevString'}}
                  
    
    
    def __init__(self, inst, props):
        #        self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self,inst,props)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst), repr(props))
        try:
            self.MythenDevice = PyTango.DeviceProxy(self.MythenDeviceName)
        except PyTango.DevFailed, e:
            self._log.error("__init__(): Could not create a device proxy from following device name: %s.\nException: %s", 
                            self.MythenDeviceName, e)
            raise
        
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        pass
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        pass
        
    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        if self.MythenDevice is None:
            return PyTango.DevState.FAULT
        try:
            state = self.MythenDevice.state()
            return (state, "Mythen DeviceProxy present.") 
        except Exception, e:
            self._log.error("StateOne(%d): Could not verify state of the device: %s.\nException: %s", 
                            axis, self.MythenDeviceName, e)
            return (PyTango.DevState.UNKNOWN, "Mythen DeviceProxy is not responding.")
        
    def PreReadOne(self, axis):
        self._log.debug("PreReadOne(%d): Entering...", axis)
        pass
        
    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        try:
            value = self.MythenDevice.ExposureTime
            return value 
        except Exception, e:
            self._log.error("StateOne(%d): Could not read exposure time of the device: %s.\nException: %s", 
                            axis, self.MythenDeviceName, e)
            
    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        state = self.MythenDevice.state()
        if state == PyTango.DevState.MOVING:
            self.MythenDevice.command_inout("StopAcquisition")
    
    def StartAllCT(self):
        """Starting the acquisition is done only if before was called PreStartOneCT for master channel."""
        self._log.debug("StartAllCT(): Entering...")
        try:
            self.MythenDevice.command_inout("StartAcquisition")
        except Exception, e:
            self._log.error("StartAllCT(): Could not start acquisition on the device: %s.\nException: %s", 
                            self.MythenDeviceName, e)
            raise
        
    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(%d, %f): Entering...", axis, value)    
        try:
            self.MythenDevice.ExposureTime = value
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not configure device: %s.\nException: %s", self.MythenDeviceName, e)
            raise
