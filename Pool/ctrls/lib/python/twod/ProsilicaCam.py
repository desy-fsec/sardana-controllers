import PyTango
from sardana.pool.controller import TwoDController
import time

# Still to be implemented: how to StopAcquisition after start it in a scan.
# Possibilities:
#               -> with a post-acq hooks using SendToController("StopAcquisition")
#               -> implement it in the StateOne function of this controller
#                  using the FileCounter attribute

class ProsilicaCamCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the Prosilica camara"

    ctrl_extra_attributes = {'ExposureTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'}}

			     
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the ProsilicaCam Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        TwoDController.__init__(self,inst,props, *args, **kwargs)
        print "PYTHON -> TwoDController ctor for instance",inst

        self.ct_name = "ProsilicaCamCtrl/" + self.inst_name
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
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In AddDevice method for index",ind
        TwoDController.AddDevice()
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.ExposureTime.append(self.dft_ExposureTime)
        self.AcquireMode.append(self.dft_AcquireMode)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        TwoDController.DeleteDevice()
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"Camera ready")
            elif sta == PyTango.DevState.RUNNING:
                sta = PyTango.DevState.MOVING
                tup = (sta,"Camera taking images")
            elif sta == PyTango.DevState.FAULT:
                tup = (sta,"Camera in FAULT state")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In ReadOne method for index",ind
        #The ProsilicaCam return an Image in type encoded
        tmp_value = 0.0
        if self.device_available[ind-1] == 1:
            return tmp_value

    def PreStartAll(self):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In PreStartAllCT method"
        pass

    def PreStartOne(self,ind):
        return True
		
    def StartOne(self,ind):
        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In StartOneCT method for index",ind
        self.proxy[ind-1].command_inout("StartSingleAcquisition")
       
    def GetPar(self, ind, par_name):       
        if par_name == "XDim":
            if self.device_available[ind-1]:
                return int(self.proxy[ind-1].read_attribute("MaxWidth").value)
        elif par_name == "YDim":
            if self.device_available[ind-1]:
                return int(self.proxy[ind-1].read_attribute("MaxHeight").value)
        
	
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("Exposure").value

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",valu
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Exposure",value)
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        cmd, arg = in_data.split(" ")
        if cmd == "StopAcquisition":
            self.proxy[ind-1].command_inout("StopAcquisition")
        elif cmd == "StartAcquisition":
            self.proxy[ind-1].command_inout("StartAcquisition")
            

        return "Nothing sent"
    
        
    def __del__(self):
        print "PYTHON -> ProsilicaCamCtrl/",self.inst_name,": killed"

        
if __name__ == "__main__":
    obj = TwoDController('ProsilicaCam Detector')
