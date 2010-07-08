import PyTango
from pool import CounterTimerController
import time

class SIS3820Ctrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the SIS3820"
    ctrl_extra_attributes = {'Offset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'}}
			     
    class_prop = {'RootDevName':{'Type':'PyTango.DevString','Description':'The root name of the SIS3820 Tango devices'}}
	
    MaxDevice = 97
	
    def __init__(self,inst,props):
        CounterTimerController.__init__(self,inst,props)
#        print "PYTHON -> SIS3820Ctrl ctor for instance",inst

        self.ct_name = "SIS3820Ctrl/" + self.inst_name
        self.db = PyTango.Database()
        name_dev_ask =  self.RootDevName + "*"
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
#		print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In AddDevice method for index",ind
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.Offset.append(self.dft_Offset)
		
        
    def DeleteDevice(self,ind):
        print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In DeleteDevice method for index",ind
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
		
    def StateOne(self,ind):
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            tup = (sta,"Status error string from controller")
            return tup

    def PreReadAll(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In PreReadAll method"
        pass
        

    def PreReadOne(self,ind):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In ReadOne method for index",ind
         if self.device_available[ind-1] == 1:
             return self.proxy[ind-1].read_attribute("Counts").value
	
    def AbortOne(self,ind):
		pass
        
    def PreStartAllCT(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In PreStartAllCT method"
		self.wantedCT = []

    def PreStartOneCT(self,ind):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].command_inout("Reset")
            return True
        else:
            raise RuntimeError,"Ctrl Tango's proxy null!!!"
            return False
		
    def StartOneCT(self,ind):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In StartOneCT method for index",ind
        self.wantedCT.append(ind)
	
    def StartAllCT(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In StartAllCT method"
        self.started = True
        self.start_time = time.time()
		     	
    def LoadOne(self,ind,value):
		pass
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In LoadOne method for index",ind," with value",value
	
    def GetExtraAttributePar(self,ind,name):
        if name == "Offset":
            if self.device_available[ind-1]:
                return float(self.proxy[ind-1].read_attribute("Offset").value)
        
            
    def SetExtraAttributePar(self,ind,name,value):
        if name == "Offset":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Offset",value)
			
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"

    def __del__(self):
        print "PYTHON -> SIS3820Ctrl/",self.inst_name,": dying"

 
if __name__ == "__main__":
    obj = SIS3820Ctrl('test')
