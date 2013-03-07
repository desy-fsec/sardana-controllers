import PyTango
from sardana.pool.controller import OneDController
import time, os

debugFlag = True

class HasyOneDCtrl(OneDController):
    "This class is the Tango Sardana One D controller for Hasylab"

    ctrl_extra_attributes = {'DataLength':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
                             'TangoDevice':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_ONLY'},
                             }
                 
    class_prop = {'RootDeviceName':{'Type':'PyTango.DevString','Description':'The root name of the MCA Tango devices'}}
                 
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        OneDController.__init__(self,inst,props, *args, **kwargs)
        self.debugFlag = False
        if os.isatty(1): 
            self.debugFlag = True
        if self.debugFlag: print "HasyOneDCtrl.__init__, inst ",self.inst_name,"RootDeviceName",self.RootDeviceName
        self.ct_name = "HasyOneDCtrl/" + self.inst_name
        self.db = PyTango.Database()
        name_dev_ask =  self.RootDeviceName + "*"
        self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.flagIsMCA8715 = []
        self.device_available = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.flagIsMCA8715.append( False)
            self.device_available.append(False)
            self.max_device =  self.max_device + 1
        self.started = False
        self.dft_DataLength = 0
        self.DataLength = []

        
    def AddDevice(self,ind):
        OneDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "HasyOneDCtrl: False index %d max %d" % (ind, self.max_device)
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = True
        self.DataLength.append(self.dft_DataLength)
        if hasattr(self.proxy[ind-1], 'BankId'):
            self.flagIsMCA8715[ind-1] = True
        if self.debugFlag: print "HasyOneDCtrl.AddDevice ",self.inst_name,"index",ind, "isMCA8715", self.flagIsMCA8715[ind-1]

       
    def DeleteDevice(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.DeleteDevice",self.inst_name,"index",ind
        OneDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
        
    def StateOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.StatOne",self.inst_name,"index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"The MCA is ready")
        else:
            sta = PyTango.DevState.FAULT
            tup = (sta, "Device not available")

        return tup
    
    def LoadOne(self, axis, value):
        if self.debugFlag: print "HasyOneDCtrl.LoadOne",self.inst_name,"axis", axis
        idx = axis - 1
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        

    def PreReadAll(self):
        if self.debugFlag: print "HasyOneDCtrl.PreReadAll",self.inst_name
        pass

    def PreReadOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.PreReadOne",self.inst_name,"index",ind
        if self.proxy[ind-1].state() != PyTango.DevState.ON:
            self.proxy[ind-1].command_inout("Stop")
        self.proxy[ind-1].command_inout("Read")

    def ReadAll(self):
        if self.debugFlag: print "HasyOneDCtrl.ReadAll",self.inst_name
        pass

    def ReadOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.ReadOne",self.inst_name,"index",ind
        data = self.proxy[ind-1].Data
        return data

    def PreStartAll(self):
        if self.debugFlag: print "HasyOneDCtrl.PreStartAll",self.inst_name
        pass

    def PreStartOne(self,ind, value):
        return True
        
    def StartOne(self,ind, value):
        if self.debugFlag: print "HasyOneDCtrl.StartOne",self.inst_name,"index",ind
        if self.flagIsMCA8715[ind-1]:
            self.proxy[ind-1].BankId = 0
        if self.proxy[ind-1].state() != PyTango.DevState.ON:
            self.proxy[ind-1].command_inout("Stop")
        self.proxy[ind-1].command_inout("Clear")
        self.proxy[ind-1].command_inout("Start")
        
    def AbortOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.AbortOne",self.inst_name,"index",ind
        self.proxy[ind-1].command_inout("Stop")
       
    def GetPar(self, ind, par_name):
        if self.debugFlag: print "HasyOneDCtrl.GetPar",self.inst_name,"index",ind, "par_name", par_name

    def SetPar(self,ind,par_name,value):
        pass
    
    def GetExtraAttributePar(self,ind,name):
        if self.debugFlag: print "HasyOneDCtrl.GetExtraAttrPar",self.inst_name,"index",ind, "name", name
        if name == "TangoDevice":
            if self.device_available[ind-1]:
                return self.proxy[ind-1].name()
        elif name == "DataLength": 
            if self.device_available[ind-1]:
                return int(self.proxy[ind-1].read_attribute("DataLength").value)

    def SetExtraAttributePar(self,ind,name,value):
        if self.debugFlag: print "HasyOneDCtrl.SetExtraAttributePar",self.inst_name,"index",ind," name=",name," value=",value
        if par_name == "DataLength":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("DataLength",value)
        pass

    def SendToCtrl(self,in_data):
#        if self.debugFlag: print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        if self.debugFlag: print "HasyOneDCtrl/",self.inst_name,": Aarrrrrg, I am dying"

        
if __name__ == "__main__":
    obj = OneDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
