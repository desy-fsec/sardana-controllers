import PyTango
from sardana.pool.controller import CounterTimerController
import time


from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class LimaCounterCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the LimaCounter"
    axis_attributes = {'Offset':{Type:float,Access:ReadWrite}}
			     
    class_prop = {'RoiCounterDeviceName':{Type:str,Description:'The name of the RoiCounterDeviceServer device from Lima'}}
      
    gender = "CounterTimer"
    model = "LimaCounter"
    organization = "DESY"
    state = ""
    status = ""
    
    def __init__(self,inst,props, *args, **kwargs):
        CounterTimerController.__init__(self,inst,props, *args, **kwargs)
        self.proxy = PyTango.DeviceProxy(self.RoiCounterDeviceName)
        self.started = False
        
    def AddDevice(self,ind):
        CounterTimerController.AddDevice(self,ind)
		
        
    def DeleteDevice(self,ind):
        CounterTimerController.DeleteDevice(self,ind)
        self.proxy =  None
        
		
    def StateOne(self,ind):
        try:
            counterstatus = self.proxy.CounterStatus
        except:
            sta = PyTango.DevState.FAULT
            status = "roicounter Lima device not started"
            tup = (sta,status)
            return tup
        if counterstatus == -1:
            sta = PyTango.DevState.MOVING
            status = "Taking data"
        elif counterstatus == 0:
            sta = PyTango.DevState.ON
            status = "Calculation done"
        elif counterstatus == -2:
            sta = PyTango.DevState.FAULT
            status = "Not RoIs defined"
        tup = (sta,status)
        return tup

    def PreReadAll(self):
        pass
        

    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self,ind):
        counts = self.proxy.command_inout("readCounters",0)
        return counts[7*(ind-1) + 2]
	
    def AbortOne(self,ind):
        pass
        
    def PreStartAllCT(self):
        self.wantedCT = []

    def PreStartOneCT(self,ind):
        return True
		
    def StartOneCT(self,ind):
        self.wantedCT.append(ind)
	
    def StartAllCT(self):
        self.started = True
        self.start_time = time.time()
		     	
    def LoadOne(self,ind,value):
        pass
	
    def GetExtraAttributePar(self,ind,name):
        pass
        
            
    def SetExtraAttributePar(self,ind,name,value):
        pass
			
    def SendToCtrl(self,in_data):
        return "Nothing sent"

    def start_acquisition(self, value=None):
        print "Teresa: my start_aquisition"
    
    def __del__(self):
        print "PYTHON -> LimaCounterCtrl/",self.inst_name,": dying"

 
if __name__ == "__main__":
    obj = LimaCounterCtrl('test')
