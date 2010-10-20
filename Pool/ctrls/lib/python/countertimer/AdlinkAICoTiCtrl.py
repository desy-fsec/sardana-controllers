import logging
import numpy
import PyTango
from pool import CounterTimerController


def evalState(state):
    """This function converts Adlink device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return PyTango.DevState.MOVING
    elif state == PyTango.DevState.STANDBY:
        return PyTango.DevState.ON
    else:
        return state

class AdlinkAICoTiCtrl(CounterTimerController):
    """This class is the Sardana CounterTimer controller for the Adlink adc based counters.
    The only way to use this controller is to define up to 4 channels 
    and create a measurement group where one of this channel is a master channel. 
    The Adlink card works in a way where acquisition for all channels is started only once 
    and in controller this is done when StartsAll() method was called for this controller, 
    only when PreStartOne() was called for master channel. 
    
    Configuration of Adlink card is done in LoadOne() method where size of acquisition buffer 
    is calculated from acquisition time and SampleRate property. 
    
    Value returned by a channel is an average of buffer values. If you need also 
    standard deviation of these values you can read it from extra attribute SD right after reading 
    value of the channel. If you need SD value in measurement group, add one tango attribute counter
    per each SD and place it in a measurement group after corresponding Adlink counter."""
    
    MaxDevice = 4
    class_prop = {'AdlinkAIDeviceName':{'Description' : 'AdlinkAI Tango device', 'Type' : 'PyTango.DevString'},
                  'SampleRate':{'Description' : 'SampleRate set for AIDevice','Type' : 'PyTango.DevLong'}}
    
    ctrl_extra_attributes ={ "SD": {'Type':'PyTango.DevDouble','Description':'Standard deviation','R/W Type':'PyTango.READ'}}
    
    
    def __init__(self, inst, props):
        #        self._log.setLevel(logging.DEBUG)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst), repr(props))
        CounterTimerController.__init__(self,inst,props)

        self.sd = {}
        self.master = None
        
        try:
            self.AIDevice = PyTango.DeviceProxy(self.AdlinkAIDeviceName)
        except PyTango.DevFailed, e:
            self._log.error("__init__(): Could not create a device proxy from following device name: %s.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        self.sd[axis] = 0
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        self.sd.pop(axis)
        
    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        if self.AIDevice is None:
            return PyTango.DevState.FAULT
        try:
            self.state = self.AIDevice.state()
            return (evalState(self.state), "AI DeviceProxy present.") 
        except Exception, e:
            self._log.error("StateOne(%d): Could not verify state of the device: %s.\nException: %s", 
                            axis, self.AdlinkAIDeviceName, e)
            return (PyTango.DevState.UNKNOWN, "AI DeviceProxy is not responding.")
        
    def PreReadOne(self, axis):
        self._log.debug("PreReadOne(%d): Entering...", axis)
        self.sd[axis] = 0
        
    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        state = self.AIDevice.state() 
        mean = 0
        if state == PyTango.DevState.ON: 
            signal = self.AIDevice.read_attribute("C0%s_ChannelValues" % (axis - 1)).value
            n_signal = numpy.array(signal)
            mean = float(n_signal.mean())
            self.sd[axis] = float(n_signal.std())
            self._log.debug("ReadOne(%d): mean=%f, max=%f, min=%f, sd=%f", 
                            axis, n_signal.mean(), n_signal.max(), n_signal.min(), n_signal.std())
        return mean
            
    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        state = self.AIDevice.state()
        if state == PyTango.DevState.RUNNING:
            self.AIDevice.command_inout("Stop")
    
    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        self.axesToStart = []
        try:
            state = self.AIDevice.state()
            if state == PyTango.DevState.RUNNING:
                self.AIDevice.command_inout('Stop')
        except Exception, e:
            self._log.error("PreStartAllCT(): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def PreStartOneCT(self, axis):
        """Here we are counting which axes are going to be start, so later we can distinguish 
        if we are starting only the master channel."""
        self._log.debug("PreStartOneCT(%d): Entering...", axis)
        self.axesToStart.append(axis)
        return True

    def StartAllCT(self):
        """Starting the acquisition is done only if before was called PreStartOneCT for master channel."""
        self._log.debug("StartAllCT(): Entering...")
        if not (len(self.axesToStart) == 1 and self.axesToStart[0] == self.master):
            return
        try:
            self.AIDevice.command_inout("Start")
        except Exception, e:
            self._log.error("StartAllCT(): Could not start acquisition on the device: %s.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def PreLoadOne(self, axis, value):
        """Here we are keeping a reference to the master channel, so later in StartAll() 
        we can distinguish if we are starting only the master channel."""
        self._log.debug("PreLoadOne(%d, %f): Entering...", axis, value)
        self.master = None
        return True
        
    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(%d, %f): Entering...", axis, value)
        self.master = axis
        try:
            self.state = self.AIDevice.state()
            if self.state == PyTango.DevState.RUNNING or self.state == PyTango.DevState.ON:
                self.AIDevice.command_inout('Stop')
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            axis, value, self.AdlinkAIDeviceName, e)
            raise
        bufferSize = int(value * self.SampleRate)
            
        try:
            self.AIDevice.write_attribute('NumOfTriggers', 1)
            self.AIDevice.write_attribute('TriggerInfinite', 0)    
            self.AIDevice.write_attribute('SampleRate', self.SampleRate)
            self.AIDevice.write_attribute('ChannelSamplesPerTrigger', bufferSize)
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not configure device: %s.\nException: %s", self.AdlinkAIDeviceName, e)
            raise
        
    def GetExtraAttributePar(self, axis, name):
        self._log.debug("GetExtraAttributePar(%d, %s): Entering...", axis, name)
        if name.lower() == "sd":
            return self.sd[axis]

    def SetExtraAttributePar(self,axis, name, value):
        self.set_extra_attribute_par(axis, name, value)