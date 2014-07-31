import PyTango
from sardana.pool.controller import TwoDController
import time

class PerkinElmerCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the PerkinElmer detector"

    ctrl_extra_attributes = {'ExposureTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'AcquireMode':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},}

			     
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the PerkinElmer Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        TwoDController.__init__(self,inst,props, *args, **kwargs)
        print "PYTHON -> TwoDController ctor for instance",inst

        self.ct_name = "PerkinElmerCtrl/" + self.inst_name
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
        self.dft_ExposureTime = 0
        self.ExposureTime = []
        self.dft_AcquireMode = 0
        self.AcquireMode = []
        self.value = 1
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In AddDevice method for index",ind
        TwoDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.ExposureTime.append(self.dft_ExposureTime)
        self.AcquireMode.append(self.dft_AcquireMode)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        TwoDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"Camera ready")
            elif sta == PyTango.DevState.MOVING:
                tup = (sta,"Camera taking images")
            elif sta == PyTango.DevState.FAULT:
                tup = (sta,"Camera in FAULT state")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In ReadOne method for index",ind
        #The PerkinElmer return an Image in type encoded
        tmp_value = 0.0
        if self.device_available[ind-1] == 1:
            return tmp_value

    def PreStartAll(self):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In PreStartAllCT method"
        pass

    def PreStartOne(self,ind):
        return True
		
    def StartOne(self,ind):
        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In StartOneCT method for index",ind
        if self.AcquireMode[ind-1] == 0:
            self.proxy[ind-1].command_inout("AcquireSubtractedImagesAndSave")
        elif self.AcquireMode[ind-1] == 1:
            self.proxy[ind-1].command_inout("AcquireSubtractedImages")
        elif self.AcquireMode[ind-1] == 2:
            self.proxy[ind-1].command_inout("AcquireRawImagesAndSave")
        elif self.AcquireMode[ind-1] == 3:
            self.proxy[ind-1].command_inout("AcquireDarkImagesAndSave")
        elif self.AcquireMode[ind-1] == 4:
            self.proxy[ind-1].command_inout("AcquireDarkImages")
        else:
            self.proxy[ind-1].command_inout("AcquireSubtractedImagesAndSave")
      
    def LoadOne(self, axis, value):
        self.proxy[ind-1].write_attribute("ExposureTime",value)
 
    def GetPar(self, ind, par_name):       
        if par_name == "XDim":
            return 1
        elif par_name == "YDim":
            return 1
        
	
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("ExposureTime").value
        if name == "AcquireMode":
            return self.AcquireMode[ind-1]

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",valu
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("ExposureTime",value)
        if name == "AcquireMode":
            self.AcquireMode[ind-1] = value
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> PerkinElmerCtrl/",self.inst_name,": killed"

        
if __name__ == "__main__":
    obj = TwoDController('PerkinElmer Detector')
