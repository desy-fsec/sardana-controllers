import PyTango
import time, os

from sardana import State, DataAccess
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

class TangoVimbaCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the TangoVimba"


    ctrl_extra_attributes = {
                             'AcquisitionType':{Type:'PyTango.DevLong',Access:ReadWrite,Description:'0-> StartAcquisition (hw trigger), 1-> StartSingleAcquisition (sw trigger)'},
                             'TangoDevice':{Type:'PyTango.DevString',Access:ReadOnly}
                             }
			     
    class_prop = {'RootDeviceName':{Type:str,Description:'The root name of the TangoVimba Tango devices'},
                  'TangoHost':{Type:str,Description:'The tango host where searching the devices'},}
			     
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        self.TangoHost = None
        TwoDController.__init__(self,inst,props, *args, **kwargs)
        print("PYTHON -> TwoDController ctor for instance",inst)

        self.ct_name = "TangoVimbaCtrl/" + self.inst_name
        if self.TangoHost == None:
            self.db = PyTango.Database()
        else:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find( ':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int( lst[1])                           
            self.db = PyTango.Database(self.node, self.port)
        name_dev_ask =  self.RootDeviceName + "*"
	self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.device_available = []
        self.start_time = []
        self.acq_type = []
        self.exp_time = 0
	for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.start_time.append(time.time())
            self.acq_type.append(0)
            self.max_device =  self.max_device + 1
        self.started = False
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In AddDevice method for index",ind
        TwoDController.AddDevice(self,ind)
        if ind > self.max_device:
            print("False index")
            return
        proxy_name = self.tango_device[ind-1]
        if self.TangoHost == None:
            proxy_name = self.tango_device[ind-1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + str(self.tango_device[ind-1])
        self.proxy[ind-1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind-1] = 1
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        TwoDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In StateOne method for index",ind
        if  self.device_available[ind-1] == 1:
            if time.time() - self.start_time[ind-1] > self.exp_time and self.started == True:
                try:
                    self.proxy[ind-1].command_inout("StopAcquisition")
                    self.started = False
                except:
                    pass
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"Camera ready")
            elif sta == PyTango.DevState.RUNNING:
                sta = PyTango.DevState.MOVING
                tup = (sta,"Camera taking images")
            elif sta == PyTango.DevState.FAULT:
                tup = (sta,"Camera in FAULT state")
            elif sta == PyTango.DevState.ALARM:
                sta = PyTango.DevState.FAULT
                tup = (sta,"Device in ALARM state")
            return tup

    def PreReadAll(self):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In PreReadOne method for index",ind
        try:
            self.proxy[ind-1].command_inout("StopAcquisition")
        except:
            pass
        
    def ReadAll(self):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In ReadOne method for index",ind
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind-1] == 1:
            return tmp_value

    def PreStartAll(self):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In PreStartAll method"
        pass
		
    def StartOne(self,ind, position=None):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In StartOne method for index",ind
        self.proxy[ind-1].FileSaving = True
        if self.acq_type[ind-1] == 0:
            self.proxy[ind-1].command_inout("StartAcquisition")
        else:
            self.proxy[ind-1].command_inout("StartSingleAcquisition")
            
        self.started = True
        self.start_time[ind-1] = time.time()
        
        
    def AbortOne(self,ind):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In AbortOne method for index",ind
        try:
            self.proxy[ind-1].command_inout("StopAcquisition")
        except:
            pass

    def LoadOne(self, ind, value):
        self.exp_time = value
        

    def GetAxisPar(self, ind, par_name):
        if par_name == "data_source":
            data_source = "Not set"
            return data_source
 
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if self.device_available[ind-1]:
            if name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + self.proxy[ind-1].name() 
                return tango_device
            if name == "AcquisitionType":
                return self.acq_type[ind-1]

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> TangoVimbaCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        if self.device_available[ind-1]:
            if name == "AcquisitionType":
                self.acq_type[ind-1] = value
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print("PYTHON -> TangoVimbaCtrl/",self.inst_name,": dying")

        
if __name__ == "__main__":
    obj = TwoDController('test')
