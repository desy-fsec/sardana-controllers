import PyTango
from sardana.pool.controller import OneDController
import time

class HasyOneDCtrl(OneDController):
    "This class is the Tango Sardana One D controller for Hasylab"

    ctrl_extra_attributes = {'DataLength':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'}}
			     
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the MCA Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        OneDController.__init__(self,inst,props, *args, **kwargs)
        print "PYTHON -> OneDController ctor for instance",inst

        self.ct_name = "HasyOneDCtrl/" + self.inst_name
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
        self.dft_DataLength = 0
        self.DataLength = []
        
    def AddDevice(self,ind):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In AddDevice method for index",ind
        OneDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.DataLength.append(self.dft_DataLength)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        OneDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"The MCA is ready")
        else:
            sta = PyTango.DevState.FAULT
            tup = (sta, "Device not available")

        return tup
    
    def LoadOne(self, axis, value):
        idx = axis - 1
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        

    def PreReadAll(self):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In PreReadOne method for index",ind
        self.proxy[ind-1].command_inout("Read")

    def ReadAll(self):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In ReadOne method for index",ind
        return self.proxy[ind-1].Data

    def PreStartAll(self):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In PreStartAll method"
        pass

    def PreStartOne(self,ind, value):
        return True
		
    def StartOne(self,ind, value):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In StartOne method for index",ind
        self.proxy[ind-1].command_inout("Start")
		
    def AbortOne(self,ind):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In AbortOne method for index",ind
        self.proxy[ind-1].command_inout("Stop")
       
    def GetPar(self, ind, par_name):
        if par_name == "datalength":
            if self.device_available[ind-1]:
                print self.proxy[ind-1].read_attribute("DataLength").value
                return int(self.proxy[ind-1].read_attribute("DataLength").value)

    def SetPar(self,ind,par_name,value):
        if par_name == "datalength":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("DataLength",value)
	
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if name == "BankId":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("BankId").value

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        if name == "BankId":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("BankId",value)
        if name == "Clear":
            if self.device_available[ind-1]:
                self.proxy[ind-1].command_inout("Clear")
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> HasyOneDCtrl/",self.inst_name,": Aarrrrrg, I am dying"

        
if __name__ == "__main__":
    obj = OneDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
