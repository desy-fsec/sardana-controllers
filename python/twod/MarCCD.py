import PyTango
import time, os

from sardana import State, DataAccess
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

class MarCCDCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the MarCCD"


    ctrl_extra_attributes = {'FilePrefix':{Type:'PyTango.DevString',Access:ReadWrite},
                             'FilePostfix':{Type:'PyTango.DevString',Access:ReadWrite},
			     'FileDir':{Type:'PyTango.DevString',Access:ReadWrite},
			     'ReadMode':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'TangoDevice':{Type:'PyTango.DevString',Access:ReadOnly}
                             }
			     
    class_prop = {'RootDeviceName':{Type:str,Description:'The root name of the MarCCD Tango devices'},
                  'TangoHost':{Type:str,Description:'The tango host where searching the devices'},}
			     
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        self.TangoHost = None
        TwoDController.__init__(self,inst,props, *args, **kwargs)
        print "PYTHON -> TwoDController ctor for instance",inst

        self.ct_name = "MarCCDCtrl/" + self.inst_name
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
	for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.max_device =  self.max_device + 1
        self.started = False
        self.dft_FilePrefix = ""
        self.FilePrefix = []
        self.dft_FilePostfix = ""
        self.FilePostfix = []
        self.dft_FileDir = ""
        self.FileDir = []
        self.dft_ReadMode = 0
        self.ReadMode = []
        
        
    def AddDevice(self,ind):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In AddDevice method for index",ind
        TwoDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.FilePrefix.append(self.dft_FilePrefix)
        self.FilePostfix.append(self.dft_FilePostfix)
        self.FileDir.append(self.dft_FileDir)
        self.ReadMode.append(self.dft_ReadMode)
        
    def DeleteDevice(self,ind):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In DeleteDevice method for index",ind
        TwoDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In StateOne method for index",ind
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
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,ind):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In ReadOne method for index",ind
        #The MarCCD return an Image in type encoded
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind-1] == 1:
            return tmp_value

    def PreStartAll(self):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In PreStartAll method"
        pass
		
    def StartOne(self,ind, position=None):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In StartOne method for index",ind
        self.proxy[ind-1].command_inout("StartExposing")
        
    def AbortOne(self,ind):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In AbortOne method for index",ind
        self.proxy[ind-1].command_inout("StopExposing")

    def LoadOne(self, ind, value):
        pass

    def GetAxisPar(self, ind, par_name):
        if par_name == "data_source":
            data_source = "Not set"
            return data_source
 
    def GetExtraAttributePar(self,ind,name):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In GetExtraFeaturePar method for index",ind," name=",name
        if self.device_available[ind-1]:
            if name == "FilePrefix":
                return self.proxy[ind-1].read_attribute("SavingPrefix").value
            elif name == "FilePostfix":
                return self.proxy[ind-1].read_attribute("SavingPostfix").value
            elif name == "FileDir":
                return self.proxy[ind-1].read_attribute("SavingDirectory").value
            elif name == "ReadMode":
                return self.proxy[ind-1].read_attribute("ReadMode").value
            elif name == "TangoDevice":
                return str(self.proxy[ind-1].name())

    def SetExtraAttributePar(self,ind,name,value):
#        print "PYTHON -> MarCCDCtrl/",self.inst_name,": In SetExtraFeaturePar method for index",ind," name=",name," value=",value
        if self.device_available[ind-1]:
            if name == "FilePrefix":
                self.proxy[ind-1].write_attribute("SavingPrefix",value)
            elif name == "FilePostfix":
                self.proxy[ind-1].write_attribute("SavingPostfix",value)
            elif name == "FileDir":
                self.proxy[ind-1].write_attribute("SavingDirectory",value)
            elif name == "ReadMode":
                self.proxy[ind-1].write_attribute("ReadMode",value)
        
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        print "PYTHON -> MarCCDCtrl/",self.inst_name,": dying"

        
if __name__ == "__main__":
    obj = TwoDController('test')
