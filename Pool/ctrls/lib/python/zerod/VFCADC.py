import PyTango
from pool import ZeroDController
import time

class VFCADCController(ZeroDController):
    "This class is the Tango Sardana Zero D controller for the VFCADC"

    ctrl_extra_attributes = {'Gain':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'Offset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
			     'Polarity':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ'}}

			     
    class_prop = {'RootDevName':{'Type':'PyTango.DevString','Description':'The root name of the VFCADC Tango devices'}}
			     
    MaxDevice = 97

    def __init__(self,inst,props):
        ZeroDController.__init__(self,inst,props)
#        print "PYTHON -> ZeroDController ctor for instance",inst

        self.ct_name = "VFCADCCtrl/" + self.inst_name
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
        self.dft_Gain = 0
        self.Gain = []
        self.dft_Polarity = 0
        self.Polarity = []
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In AddDevice method for index",ind
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.Offset.append(self.dft_Offset)
        self.Gain.append(self.dft_Gain)
        self.Polarity.append(self.dft_Polarity)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            tup = (sta,"Status error string from controller")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In ReadOne method for index",ind
        if self.device_available[ind-1] == 1:
            return self.proxy[ind-1].read_attribute("Value").value

    def PreStartAllCT(self):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In PreStartAllCT method"
        self.wantedCT = []

    def PreStartOneCT(self,ind):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].command_inout("Reset")
            return True
        else:
            raise RuntimeError,"Ctrl Tango's proxy null!!!"
            return False
		
    def StartOneCT(self,ind):
        #print "PYTHON -> VFCADCCtrl/",self.inst_name,": In StartOneCT method for index",ind
        self.wantedCT.append(ind)
	
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if name == "Offset":
            if self.device_available[ind-1]:
                return float(self.proxy[ind-1].read_attribute("Offset").value)
        if name == "Gain":
            if self.device_available[ind-1]:
                return float(self.proxy[ind-1].read_attribute("Gain").value)
        if name == "Polarity":
            if self.device_available[ind-1]:
                return float(self.proxy[ind-1].read_attribute("Polarity").value)

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> VFCADCCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        if name == "Offset":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Offset",value)
                self.proxy[ind-1].command_inout("SetOffset")
        if name == "Gain":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Gain",value)
                self.proxy[ind-1].command_inout("SetGain")
        if name == "Polarity":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Polarity",value)
                self.proxy[ind-1].command_inout("SetPolarity")
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> VFCADCCtrl/",self.inst_name,": Aarrrrrg, I am dying"

        
if __name__ == "__main__":
    obj = ZeroDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
