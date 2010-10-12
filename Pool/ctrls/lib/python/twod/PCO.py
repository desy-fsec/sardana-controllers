import PyTango
from pool import TwoDController
import time

class PCOController(TwoDController):
    "This class is the Tango Sardana Zero D controller for the PCO"

    ctrl_extra_attributes = {'DelayTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'ExposureTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
			     'ADCs':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'FileStartNum':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'FilePrefix':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'FileDir':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'}}

			     
    class_prop = {'RootDevName':{'Type':'PyTango.DevString','Description':'The root name of the PCO Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props):
        TwoDController.__init__(self,inst,props)
        print "PYTHON -> TwoDController ctor for instance",inst

        self.ct_name = "PCOCtrl/" + self.inst_name
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
        self.dft_DelayTime = 0
        self.DelayTime = []
        self.dft_ExposureTime = 0
        self.ExposureTime = []
        self.dft_ADCs = 0
        self.ADCs = []
        self.dft_FileStartNum = 0
        self.FileStartNum = []
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FileDir = ""
        self.FileDir = []
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In AddDevice method for index",ind
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.DelayTime.append(self.dft_DelayTime)
        self.ExposureTime.append(self.dft_ExposureTime)
        self.ADCs.append(self.dft_ADCs)
        self.FileStartNum.append(self.dft_FileStartNum)
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FileDir.append(self.dft_FileDir)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"Camera ready")
            elif sta == PyTango.DevState.RUNNING:
                sta = PyTango.DevState.MOVING
                tup = (sta,"Camera taking images")
            elif stat == PyTango.DevState.FAULT:
                tup = (sta,"Camera in FAULT state")
            elif stat == PyTango.DevState.UNKNOWN:
                sta = PyTango.DevState.FAULT
                tup = (sta,"Camera in UNKNOWN state")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
        #print "PYTHON -> PCOCtrl/",self.inst_name,": In ReadOne method for index",ind
        #The PCO return an Image in type encoded
        tmp_value = 0.0
        if self.device_available[ind-1] == 1:
            return tmp_value

    def PreStartAll(self):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In PreStartAllCT method"
        pass

    def PreStartOne(self,ind):
        return True
		
    def StartOne(self,ind):
        #print "PYTHON -> PCOCtrl/",self.inst_name,": In StartOneCT method for index",ind
        self.proxy[ind-1].command_inout("StartAcquisition")
       
    def GetPar(self, ind, par_name):       
        if par_name == "XDim":
            return int(self.proxy[ind-1].read_attribute("Width").value)
        elif par_name == "YDim":
            return int(self.proxy[ind-1].read_attribute("Heigth").value)
	
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if name == "DelayTime":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("DelayTime").value
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("ExposureTime").value
        if name == "ADCs":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("ADCs").value
        if name == "FileStartNum":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("FileStartNum").value
        if name == "FilePrefix":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("FilePrefix").value
        if name == "FileDir":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].read_attribute("FileDir").value

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> PCOCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        if name == "DelayTime":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("DelayTime",value)
        if name == "ExposureTime":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("ExposureTime",value)
        if name == "ADCs":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("ADCs",value)
        if name == "FileStartNum":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("FileStartNum",value)
        if name == "FilePrefix":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("FilePrefix",value)
        if name == "FileDir":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("FileDir",value)
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> PCOCtrl/",self.inst_name,": Aarrrrrg, I am dying"

        
if __name__ == "__main__":
    obj = TwoDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
