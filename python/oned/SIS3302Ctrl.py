
import time, os

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import OneDController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class SIS3302Ctrl(OneDController):
    "This class is the Tango Sardana One D controller for Hasylab"

    ctrl_extra_attributes = {'DataLength':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'TangoDevice':{Type:'PyTango.DevString',Access:ReadOnly},     
                         }
    
    class_prop = {'RootDeviceName':{Type:'PyTango.DevString',Description:'The root name of the MCA Tango devices'},
                  'TangoHost':{Type:str,Description:'The tango host where searching the devices'}, }
    
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        self.TangoHost = None
        OneDController.__init__(self,inst,props, *args, **kwargs)
        if self.TangoHost != None:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find(':') != -1:
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int( lst[1])
        self.proxy_name = self.RootDeviceName
        if self.TangoHost != None:
            self.proxy_name = str(self.node) + (":%s/" % self.port) + str(self.proxy_name)
        self.proxy = PyTango.DeviceProxy(self.proxy_name)
        self.started = False
        self.acqTime = 0
        self.acqStartTime = None
        
    def AddDevice(self,ind):
        OneDController.AddDevice(self,ind)

       
    def DeleteDevice(self,ind):
        #print "SIS3302Ctrl.DeleteDevice",self.inst_name,"index",ind
        OneDController.DeleteDevice(self,ind)
        
        
    def StateOne(self,ind):
        #print "SIS3302Ctrl.StatOne",self.inst_name,"index",ind
        if self.acqStartTime != None: #acquisition was started, equivalent to self.started == True
            now = time.time()
            elapsedTime = now - self.acqStartTime - 0.2
            if elapsedTime < self.acqTime: #acquisition has probably not finished yet
                self.sta = State.Moving
                self.status = "Acqusition time has not elapsed yet."
            else:
                self.proxy.command_inout("Stop")
                self.started = False
                self.acqStartTime = None
                self.sta = PyTango.DevState.ON
                self.status = "Device is ON"
        else:
            self.sta = PyTango.DevState.ON
            self.status = "Device is ON"
        tup = (self.sta, self.status)
        return tup
    
    def LoadOne(self, axis, value):
        #print "SIS3302Ctrl.LoadOne",self.inst_name,"axis", axis
        idx = axis - 1
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        self.acqTime = value
        

    def PreReadAll(self):
        #print "SIS3302Ctrl.PreReadAll",self.inst_name
        pass
        
    def PreReadOne(self,ind):
        #print "SIS3302Ctrl.PreReadOne",self.inst_name,"index",ind
        pass

    def ReadAll(self):
        #while(self.proxy.command_inout("State") != PyTango.DevState.ON):
        #    sleep(0.1)
        self.counts = self.proxy.read_attribute("Count").value

    def ReadOne(self,ind):
        #print "SIS3302Ctrl.ReadOne",self.inst_name,"index",ind
        if ind == 1:            
            data = self.proxy.Data
        else:
            data = [self.counts[ind - 2]]
        return data

    def PreStartAll(self):
        pass

    def PreStartOne(self,ind, value):
        return True
        
    def StartAll(self):
        if self.started == False: # equivalent to self.acqStartTime == None
            self.proxy.command_inout("Stop")
            self.proxy.command_inout("Clear")
            self.proxy.command_inout("Start")
            self.started = True
            self.acqStartTime = time.time()
        
    def StartOne(self,ind, value):
        pass
            
    def AbortOne(self,ind):
        #print "SIS3302Ctrl.AbortOne",self.inst_name,"index",ind
        self.proxy.command_inout("Stop")
        self.proxy.command_inout("Read")

       
    def GetPar(self, ind, par_name):
        #print "SIS3302Ctrl.GetPar",self.inst_name,"index",ind, "par_name", par_name
        pass
        
    def SetPar(self,ind,par_name,value):
        pass
    
    def GetExtraAttributePar(self,ind,name):
        #print "SIS3302Ctrl.GetExtraAttrPar",self.inst_name,"index",ind, "name", name
        if name == "TangoDevice": 
            return self.proxy_name
        elif name == "DataLength":
            if ind == 1:
                datalength = int(self.proxy.read_attribute("DataLength").value)
            else:
                datalength = 1
                return datalength

    def SetExtraAttributePar(self,ind,name,value):
        #print "SIS3302Ctrl.SetExtraAttributePar",self.inst_name,"index",ind," name=",name," value=",value
        if name == "DataLength":
            if ind == 1:
                self.proxy.write_attribute("DataLength",value)
                
    def SendToCtrl(self,in_data):
        #print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        #print "SIS3302Ctrl/",self.inst_name,": Aarrrrrg, I am dying"
        pass
        
if __name__ == "__main__":
    obj = OneDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
