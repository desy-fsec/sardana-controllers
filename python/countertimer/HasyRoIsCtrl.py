
import time, os

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

global last_sta

start_one = 0

class HasyRoIsCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for making RoIs from OneD"

    ctrl_extra_attributes = {'DataLength':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'TangoDevice':{Type:'PyTango.DevString',Access:ReadOnly},
                             'RoIStart':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'RoIEnd':{Type:'PyTango.DevLong',Access:ReadWrite},                             
                             }
                 
    class_prop = {'RootDeviceName':{Type:'PyTango.DevString',Description:'The root name of the MCA Tango devices'},
                  'TangoHost':{Type:str,Description:'The tango host where searching the devices'}, }
                 
    MaxDevice = 97

    gender = "CounterTimer"
    model = "HasyRoIs"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self,inst,props, *args, **kwargs):
        self.TangoHost = None
        CounterTimerController.__init__(self,inst,props, *args, **kwargs)
        self.debugFlag = False
        if os.isatty(1):
            self.debugFlag = True
        if self.debugFlag: print "HasyRoIsCtrl.__init__, inst ",self.inst_name,"RootDeviceName",self.RootDeviceName
        self.ct_name = "HasyRoIsCtrl/" + self.inst_name

        self.flagIsMCA8715 = False
        self.flagIsXIA = False
        self.flagIsSIS3320 = False

        if self.TangoHost != None:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find( ':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int( lst[1])
        self.RoIs_start = []
        self.RoIs_end = []
        proxy_name = self.RootDeviceName
        if self.TangoHost != None:
            proxy_name = str(self.node) + (":%s/" % self.port) + str(proxy_name)
        self.proxy = PyTango.DeviceProxy(proxy_name) 
        if hasattr(self.proxy, 'BankId'):
            self.flagIsMCA8715 = True
        if hasattr(self.proxy, 'Spectrum') and hasattr(self.proxy, 'McaLength'):
            self.flagIsXIA = True
        if hasattr(self.proxy, 'ADCxInputInvert') or hasattr(self.proxy, 'TriggerPeakingTime'):
            self.flagIsSIS3320 = True

        global last_sta
        last_sta = PyTango.DevState.ON

        
    def AddDevice(self,ind):
        CounterTimerController.AddDevice(self,ind)
        self.RoIs_start.append(0)
        self.RoIs_end.append(0)
       
    def DeleteDevice(self,ind):
        if self.debugFlag: print "HasyRoIsCtrl.DeleteDevice",self.inst_name,"index",ind
        CounterTimerController.DeleteDevice(self,ind)
        self.proxy =  None
        
        
    def StateOne(self,ind):
        global last_sta
        try:
            sta = self.proxy.command_inout("State")
            last_sta = sta
        except:
            sta = last_sta
        if sta == PyTango.DevState.ON:
            tup = (sta,"The MCA is ready")
        elif sta == PyTango.DevState.MOVING or  sta == PyTango.DevState.RUNNING:
            tup = (PyTango.DevState.MOVING,"Device is acquiring data")
        else:
            tup = (sta, "")

        return tup
    
    def LoadOne(self, axis, value):
        if self.debugFlag: print "HasyRoIsCtrl.LoadOne",self.inst_name,"axis", axis
        idx = axis - 1
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        
    def PreReadAll(self):
        pass

    def PreReadOne(self,ind):
        if self.debugFlag: print "HasyRoIsCtrl.PreReadOne",self.inst_name,"index",ind
        if self.flagIsXIA == 0:
            self.proxy.command_inout("Stop")
            self.proxy.command_inout("Read")
        else:
            if self.proxy.command_inout("State") != PyTango.DevState.ON:
                self.proxy.command_inout("Stop")  

    def ReadAll(self):
        if self.debugFlag: print "HasyRoIsCtrl.ReadAll",self.inst_name
        pass

    def ReadOne(self,ind):
        if self.debugFlag: print "HasyRoIsCtrl.ReadOne",self.inst_name,"index",ind
        if self.flagIsXIA:
            data = self.proxy.Spectrum
        else:
            data = self.proxy.Data
        value = 0
        for i in range(self.RoIs_start[ind-1], self.RoIs_end[ind-1] + 1):
            value = value + data[i]
        return value

    def PreStartAll(self):
        pass	

    def StartAllCT(self):
        try:
            sta = self.proxy.command_inout("State")
        except:
            sta = PyTango.DevState.ON
        if self.flagIsMCA8715:
            self.proxy.BankId = 0
        # the state may be ON but one bank can be active
        global start_one
        if sta == PyTango.DevState.ON and start_one == 0:
            self.proxy.command_inout("Stop")
            self.proxy.command_inout("Clear")
            self.proxy.command_inout("Start")
            start_one = 1
        

    def PreStartOne(self,ind, value):
        return True
        
    def StartOne(self,ind, value):
        pass
        
    def AbortOne(self,ind):
        if self.debugFlag: print "HasyRoIsCtrl.AbortOne",self.inst_name,"index",ind
        self.proxy.command_inout("Stop")
        if self.flagIsXIA == 0:
            self.proxy.command_inout("Read")

    def GetPar(self, ind, par_name):
        if self.debugFlag: print "HasyRoIsCtrl.GetPar",self.inst_name,"index",ind, "par_name", par_name

    def SetPar(self,ind,par_name,value):
        pass
    
    def GetExtraAttributePar(self,ind,name):
        if self.debugFlag: print "HasyRoIsCtrl.GetExtraAttrPar",self.inst_name,"index",ind, "name", name
        if name == "TangoDevice":
            tango_device = self.node + ":" + str(self.port) + "/" + self.proxy.name() 
            return tango_device
        elif name == "DataLength":
            if self.flagIsXIA:
                datalength = int(self.proxy.read_attribute("McaLength").value)
            else:
                datalength = int(self.proxy.read_attribute("DataLength").value)
            return datalength
        elif name == "RoIStart":
            return self.RoIs_start[ind-1]
        elif name == "RoIEnd":
            return self.RoIs_end[ind-1]

    def SetExtraAttributePar(self,ind,name,value):
        if self.debugFlag: print "HasyRoIsCtrl.SetExtraAttributePar",self.inst_name,"index",ind," name=",name," value=",value
        if name == "DataLength":
            if self.flagIsXIA:
                self.proxy.write_attribute("McaLength",value)
            else:
                self.proxy.write_attribute("DataLength",value)
        elif name == "RoIStart":
            self.RoIs_start[ind-1] = value
        elif name == "RoIEnd":
            self.RoIs_end[ind-1] = value

    def SendToCtrl(self,in_data):
        return "Nothing sent"
        
    def __del__(self):
        if self.debugFlag: print "HasyRoIsCtrl/",self.inst_name,": dying"

        
if __name__ == "__main__":
    obj = CounterTimerController('test')
