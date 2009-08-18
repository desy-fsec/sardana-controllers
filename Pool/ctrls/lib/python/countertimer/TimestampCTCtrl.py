import time
from PyTango import DevState
from pool import CounterTimerController

class TimeStampCTController(CounterTimerController):
    """This controller offers two channels which correspond to the begin
    and end timestamps of the acquisition.
    This output is intended to be used with parallel scripts which collect data that you would
    like to plot together with macros' output.
    """
                 
    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"
                     
    MaxDevice = 2

    def __init__(self, inst, props):
        CounterTimerController.__init__(self, inst, props)

        self._start_time = None

    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def PreStateAll(self):
        pass

    def StateAll(self):
        pass
            
    def StateOne(self, axis):
        return (DevState.ON, "Always ON, just returning timestamps...")

    def PreReadAll(self):
        pass
        
    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        if axis == 1:
            self._log.debug("The begin acquisition timestamp is %f" % self._start_time)
            return self._start_time
        elif axis == 2:
            now = time.time()
            self._log.debug("The current acquisition timestamp is %f" % now)
            return now
    
    def AbortOne(self, axis):
        self._start_time = None
        
    def PreStartAllCT(self):
        pass
    
    def StartOneCT(self, axis):
        pass
    
    def StartAllCT(self):
        self._start_time = time.time()
                 
    def LoadOne(self, axis, value):
        pass
    
    def GetExtraAttributePar(self, axis, name):
        pass

    def SetExtraAttributePar(self,ind,name,value):
        pass
        
    def SendToCtrl(self,in_data):
        return ""
