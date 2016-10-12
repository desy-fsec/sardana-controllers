import PyTango
from sardana.pool.controller import CounterTimerController
import time

from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


# This controller has to be used with another controller for the sis3302 in the MG
# It only reads the counts.

class SIS3302RoisCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the SIS3302 RoIs"
	

    axis_attributes = {'TangoDevice':{Type:str,Access:ReadOnly},
                       'RoIIndex':{Type:int,Access:ReadWrite},
                       }
		     
    ctrl_properties = {'RootDeviceName':{Type:str,Description:'The root name of the SIS3302Rois Tango devices'},
                       'TangoHost':{Type:str,Description:'The tango host where searching the devices'}, 
                       }

    gender = "CounterTimer"
    model = "SIS3302Rois"
    organization = "DESY"
    state = ""
    status = ""
    
    def __init__(self,inst,props, *args, **kwargs):
        self.TangoHost = None
        CounterTimerController.__init__(self,inst,props, *args, **kwargs)
        if self.TangoHost != None:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find( ':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int( lst[1])
        self.started = False
        self.dft_Offset = 0
        self.Offset = []
        self.RoIIndexes = []
        proxy_name = self.RootDeviceName
        if self.TangoHost != None:
            proxy_name = str(self.node) + (":%s/" % self.port) + str(proxy_name)
        self.proxy = PyTango.DeviceProxy(proxy_name)

    def AddDevice(self,ind):
        CounterTimerController.AddDevice(self,ind)
        self.Offset.append(self.dft_Offset)
        self.RoIIndexes.append(-1)
        
    def DeleteDevice(self,ind):
        CounterTimerController.DeleteDevice(self,ind)
        self.proxy =  None
        
		
    def StateOne(self,ind):
        sta = self.proxy.command_inout("State")
        if sta == PyTango.DevState.ON:
            status_string = "MCA is in ON state"
        elif sta == PyTango.DevState.MOVING:
            sta = PyTango.DevState.MOVING
            status_string = "MCA is busy"
        elif sta == PyTango.DevState.OFF:
            sta = PyTango.DevState.FAULT
            status_string = "Error detected" 
        tup = (sta, status_string)
        return tup

    def PreReadAll(self):
        pass
        

    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        self.counts = self.proxy.read_attribute("Count").value

    def PreStartOne(self,ind,pos):
        return True
        
    def StartOneCT(self,ind):
        return True
            
    def ReadOne(self,ind):
        value = self.counts[self.RoIIndexes[ind-1]-1]
        return  value
	
    def AbortOne(self,ind):
        pass
        
    def PreStartAllCT(self):
        self.wantedCT = []

    def PreStartOneCT(self,ind):
        pass
	
    def StartAllCT(self):
        pass
		     	
    def LoadOne(self,ind,value):
        self.proxy.write_attribute("ExposureTime", value)
	
    def GetExtraAttributePar(self,ind,name):
        if name == "TangoDevice":
            tango_device = self.node + ":" + str(self.port) + "/" + self.proxy.name() 
            return tango_device
        if name == "RoIIndex":
            return self.RoIIndexes[ind-1]
        
            
    def SetExtraAttributePar(self,ind,name,value):
        if name == "RoIIndex":
            self.RoIIndexes[ind-1] = value
			
    def SendToCtrl(self,in_data):
        return "Nothing sent"

    def __del__(self):
        print "PYTHON -> SIS3302RoisCtrl/",self.inst_name,": dying"

