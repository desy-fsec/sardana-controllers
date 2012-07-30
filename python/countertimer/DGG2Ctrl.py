import PyTango
from sardana.pool.controller import CounterTimerController
import time

from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

class DGG2Controller(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the DGG2 timer"
			     
    ctrl_properties = {'RootDeviceName':{Type:str,Description:'The root name of the DGG2 timer Tango devices'}}

    gender = "CounterTimer"
    model = "DGG2"
    organization = "DESY"
    state = ""
    status = ""
    
    def __init__(self,inst,props, *args, **kwargs):
        CounterTimerController.__init__(self,inst,props, *args, **kwargs)
        self.db = PyTango.Database()
        name_dev_ask =  self.RootDeviceName + "*"
	self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.device_available = []
	for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.max_device =  self.max_device + 1
        self.started = False
        self.dft_Offset = 0
        self.Offset = []

    def AddDevice(self,ind):
        CounterTimerController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.Offset.append(self.dft_Offset)
		
        
    def DeleteDevice(self,ind):
        CounterTimerController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
		
    def StateOne(self,ind):
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                status_string = "Timer is in ON state"
            elif sta == PyTango.DevState.MOVING:
                status_string = "Timer is busy"
            tup = (sta, status_string)
            return tup

    def PreReadAll(self):
        pass
        

    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        pass

    def PreStartOne(self,ind,pos):
        return True

    def ReadOne(self,ind):
         if self.device_available[ind-1] == 1:
             sample_time = self.proxy[ind-1].read_attribute("SampleTime").value
             remaining_time = self.proxy[ind-1].read_attribute("RemainingTime").value
             v = sample_time - remaining_time
             return  v
	
    def AbortOne(self,ind):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].command_inout("Stop")
        
    def PreStartAllCT(self):
		self.wantedCT = []

    def PreStartOneCT(self,ind):
        pass
		
    def StartOneCT(self,ind):
        if self.device_available[ind-1] == 1:
            self.wantedCT.append(ind)
	
    def StartAllCT(self):
        for index in self.wantedCT:
            self.proxy[index-1].command_inout("Start")
		     	
    def LoadOne(self,ind,value):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].write_attribute("SampleTime", value)
	
    def GetExtraAttributePar(self,ind,name):
        pass
        
            
    def SetExtraAttributePar(self,ind,name,value):
        pass
			
    def SendToCtrl(self,in_data):
        return "Nothing sent"

    def __del__(self):
        print "PYTHON -> DGG2Controller/",self.inst_name,": dying"

