import PyTango
from pool import TwoDController
import time

class LimaCCDCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the LimaCCD"

    ctrl_extra_attributes = {'LatencyTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'ExposureTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'FilePrefix':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'FileSuffix':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'FileDir':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'SavingMode':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'LastImageReady':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'NbFrames':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'TriggerMode':{'Type':'PyTango.DevShort','R/W Type':'PyTango.READ_WRITE'},
			     'CameraType':{'Type':'PyTango.DevString','R Type':'PyTango.READ'},
			     'Reset':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'}}

			     
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the LimaCCD Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props):
        TwoDController.__init__(self,inst,props)
        print "PYTHON -> TwoDController ctor for instance",inst

        self.ct_name = "LimaCCDCtrl/" + self.inst_name
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
        self.dft_LatencyTime = 0
        self.LatencyTime = []
        self.dft_ExposureTime = 0
        self.ExposureTime = []
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FileSuffix = ""
        self.FileSuffix = []
        self.dft_FileDir = ""
        self.FileDir = []
        self.dft_SavingMode = ""
        self.SavingMode = []
        self.dft_LastImageReady = ""
        self.LastImageReady = []
        self.dft_NbFrames = 0
        self.NbFrames = []
        self.dft_TriggerMode = 0
        self.TriggerMode = []
        self.dft_Reset = 0
        self.Reset = []
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In AddDevice method for index",ind
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.LatencyTime.append(self.dft_LatencyTime)
        self.ExposureTime.append(self.dft_ExposureTime)
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FileSuffix.append(self.dft_FileSuffix)
        self.FileDir.append(self.dft_FileDir)
        self.SavingMode.append(self.dft_SavingMode)
        self.LastImageReady.append(self.dft_LastImageReady)
        self.NbFrames.append(self.dft_NbFrames)
        self.TriggerMode.append(self.dft_TriggerMode)
        self.Reset.append(self.dft_Reset)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].read_attribute("acq_status")
            if sta == "Ready":
                tup = (PyTango.DevState.ON,"Camera ready")
            elif sta == "Running":
                tup = (PyTango.DevState.MOVING,"Camera taking images")
            elif sta == "Fault":
                tup = (PyTango.DevState.FAULT,"Camera in FAULT state")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In ReadOne method for index",ind
        #The LimaCCD return an Image in type encoded
        tmp_value = 0.0
        if self.device_available[ind-1] == 1:
            return tmp_value

    def PreStartAll(self):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In PreStartAll method"
        pass

    def PreStartOne(self,ind):
        self.proxy[ind-1].command_inout("prepareAcq")
        return True
		
    def StartOne(self,ind):
        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In StartOne method for index",ind
        self.proxy[ind-1].command_inout("startAcq")
        
    def AbortOne(self,ind):
        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In AbortOne method for index",ind
        self.proxy[ind-1].command_inout("stopAcq")
 
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if name == "LatencyTime":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("latency_time").value
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("acq_expo_time").value
        if name == "FilePrefix":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("saving_prefix").value
        if name == "FileSuffix":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("saving_suffix").value
        if name == "FileDir":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("saving_directory").value
        if name == "SavingMode":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("saving_mode").value
        if name == "LastImageReady":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("last_image_ready").value
        if name == "NbFrames":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("acq_nb_frames").value
        if name == "TriggerMode":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("acq_trigger_mode").value
        if name == "CameraType":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("camera_type").value
        if name == "Reset":
            if self.device_available[ind-1]:
                return 0

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        if name == "LatencyTime":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("latency_time",value)
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("acq_expo_time",value)
        if name == "FilePrefix":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("saving_prefix",value)
        if name == "FileSuffix":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("saving_suffix",value)
        if name == "FileDir":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("saving_directory",value)
        if name == "SavingMode":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("saving_mode",value)
        if name == "LastImageReady":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("last_image_ready",value)
        if name == "NbFrames":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("acq_nb_frames",value)
        if name == "TriggerMode":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("acq_trigger_mode",value)
        if name == "Reset":
            if self.device_available[ind-1]:
                self.proxy[ind-1].command_inout("Reset")
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> LimaCCDCtrl/",self.inst_name,": dying"

        
if __name__ == "__main__":
    obj = TwoDController('test')
