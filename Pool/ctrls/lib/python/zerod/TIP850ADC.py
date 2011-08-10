import PyTango
from pool import ZeroDController
import time

class TIP850ADCCtrl(ZeroDController):
    "This class is the Tango Sardana Zero D controller for the TIP850ADC"

    ctrl_extra_attributes = {}

			     
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the TIP850ADC Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props):
        ZeroDController.__init__(self,inst,props)
#        print "PYTHON -> ZeroDController ctor for instance",inst

        self.ct_name = "TIP850ADCCtrl/" + self.inst_name
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
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In AddDevice method for index",ind
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            tup = (sta,"Status error string from controller")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In ReadOne method for index",ind
        if self.device_available[ind-1] == 1:
            return self.proxy[ind-1].read_attribute("Value").value

    def PreStartAll(self):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In PreStartAll method"
        self.wanted = []

    def PreStartOne(self,ind):
        pass
		
    def StartOne(self,ind):
        #print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In StartOne method for index",ind
        self.wanted.append(ind)
	
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        pass


    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        pass
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> TIP850ADCCtrl/",self.inst_name,": Aarrrrrg, I am dying"

        
if __name__ == "__main__":
    obj = ZeroDController('test')
