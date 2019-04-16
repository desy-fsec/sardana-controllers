
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
                             'RoI1Start':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'RoI1End':{Type:'PyTango.DevLong',Access:ReadWrite}, 
                             'CountsRoI1':{Type:'PyTango.DevDouble',Access:ReadOnly}, 
                             'RoI2Start':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'RoI2End':{Type:'PyTango.DevLong',Access:ReadWrite}, 
                             'CountsRoI2':{Type:'PyTango.DevDouble',Access:ReadOnly},  
                             'RoI3Start':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'RoI3End':{Type:'PyTango.DevLong',Access:ReadWrite}, 
                             'CountsRoI3':{Type:'PyTango.DevDouble',Access:ReadOnly}, 
                             'RoI4Start':{Type:'PyTango.DevLong',Access:ReadWrite},
                             'RoI4End':{Type:'PyTango.DevLong',Access:ReadWrite}, 
                             'CountsRoI4':{Type:'PyTango.DevDouble',Access:ReadOnly},        
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
        self.flagIsSIS3302 = []
        self.flagIsKromo = []
        self.device_available = []
        self.RoI1_start = []
        self.RoI1_end = []
        self.Counts_RoI1 = []
        self.RoI2_start = []
        self.RoI2_end = []
        self.Counts_RoI2 = []
        self.RoI3_start = []
        self.RoI3_end = []
        self.Counts_RoI3 = []
        self.RoI4_start = []
        self.RoI4_end = []
        self.Counts_RoI4 = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.flagIsMCA8715.append( False)
            self.flagIsXIA.append( False)
            self.flagIsSIS3302.append(False)
            self.flagIsKromo.append(False)
            self.device_available.append(False)
            self.RoI1_start.append(0)
            self.RoI1_end.append(0)
            self.Counts_RoI1.append(0)
            self.RoI2_start.append(0)
            self.RoI2_end.append(0)
            self.Counts_RoI2.append(0)
            self.RoI3_start.append(0)
            self.RoI3_end.append(0)
            self.Counts_RoI3.append(0)
            self.RoI4_start.append(0)
            self.RoI4_end.append(0)
            self.Counts_RoI4.append(0)
            self.max_device =  self.max_device + 1
        self.started = False
        self.acqTime = 0
        self.acqStartTime = None


        
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
        if hasattr(self.proxy[ind-1], 'ADCxInputInvert'):
            print "ADCxInputInvert"
        if hasattr(self.proxy[ind-1], 'TriggerPeakingTime'):
            print 'TriggerPeakingTime'
        if hasattr(self.proxy[ind-1], 'ADCxInputInvert'):
            self.flagIsSIS3302[ind-1] = True
        if hasattr(self.proxy[ind-1], 'HighSpeedMode'):
            self.flagIsKromo[ind-1] = True
        if self.debugFlag: print "HasyOneDCtrl.AddDevice ",self.inst_name,"index",ind, "isMCA8715", self.flagIsMCA8715[ind-1], "isXIA", self.flagIsXIA[ind-1], "isSIS3302", self.flagIsSIS3302[ind-1]

       
    def DeleteDevice(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.DeleteDevice",self.inst_name,"index",ind
        OneDController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
        
    def StateOne(self,ind):
        #if self.debugFlag: print "HasyOneDCtrl.StatOne",self.inst_name,"index",ind
        if  self.device_available[ind-1] == 1: 
            if self.acqStartTime != None: #acquisition was started
                now = time.time()
                elapsedTime = now - self.acqStartTime - 0.2
                if elapsedTime < self.acqTime: #acquisition has probably not finished yet
                    self.sta = PyTango.DevState.MOVING
                    self.status = "Acqusition time has not elapsed yet."
                else:
                    if self.flagIsKromo[ind-1] == False:
                        self.proxy[ind-1].command_inout("Stop")
                        if self.flagIsXIA[ind-1] == 0:
                            self.proxy[ind-1].command_inout("Read")
                    self.started = False
                    self.acqStartTime = None
                    self.sta = PyTango.DevState.ON
                    self.status = "Device is ON"
            else:
                self.sta = PyTango.DevState.ON
                self.status = "Device is ON"
        else:
            sta = PyTango.DevState.FAULT
            tup = (sta, "Device not available")
        tup = (self.sta, self.status)

        return tup
    
    def LoadOne(self, ind, value):
        if self.debugFlag: print "HasyOneDCtrl.LoadOne",self.inst_name,"index", ind
        if self.flagIsKromo[ind - 1] == True:
             self.proxy[ind-1].write_attribute("ExpositionTime",value)
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value
        self.acqTime = value
        

    def PreReadAll(self):
        if self.debugFlag: print "HasyOneDCtrl.PreReadAll",self.inst_name
        pass

    def PreReadOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.PreReadOne",self.inst_name,"index",ind
            

    def ReadAll(self):
        if self.debugFlag: print "HasyOneDCtrl.ReadAll",self.inst_name

    def ReadOne(self,ind):
        print "HasyOneDCtrl.PreReadOne",self.inst_name,"index",ind
        if self.debugFlag: print "HasyOneDCtrl.ReadOne",self.inst_name,"index",ind
        if self.flagIsXIA[ind-1]:
            data = self.proxy[ind-1].Spectrum
        else:
            data = self.proxy[ind-1].Data
        self.Counts_RoI1[ind-1] = data[self.RoI1_start[ind-1]:self.RoI1_end[ind-1]].sum()
        self.Counts_RoI2[ind-1] = data[self.RoI2_start[ind-1]:self.RoI2_end[ind-1]].sum()
        self.Counts_RoI3[ind-1] = data[self.RoI3_start[ind-1]:self.RoI3_end[ind-1]].sum()
        self.Counts_RoI4[ind-1] = data[self.RoI4_start[ind-1]:self.RoI4_end[ind-1]].sum()
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
        sta = self.proxy[ind-1].command_inout("State")
        if sta == PyTango.DevState.ON:
            if self.flagIsKromo[ind-1] == False:
                self.proxy[ind-1].command_inout("Stop")
                self.proxy[ind-1].command_inout("Clear")
                self.proxy[ind-1].command_inout("Start")
            else:
                self.proxy[ind-1].command_inout("StartAcquisition")
            self.started = True
            self.acqStartTime = time.time()
                
    def AbortOne(self,ind):
        if self.debugFlag: print "HasyOneDCtrl.AbortOne",self.inst_name,"index",ind
        if self.flagIsKromo[ind-1] == False:
            self.proxy[ind-1].command_inout("Stop")
            if self.flagIsXIA[ind-1] == 0:
                self.proxy[ind-1].command_inout("Read")
        else:
            self.proxy[ind-1].command_inout("StopAcquisition")

       
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
                if self.flagIsKromo[ind - 1] == False:
                    if self.flagIsXIA[ind-1]:
                        datalength = int(self.proxy[ind-1].read_attribute("McaLength").value)
                    else:
                        datalength = int(self.proxy[ind-1].read_attribute("DataLength").value)
                else:
                    datalength = 255
                return datalength
        elif name == "RoI1Start":
            return self.RoI1_start[ind-1]
        elif name == "RoI1End":
            return self.RoI1_end[ind-1]
        elif name == "CountsRoI1":
            return self.Counts_RoI1[ind-1]
        elif name == "RoI2Start":
            return self.RoI2_start[ind-1]
        elif name == "RoI2End":
            return self.RoI2_end[ind-1]
        elif name == "CountsRoI2":
            return self.Counts_RoI2[ind-1]
        elif name == "RoI3Start":
            return self.RoI3_start[ind-1]
        elif name == "RoI3End":
            return self.RoI3_end[ind-1]
        elif name == "CountsRoI3":
            return self.Counts_RoI3[ind-1]
        elif name == "RoI4Start":
            return self.RoI4_start[ind-1]
        elif name == "RoI4End":
            return self.RoI4_end[ind-1]
        elif name == "CountsRoI4":
            return self.Counts_RoI4[ind-1]

    def SetExtraAttributePar(self,ind,name,value):
        if self.debugFlag: print "HasyOneDCtrl.SetExtraAttributePar",self.inst_name,"index",ind," name=",name," value=",value
        if self.device_available[ind-1]:
            if name == "DataLength":
                if self.flagIsKromo[ind-1] == False:
                    if self.flagIsXIA[ind-1]:
                        self.proxy[ind-1].write_attribute("McaLength",value)
                    else:
                        self.proxy[ind-1].write_attribute("DataLength",value)
            elif name == "RoI1Start":
                self.RoI1_start[ind-1] = value
            elif name == "RoI1End":
                self.RoI1_end[ind-1] = value
            elif name == "RoI2Start":
                self.RoI2_start[ind-1] = value
            elif name == "RoI2End":
                self.RoI2_end[ind-1] = value
            elif name == "RoI3Start":
                self.RoI3_start[ind-1] = value
            elif name == "RoI3End":
                self.RoI3_end[ind-1] = value
            elif name == "RoI4Start":
                self.RoI4_start[ind-1] = value
            elif name == "RoI4End":
                self.RoI4_end[ind-1] = value

    def SendToCtrl(self,in_data):
#        if self.debugFlag: print "Received value =",in_data
        return "Nothing sent"
        
    def __del__(self):
        if self.debugFlag: print "HasyOneDCtrl/",self.inst_name,": Aarrrrrg, I am dying"

        
if __name__ == "__main__":
    obj = OneDController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
