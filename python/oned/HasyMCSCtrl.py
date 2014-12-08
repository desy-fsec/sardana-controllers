

import time, os

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import OneDController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

debugFlag = True


class HasyMCSCtrl(OneDController):
    "This class is the Tango Sardana One D controller for Hasylab"

    ctrl_extra_attributes = {'NbChannels':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'NbAcquisitions':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'Preset':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'TangoDevice':{Type:str,Access:ReadOnly},
                             }
                 
    class_prop = {'RootDeviceName':{Type:'PyTango.DevString',Description:'The root name of the MCS Tango devices'},
                  'TangoHost':{Type:str,Description:'The tango host where searching the devices'},}
                 
    MaxDevice = 97

    def __init__(self,inst,props, *args, **kwargs):
        self.TangoHost = None
        OneDController.__init__(self,inst,props, *args, **kwargs)
        self.debugFlag = False
        if os.isatty(1): 
            self.debugFlag = True
        if self.debugFlag: print "HasyMCSCtrl.__init__, inst ",self.inst_name,"RootDeviceName",self.RootDeviceName
        self.ct_name = "HasyMCSCtrl/" + self.inst_name
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
        self.flagIsMCS = []
        self.device_available = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.flagIsMCS.append( False)
            self.device_available.append(False)
            self.max_device =  self.max_device + 1
        self.started = False
        self.dft_NbChannels = 0
        self.NbChannels = []
        self.dft_NbAcquisitions = 0
        self.NbAcquisitions = []
        self.dft_Preset = 0
        self.Preset = []

        
    def AddDevice(self,ind):
        OneDController.AddDevice(self,ind)
        if ind > self.max_device:
            print "HasyMCSCtrl: False index %d max %d" % (ind, self.max_device)
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = True
        self.NbChannels.append(self.dft_NbChannels)
        self.NbAcquisitions.append(self.dft_NbAcquisitions)
        self.Preset.append(self.dft_Preset)
        if self.debugFlag: print "HasyMCSCtrl.AddDevice ",self.inst_name,"index",ind, "isMCS", self.flagIsMCS[ind-1]

       
    def DeleteDevice(self,ind):
        if self.debugFlag: print "HasyMCSCtrl.DeleteDevice",self.inst_name,"index",ind
        OneDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
        
    def StateOne(self,ind):
        if self.debugFlag: print "HasyMCSCtrl.StatOne",self.inst_name,"index",ind
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta,"The MCS is ready")
        else:
            sta = PyTango.DevState.FAULT
            tup = (sta, "Device not available")

        return tup
    
    def LoadOne(self, axis, value):
        if self.debugFlag: print "HasyMCSCtrl.LoadOne",self.inst_name,"axis", axis
        idx = axis - 1
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        

    def PreReadAll(self):
        if self.debugFlag: print "HasyMCSCtrl.PreReadAll",self.inst_name
        pass

    def PreReadOne(self,ind):
        if self.debugFlag: print "HasyMCSCtrl.PreReadOne",self.inst_name,"index",ind
        self.proxy[ind-1].command_inout("ReadMCS")

    def ReadAll(self):
        if self.debugFlag: print "HasyMCSCtrl.ReadAll",self.inst_name
        pass

    def ReadOne(self,ind):
        if self.debugFlag: print "HasyMCSCtrl.ReadOne",self.inst_name,"index",ind
        data = []
        for i in range(0,self.proxy[ind-1].NbAcquisitions):
            for j in range(0,self.proxy[ind-1].NbChannels):
                data.append(self.proxy[ind-1].CountsArray[i][j])
        return data

    def PreStartAll(self):
        if self.debugFlag: print "HasyMCSCtrl.PreStartAll",self.inst_name
        pass

    def PreStartOne(self,ind, value):
        return True
        
    def StartOne(self,ind, value):
        if self.debugFlag: print "HasyMCSCtrl.StartOne",self.inst_name,"index",ind
        self.proxy[ind-1].command_inout("SetupMCS")
        
    def AbortOne(self,ind):
        if self.debugFlag: print "HasyMCSCtrl.AbortOne",self.inst_name,"index",ind
       
    def GetPar(self, ind, par_name):
        if self.debugFlag: print "HasyMCSCtrl.GetPar",self.inst_name,"index",ind, "par_name", par_name

    def SetPar(self,ind,par_name,value):
        pass
    
    def GetExtraAttributePar(self,ind,name):
        if self.debugFlag: print "HasyMCSCtrl.GetExtraAttrPar",self.inst_name,"index",ind, "name", name
        if name == "NbChannels": 
            if self.device_available[ind-1]:
                return int(self.proxy[ind-1].read_attribute("NbChannels").value)
        elif name == "NbAcquisitions": 
            if self.device_available[ind-1]:
                return int(self.proxy[ind-1].read_attribute("NbAcquisitions").value)
        elif name == "Preset": 
            if self.device_available[ind-1]:
                return int(self.proxy[ind-1].read_attribute("Preset").value)
        elif name == "TangoDevice":
            if self.device_available[ind-1]:
                tango_device = self.node + ":" + str(self.port) + "/" + self.proxy[ind-1].name() 
                return tango_device

    def SetExtraAttributePar(self,ind,name,value):
        if self.debugFlag: print "HasyMCSCtrl.SetExtraAttributePar",self.inst_name,"index",ind," name=",name," value=",value
        if name == "NbChannels":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("NbChannels",value)
        if name == "NbAcquisitions":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("NbAcquisitions",value)
        if name == "Preset":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Preset",value)

    def SendToCtrl(self,in_data):
#        if self.debugFlag: print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        if self.debugFlag: print "HasyMCSCtrl/",self.inst_name,": delete"

        
if __name__ == "__main__":
    obj = OneDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
