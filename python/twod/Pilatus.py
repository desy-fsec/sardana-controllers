import PyTango
from sardana.pool.controller import TwoDController
import time

class PilatusCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the Pilatus"


    ctrl_extra_attributes = {'DelayTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'ExposureTime':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'ExposurePeriod':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'FileStartNum':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'FilePrefix':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'FilePostfix':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'FileDir':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'LastImageTaken':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
			     'NbFrames':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'NbExposures':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'ShutterEnable':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
			     'TriggerMode':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'Threshold':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
			     'Gain':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
                             'TangoDevice':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_ONLY'}
                             }
			     
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the Pilatus Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        TwoDController.__init__(self,inst,props, *args, **kwargs)
        print "PYTHON -> TwoDController ctor for instance",inst

        self.ct_name = "PilatusCtrl/" + self.inst_name
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
        self.dft_DelayTime = 0
        self.DelayTime = []
        self.dft_ExposureTime = 0
        self.ExposureTime = []
        self.dft_ExposurePeriod = 0
        self.ExposurePeriod = []
        self.dft_FileStartNum = 0
        self.FileStartNum = []
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FilePostfix = ""
        self.FilePostfix = []
        self.dft_FileDir = ""
        self.FileDir = []
        self.dft_LastImageTaken = ""
        self.LastImageTaken = []
        self.dft_NbFrames = 0
        self.NbFrames = []
        self.dft_NbExposures = 0
        self.NbExposures = []
        self.dft_ShutterEnable = 0
        self.ShutterEnable = []
        self.dft_TriggerMode = 0
        self.TriggerMode = []
        self.dft_Threshold = 0
        self.Threshold = []
        self.dft_Gain = 0
        self.Gain = []
        self.dft_Reset = 0
        self.Reset = []
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In AddDevice method for index",ind
        TwoDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.DelayTime.append(self.dft_DelayTime)
        self.ExposureTime.append(self.dft_ExposureTime)
        self.ExposurePeriod.append(self.dft_ExposurePeriod)
        self.FileStartNum.append(self.dft_FileStartNum)
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FilePostfix.append(self.dft_FilePostfix)
        self.FileDir.append(self.dft_FileDir)
        self.LastImageTaken.append(self.dft_LastImageTaken)
        self.NbFrames.append(self.dft_NbFrames)
        self.NbExposures.append(self.dft_NbExposures)
        self.ShutterEnable.append(self.dft_ShutterEnable)
        self.TriggerMode.append(self.dft_TriggerMode)
        self.Threshold.append(self.dft_Threshold)
        self.Gain.append(self.dft_Gain)
        self.Reset.append(self.dft_Reset)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        TwoDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"Camera ready")
            elif sta == PyTango.DevState.RUNNING:
                sta = PyTango.DevState.MOVING
                tup = (sta,"Camera taking images")
            elif sta == PyTango.DevState.FAULT:
                tup = (sta,"Camera in FAULT state")
            elif sta == PyTango.DevState.DISABLE:
                sta = PyTango.DevState.FAULT
                tup = (sta,"Device disconnected from camserver")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In ReadOne method for index",ind
        #The Pilatus return an Image in type encoded
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind-1] == 1:
            return tmp_value

    def PreStartAll(self):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In PreStartAll method"
        pass
		
    def StartOne(self,ind, position=None):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In StartOne method for index",ind
        self.proxy[ind-1].command_inout("StartStandardAcq")
        
    def AbortOne(self,ind):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In AbortOne method for index",ind
        self.proxy[ind-1].command_inout("StopAcq")

    def LoadOne(self, ind, value):
        self.proxy[ind-1].write_attribute("ExposureTime",value)

    def GetAxisPar(self, ind, par_name):
        if par_name == "data_source":
            data_source = str(self.tango_device[ind -1]) + "/LastImageTaken"
            return data_source
 
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if self.device_available[ind-1]:
            if name == "DelayTime":
                return self.proxy[ind-1].read_attribute("DelayTime").value
            elif name == "ExposureTime":
                return self.proxy[ind-1].read_attribute("ExposureTime").value
            elif name == "ExposurePeriod":
                return self.proxy[ind-1].read_attribute("ExposurePeriod").value
            elif name == "FileStartNum":
                return self.proxy[ind-1].read_attribute("FileStartNum").value
            elif name == "FilePrefix":
                return self.proxy[ind-1].read_attribute("FilePrefix").value
            elif name == "FilePostfix":
                return self.proxy[ind-1].read_attribute("FilePostfix").value
            elif name == "FileDir":
                return self.proxy[ind-1].read_attribute("FileDir").value
            elif name == "LastImageTaken":
                return self.proxy[ind-1].read_attribute("LastImageTaken").value
            elif name == "NbFrames":
                return self.proxy[ind-1].read_attribute("NbFrames").value
            elif name == "NbExposures":
                return self.proxy[ind-1].read_attribute("NbExposures").value
            elif name == "TriggerMode":
                return self.proxy[ind-1].read_attribute("TriggerMode").value
            elif name == "Threshold":
                return self.proxy[ind-1].read_attribute("Threshold").value
            elif name == "Gain":
                return self.proxy[ind-1].read_attribute("Gain").value
            elif name == "TangoDevice":
                return str(self.proxy[ind-1].name())

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> PilatusCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        if self.device_available[ind-1]:
            if name == "DelayTime":
                self.proxy[ind-1].write_attribute("DelayTime",value)
            elif name == "ExposureTime":
                self.proxy[ind-1].write_attribute("ExposureTime",value)
            elif name == "ExposurePeriod":
                self.proxy[ind-1].write_attribute("ExposurePeriod",value)
            elif name == "FileStartNum":
                self.proxy[ind-1].write_attribute("FileStartNum",value)
            elif name == "FilePrefix":
                self.proxy[ind-1].write_attribute("FilePrefix",value)
            elif name == "FilePostfix":
                self.proxy[ind-1].write_attribute("FilePostfix",value)
            elif name == "FileDir":
                self.proxy[ind-1].write_attribute("FileDir",value)
            elif name == "LastImageTaken":
                self.proxy[ind-1].write_attribute("LastImageTaken",value)
            elif name == "NbFrames":
                self.proxy[ind-1].write_attribute("NbFrames",value)
            elif name == "NbExposures":
                self.proxy[ind-1].write_attribute("NbExposures",value)
            elif name == "ShutterEnable":
                self.proxy[ind-1].write_attribute("ShutterEnable",value)
            elif name == "TriggerMode":
                self.proxy[ind-1].write_attribute("TriggerMode",value)
            elif name == "Threshold":
                self.proxy[ind-1].write_attribute("Threshold",value)
            elif name == "Gain":
                self.proxy[ind-1].write_attribute("Gain",value)
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> PilatusCtrl/",self.inst_name,": dying"

        
if __name__ == "__main__":
    obj = TwoDController('test')
