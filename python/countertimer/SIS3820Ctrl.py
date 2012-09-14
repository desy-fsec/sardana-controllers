import PyTango
from sardana.pool.controller import CounterTimerController
import time


from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class SIS3820Ctrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the SIS3820"
    axis_attributes = {'Offset':{Type:float,Access:ReadWrite}}
			     
    class_prop = {'RootDeviceName':{Type:str,Description:'The root name of the SIS3820 Tango devices'}}
      
    gender = "CounterTimer"
    model = "SIS3820"
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
            tup = (sta,"Status error string from controller")
            return tup

    def PreReadAll(self):
        pass
        

    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self,ind):
         if self.device_available[ind-1] == 1:
             return self.proxy[ind-1].read_attribute("Counts").value
	
    def AbortOne(self,ind):
		pass
        
    def PreStartAllCT(self):
		self.wantedCT = []

    def PreStartOneCT(self,ind):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].command_inout("Reset")
            return True
        else:
            raise RuntimeError,"Ctrl Tango's proxy null!!!"
            return False
		
    def StartOneCT(self,ind):
        self.wantedCT.append(ind)
	
    def StartAllCT(self):
        self.started = True
        self.start_time = time.time()
		     	
    def LoadOne(self,ind,value):
		pass
	
    def GetExtraAttributePar(self,ind,name):
        if name == "Offset":
            if self.device_available[ind-1]:
                return float(self.proxy[ind-1].read_attribute("Offset").value)
        
            
    def SetExtraAttributePar(self,ind,name,value):
        if name == "Offset":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Offset",value)
			
    def SendToCtrl(self,in_data):
        return "Nothing sent"

    def start_acquisition(self, value=None):
        print "Teresa: my start_aquisition"
    
    def __del__(self):
        print "PYTHON -> SIS3820Ctrl/",self.inst_name,": dying"

 
if __name__ == "__main__":
    obj = SIS3820Ctrl('test')
