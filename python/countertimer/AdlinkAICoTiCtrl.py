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
    The only way to use this controller is to define up to 5 channels 
    and create a measurement group where the first channel is a master channel. 
    The Adlink card works in a way where acquisition for all channels is started only once 
    and in controller this is done when StartsAll() method was called for this controller, 
    only when PreStartOne() was called for master channel. 
    
    Configuration of Adlink card is done in LoadOne() method where size of acquisition buffer 
    is calculated from acquisition time and SampleRate property. 
    
    Value returned by a channggel is an average of buffer values. If you need also 
    standard deviation of these values you can read it from extra attribute SD right after reading 
    value of the channel. 
    If you need SD value in measurement group you have two options:
        1- Add one tango attribute counter per each SD and place it in a measurement group after 
            corresponding Adlink counter.
        2- Add an ExtraColumn with the attribute SD."""
    
    MaxDevice = 5
    class_prop = {'AdlinkAIDeviceName':{'Description' : 'AdlinkAI Tango device', 'Type' : 'PyTango.DevString'},
                  'SampleRate':{'Description' : 'SampleRate set for AIDevice','Type' : 'PyTango.DevLong'}}
    
    ctrl_extra_attributes ={ "SD": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Standard deviation',
                                 'R/W Type':'PyTango.READ'
                                },
                             "FORMULA": {'Type':'PyTango.DevString',
                                         'Description':'The formula to get the real value.\ne.g. "(VALUE/10)*1e-06"',
                                         'R/W Type':'PyTango.READ_WRITE'
                                        },
                             "SHAREDFORMULA": {'Type':'PyTango.DevBoolean',
                                         'Description':'If you want to share the same formula for all the channels set it to true"',
                                         'R/W Type':'PyTango.READ_WRITE'
                                        }
                            }
    
    
    def __init__(self, inst, props):
        #        self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self,inst,props)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst), repr(props))


        self.sd = {}
        self.formulas = {}
        self.sharedFormula = {}
        self.master = None
        self.integrationTime = 0
        
        try:
            self.AIDevice = PyTango.DeviceProxy(self.AdlinkAIDeviceName)
        except PyTango.DevFailed, e:
            self._log.error("__init__(): Could not create a device proxy from following device name: %s.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        self.sd[axis] = 0
        self.formulas[axis] = 'value'
        self.sharedFormula[axis] = False
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        self.sd.pop(axis)
        self.formulas.pop(axis)
        self.sharedFormula.pop(axis)
        
    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        if self.AIDevice is None:
            return PyTango.DevState.FAULT
        try:
            self.state = self.AIDevice.state()
            if self.master is None:
                self.state = PyTango.DevState.ON
            else:
                if self.state == PyTango.DevState.ON:
                    self.master = None
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
        if axis == 1:
            return self.integrationTime

        if state == PyTango.DevState.ON: 
            mean = self.AIDevice["C0%s_MeanLast" % (axis - 2)].value
            std = self.AIDevice["C0%s_StdDevLast" % (axis - 2)].value
            
            self.sd[axis] = std

            value = mean
            mean = eval(self.formulas[axis])

            self._log.debug("ReadOne(%d): mean=%f, sd=%f", 
                            axis, mean, std)
        return mean
            
    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        state = self.AIDevice.state()
        if state == PyTango.DevState.RUNNING:
            self.AIDevice.stop()
    
    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        self.axesToStart = []
        try:
            state = self.AIDevice.state()
            if state == PyTango.DevState.RUNNING:
                self.AIDevice.stop()
        except Exception, e:
            self._log.error("PreStartAllCT(): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def PreStartOneCT(self, axis):
        """Here we are counting which axes are going to be start, so later we can distinguish 
        if we are starting only the master channel."""
        self._log.debug("PreStartOneCT(%d): Entering...", axis)
        #self.axesToStart.append(axis) #I think this is not needed because you can not start only one channel.
        return True

    def StartAllCT(self):
        """Starting the acquisition is done only if before was called PreStartOneCT for master channel."""
        self._log.debug("StartAllCT(): Entering...")
        #if not (len(self.axesToStart) == 1 and self.axesToStart[0] == self.master):
        #    return
        try:
            self.AIDevice.start()
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
        self.integrationTime = value
        try:
            self.state = self.AIDevice.state()
            if self.state == PyTango.DevState.RUNNING or self.state == PyTango.DevState.ON:
                self.AIDevice.stop()
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            axis, value, self.AdlinkAIDeviceName, e)
            raise
        bufferSize = int(self.integrationTime * self.SampleRate)
        try:
            self.AIDevice['NumOfTriggers'] = 1
            self.AIDevice['TriggerInfinite'] = 0    
            self.AIDevice['SampleRate'] = self.SampleRate
            self.AIDevice['ChannelSamplesPerTrigger'] = bufferSize
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not configure device: %s.\nException: %s", self.AdlinkAIDeviceName, e)
            raise
        
    def GetExtraAttributePar(self, axis, name):
        self._log.debug("GetExtraAttributePar(%d, %s): Entering...", axis, name)
        if name.lower() == "sd":
            return self.sd[axis]
        if name.lower() == "formula":
            return self.formulas[axis]
        if name.lower() == "sharedformula":
            return self.sharedFormula[axis]


    def SetExtraAttributePar(self,axis, name, value):
        #self.set_extra_attribute_par(axis, name, value) #todo Ask to zibi what is this!!
        if name.lower() == "formula":
            self.formulas[axis] = value

        if name.lower() == "sharedformula":
            self.sharedFormula[axis] = value
            if value:
                for i in self.formulas:
                    self.formulas[i] = self.formulas[axis]

