import PyTango
import pool
from pool import CounterTimerController
import time
import datetime
import sys

class Counter:
    def __init__(self, axis):
        self.axis = axis
        self.value = None
        self.state = None
        self.status = None

class SimuCoTiController(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the SimuCoTiCtrl tango device"
              
    class_prop = {'DevName':{'Type':'PyTango.DevString','Description':'The ctrl simulator Tango device name'}}
                 
    gender = "Simulation"
    model  = "Best"
    organization = "CELLS - ALBA"
    image = "motor_simulator.png"
    icon = "motor_simulator_icon.png"
    logo = "ALBA_logo.png"
                     
    MaxDevice = 1024

    def __init__(self, inst, props):
        CounterTimerController.__init__(self, inst, props)

        self._counters = {}
        self._dp = None
        self._started = False

    def _getCTCtrl(self):
        if not self._dp:
            self._dp = pool.PoolUtil().get_device(self.inst_name, self.DevName)
        return self._dp

    def AddDevice(self, axis):
        if axis > self.MaxDevice:
            raise Exception("Invalid axis %d" % axis)
        self._counters[axis] = Counter(axis)
            
    def DeleteDevice(self, axis):
        if not self._counters.has_key(axis):
            raise Exception("Invalid axis %d" % axis)
        del self._counters[axis]
        
    def PreStateAll(self):
        for c in self._counters.values():
            c.state, c.switchstate = None, None
            
    def StateAll(self):
        for c in self._counters.values():
            try:
                self._getCTCtrl().ping()
                c.state, c.status = self._getCTCtrl().command_inout("GetCounterState",c.axis), "OK"
            except:
                c.state, c.status = PyTango.DevState.OFF, "Offline"
            
    def StateOne(self, axis):
        c = self._counters[axis]
        return (int(c.state), c.status)

    def PreReadAll(self):
        pass
        
    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        return self._getCTCtrl().command_inout("GetCounterValue", axis)
    
    def AbortOne(self, axis):
        self._getCTCtrl().command_inout("Stop", axis);
        self._started = False
        
    def PreStartAllCT(self):
        self._wantedCT = []
    
    def StartOneCT(self, axis):
        self._wantedCT.append(axis)
    
    def StartAllCT(self):
        for axis in self._wantedCT:
            self._getCTCtrl().command_inout("Start", axis)
        self._started = True
        self._start_time = time.time()
                 
    def LoadOne(self, axis, value):
        self._getCTCtrl().command_inout("Clear", axis)
    
    def GetExtraAttributePar(self, axis, name):
        pass

    def SetExtraAttributePar(self,ind,name,value):
        pass
        
    def SendToCtrl(self,in_data):
        return "Adios"

        
if __name__ == "__main__":
    obj = SimuCoTiController('test',{'DevName' : 'tcoutinho/simulator/motctrl1'})

