import PyTango
from sardana.pool.controller import ZeroDController
import time

class HasyADCCtrl(ZeroDController):
    "This class is the Tango Sardana Zero D controller for a generic Hasylab ADC"
			     
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the VFCADC Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props,*args, **kwargs):
        ZeroDController.__init__(self,inst,props,*args, **kwargs)
#        print "PYTHON -> ZeroDController ctor for instance",inst

        self.ct_name = "HasyADCCtrl/" + self.inst_name
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
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In AddDevice method for index",ind
        ZeroDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        ZeroDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"ADC is in ON State")
            elif sta == PyTango.DevState.MOVING:
                tup = (sta,"ADC is busy")
            else:
                tup = (sta,"Unknown status")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In ReadOne method for index",ind
        if self.device_available[ind-1] == 1:
            return self.proxy[ind-1].read_attribute("Value").value

    def PreStartAll(self):
#        print "PYTHON -> HasyADCCtrl/",self.inst_name,": In PreStartAll method"
        self.wanted = []

    def PreStartOne(self,ind):
        pass
		
    def StartOne(self,ind):
        #print "PYTHON -> HasyADCCtrl/",self.inst_name,": In StartOne method for index",ind
        self.wanted.append(ind)
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> HasyADCCtrl/",self.inst_name,": being deleted"

        
if __name__ == "__main__":
    obj = ZeroDController('ADC')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
