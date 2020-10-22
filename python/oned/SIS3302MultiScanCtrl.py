
import time, os

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import OneDController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class SIS3302MultiScanCtrl(OneDController):
    "This class is the Tango Sardana One D controller for Hasylab"

    axis_attributes = {'DataLength':{Type:'PyTango.DevLong',Access:ReadWrite},
                       'TangoDevice':{Type:'PyTango.DevString',Access:ReadOnly},
    }

    ctrl_properties = {'RootDeviceName':{Type:'PyTango.DevString',Description:'The root name of the MCA Tango devices'},
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
        self.started = False
        self.proxy_name = self.RootDeviceName
        if self.TangoHost != None:
            self.proxy_name = str(self.node) + (":%s/" % self.port) + str(self.proxy_name)
        self.proxy = PyTango.DeviceProxy(self.proxy_name)
        self.started = False

    def AddDevice(self,ind):
        OneDController.AddDevice(self,ind)


    def DeleteDevice(self,ind):
        #print "SIS3302MultiScanCtrl.DeleteDevice",self.inst_name,"index",ind
        OneDController.DeleteDevice(self,ind)


    def StateOne(self,ind):
        #print "SIS3302MultiScanCtrl.StatOne",self.inst_name,"index",ind
        if self.proxy.MCAScanNofHistogramsPreset == 0:
            sta = PyTango.DevState.ON
            tup = (sta, "The MCA is always ON. MCAScanNofHistogramsPreset = 0")
        else:
            sta = self.proxy.command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta, "The MCA is ready")
            elif sta == PyTango.DevState.MOVING or  sta == PyTango.DevState.RUNNING:
                tup = (PyTango.DevState.MOVING,"Device is acquiring data")
            else:
                tup = (sta, "")
        return tup

    def LoadOne(self, axis, value, repetitions, latency_time):
        #print "SIS3302MultiScanCtrl.LoadOne",self.inst_name,"axis", axis
        idx = axis - 1
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        nb_scans = 11.5*value-1
        self.proxy.MCAMultiScanNofScansPreset = int(nb_scans)

    def PreReadAll(self):
        #print "SIS3302MultiScanCtrl.PreReadAll",self.inst_name
        if self.started == True:
            if self.proxy.MCAScanNofHistogramsPreset == 0:
                self.proxy.command_inout("MultiScanDisable")
                time.sleep(0.2)
            self.started = False

    def PreReadOne(self,ind):
        #print "SIS3302MultiScanCtrl.PreReadOne",self.inst_name,"index",ind
        pass

    def ReadAll(self):
        self.counts = self.proxy.read_attribute("Count").value

    def ReadOne(self,ind):
        #print "SIS3302MultiScanCtrl.ReadOne",self.inst_name,"index",ind
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
        if self.started == False:
            self.proxy.command_inout("MultiScanDisable")
            self.proxy.command_inout("MultiScanArmScanEnable")
            self.proxy.command_inout("MultiScanStartReset")
            self.started = True

    def StartOne(self,ind, value):
        pass

    def AbortOne(self,ind):
        #print "SIS3302MultiScanCtrl.AbortOne",self.inst_name,"index",ind
        self.proxy.command_inout("MultiScanDisable")


    def GetAxisExtraPar(self,ind,name):
        #print "SIS3302MultiScanCtrl.GetExtraAttrPar",self.inst_name,"index",ind, "name", name
        if name == "TangoDevice":
            return self.proxy_name
        elif name == "DataLength":
            if ind == 1:
                datalength = int(self.proxy.read_attribute("DataLength").value)
            else:
                datalength = 1
                return datalength

    def SetAxisExtraPar(self,ind,name,value):
        #print "SIS3302MultiScanCtrl.SetExtraAttributePar",self.inst_name,"index",ind," name=",name," value=",value
        if name == "DataLength":
            if ind == 1:
                self.proxy.write_attribute("DataLength",value)

    def SendToCtrl(self,in_data):
        #print "Received value =",in_data
        return "Nothing sent"

    def __del__(self):
        #print "SIS3302MultiScanCtrl/",self.inst_name,": Aarrrrrg, I am dying"
        pass

if __name__ == "__main__":
    obj = OneDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
