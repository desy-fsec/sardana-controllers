
import time, os

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import OneDController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class HasyOneDCtrl(OneDController):
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
        self.debugFlag = False
        if os.isatty(1):
            self.debugFlag = True
        if self.debugFlag: print "HasyOneDCtrl.__init__, inst ",self.inst_name,"RootDeviceName",self.RootDeviceName
        self.ct_name = "HasyOneDCtrl/" + self.inst_name
        if self.TangoHost == None:
            self.db = PyTango.Database()
        else:
            #
            # TangoHost can be hasgksspp07eh3:10000
            #
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
        self.flagIsMCA8715 = []
        self.flagIsXIA = []
        self.flagIsSIS3320 = []
        self.device_available = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.flagIsMCA8715.append( False)
            self.flagIsXIA.append( False)
            self.flagIsSIS3320.append(False)
            self.device_available.append(False)
            self.max_device =  self.max_device + 1
        self.started = False

        
    def AddDevice(self,ind):
        OneDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "HasyOneDCtrl: False index %d max %d" % (ind, self.max_device)
            return
        proxy_name = self.tango_device[ind-1]
        if self.TangoHost == None:
            proxy_name = self.tango_device[ind-1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + str(self.tango_device[ind-1])
        self.proxy[ind-1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind-1] = True
        if hasattr(self.proxy[ind-1], 'BankId'):
            self.flagIsMCA8715[ind-1] = True
        if hasattr(self.proxy[ind-1], 'Spectrum') and hasattr(self.proxy[ind-1], 'McaLength'):
            self.flagIsXIA[ind-1] = True
        if hasattr(self.proxy[ind-1], 'ADCxInputInvert') or hasattr(self.proxy[ind-1], 'TriggerPeakingTime'):
            self.flagIsSIS3320[ind-1] = True
        if self.debugFlag: print "HasyOneDCtrl.AddDevice ",self.inst_name,"index",ind, "isMCA8715", self.flagIsMCA8715[ind-1], "isXIA", self.flagIsXIA[ind-1]

       
    def DeleteDevice(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.DeleteDevice",self.inst_name,"index",ind
        OneDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
        
    def StateOne(self,ind):
        #if self.debugFlag: print "HasyOneDCtrl.StatOne",self.inst_name,"index",ind
        if  self.device_available[ind-1] == 1: 
            sta = self.proxy[ind-1].command_inout("State")
            if self.flagIsSIS3320[ind-1]:
                if sta == PyTango.DevState.ON:
                    tup = (sta,"The MCA is ready")
                elif sta == PyTango.DevState.MOVING or  sta == PyTango.DevState.RUNNING:
                    tup = (PyTango.DevState.ON,"Device is acquiring data")
                else:
                    tup = (sta, "")
            else:
                if sta == PyTango.DevState.ON:
                    tup = (sta,"The MCA is ready")
                elif sta == PyTango.DevState.MOVING or  sta == PyTango.DevState.RUNNING:
                    tup = (sta,"Device is acquiring data")
                else:
                    tup = (sta, "")
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
        if self.flagIsXIA[ind-1] == 0:
            self.proxy[ind-1].command_inout("Stop")
            self.proxy[ind-1].command_inout("Read")
        else:
            if self.proxy[ind-1].state() != PyTango.DevState.ON:
                self.proxy[ind-1].command_inout("Stop")  

    def ReadAll(self):
        if self.debugFlag: print "HasyOneDCtrl.ReadAll",self.inst_name
        pass

    def ReadOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.ReadOne",self.inst_name,"index",ind
        if self.flagIsXIA[ind-1]:
            data = self.proxy[ind-1].Spectrum
        else:
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
        # the state may be ON but one bank can be active
        self.proxy[ind-1].command_inout("Stop")
        self.proxy[ind-1].command_inout("Clear")
        self.proxy[ind-1].command_inout("Start")
        
    def AbortOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.AbortOne",self.inst_name,"index",ind
        self.proxy[ind-1].command_inout("Stop")
        if self.flagIsXIA[ind-1] == 0:
            self.proxy[ind-1].command_inout("Read")

       
    def GetPar(self, ind, par_name):
        if self.debugFlag: print "HasyOneDCtrl.GetPar",self.inst_name,"index",ind, "par_name", par_name

    def SetPar(self,ind,par_name,value):
        pass
    
    def GetExtraAttributePar(self,ind,name):
        if self.debugFlag: print "HasyOneDCtrl.GetExtraAttrPar",self.inst_name,"index",ind, "name", name
        if name == "TangoDevice":
            if self.device_available[ind-1]:
                tango_device = self.node + ":" + str(self.port) + "/" + self.proxy[ind-1].name() 
                return tango_device
        elif name == "DataLength":
            if self.device_available[ind-1]:
                if self.flagIsXIA[ind-1]:
                    datalength = int(self.proxy[ind-1].read_attribute("McaLength").value)
                else:
                    datalength = int(self.proxy[ind-1].read_attribute("DataLength").value)
                return datalength

    def SetExtraAttributePar(self,ind,name,value):
        if self.debugFlag: print "HasyOneDCtrl.SetExtraAttributePar",self.inst_name,"index",ind," name=",name," value=",value
        if name == "DataLength":
            if self.device_available[ind-1]:
                if self.flagIsXIA[ind-1]:
                    self.proxy[ind-1].write_attribute("McaLength",value)
                else:
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
