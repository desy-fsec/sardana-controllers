import PyTango
import pool
from pool import CounterTimerController
import time
import datetime
import sys
from HasyVirtualCounterLib import *

class HasyVirtualCounter(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the SimuCoTiCtrl tango device"
              
    class_prop = {'LibId':{'Type':'PyTango.DevLong',
                           'Description':'Id for the functions argument',
                           'DefaultValue':1}}
    
    gender = "VirtualCounter"
    model  = "Best"
    organization = "DESY"
    image = "dummy_ct_ctrl.png"
    icon = ""
    logo = "ALBA_logo.png"
                     
    MaxDevice = 1

    def __init__(self, inst, props):
        CounterTimerController.__init__(self, inst, props)

    def AddDevice(self, axis):
        if axis > self.MaxDevice:
            raise Exception("Only one axis ist allowed")

    def DeleteDevice(self, axis):
        pass
        
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
        
    def PreStartAllCT(self):
        pass
    
    def StartOneCT(self, axis):
        reset(self.LibId)
        pass
    
    def StartAllCT(self):
        self._started = True
        self._start_time = time.time()
                 
    def LoadOne(self, axis, value):
        pass
    
    def GetExtraAttributePar(self, axis, name):
        pass

    def SetExtraAttributePar(self,ind,name,value):
        pass
    
    def SendToCtrl(self,in_data):
        return "Adios"

 
