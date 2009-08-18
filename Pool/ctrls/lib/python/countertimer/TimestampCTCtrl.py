import time
from PyTango import DevState
from pool import CounterTimerController

class TimeStampCTController(CounterTimerController):
    "This controller offers two channels which correspond to the begin
    and end timestamps of the acquisition."
                 
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
        return (DevState.ON, "Always ON")

    def PreReadAll(self):
        pass
        
    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        if axis == 1:
            return self._start_time
        elif axis == 2:
            return int(1000 * time.time())
    
    def AbortOne(self, axis):
        self._start_time = None
        
    def PreStartAllCT(self):
        pass
    
    def StartOneCT(self, axis):
        pass
    
    def StartAllCT(self):
        self._start_time = int(1000 * time.time())
                 
    def LoadOne(self, axis, value):
        pass
    
    def GetExtraAttributePar(self, axis, name):
        pass

    def SetExtraAttributePar(self,ind,name,value):
        pass
        
    def SendToCtrl(self,in_data):
        return ""
