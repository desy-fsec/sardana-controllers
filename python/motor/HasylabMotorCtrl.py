import PyTango

import time

from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

    
class HasylabMotorController(MotorController):
    "This class is the Tango Sardana Motor controller for standard Hasylab Motors"


    axis_attributes = {'UnitLimitMax':{Type:float,Access:ReadWrite},
                       'UnitLimitMin':{Type:float,Access:ReadWrite},
                       'PositionSim':{Type:float,Access:ReadWrite},
                       'ResultSim':{Type:str,Access:ReadWrite},
                       'Calibrate':{Type:float,Access:ReadWrite}}

			     
    ctrl_properties = {'RootDeviceName':{Type:str,Description:'The root name of the Motor Tango devices'}}


    ctrl_attributes = {'ExtraParameterName':{Type:str,Access:ReadWrite}}
      
    gender = "Motor"
    model = "Hasylab Motor"
    organization = "DESY"
    state = ""
    status = ""
    
    def __init__(self,inst,props,*args, **kwargs):
        MotorController.__init__(self,inst,props,*args, **kwargs)

        self.db = PyTango.Database()
        name_dev_ask =  self.RootDeviceName + "*"
        self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.device_available = []
        self.haslimits = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.haslimits.append(0)
            self.max_device =  self.max_device + 1
        self.dft_UnitLimitMax = 0
        self.UnitLimitMax = []
        self.dft_UnitLimitMin = 0
        self.UnitLimitMin = []
        self.dft_PositionSim = 0
        self.PositionSim = []
        self.dft_ResultSim = " "
        self.ResultSim = []
        self.extraparametername = "None"
        
    def AddDevice(self,ind):
        MotorController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1
        self.UnitLimitMax.append(self.dft_UnitLimitMax)
        self.UnitLimitMin.append(self.dft_UnitLimitMin)
        self.PositionSim.append(self.dft_PositionSim)
        self.ResultSim.append(self.dft_ResultSim)
        for attr in self.proxy[ind-1].get_attribute_list():
            if attr == "CcwLimit":
                self.haslimits[ind - 1] = 1
        
    def DeleteDevice(self,ind):
        MotorController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
    def StateOne(self,ind):
        status_template = "STATE(%s) LIM+(%s) LIM-(%s)"
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            switchstate = 0
            if self.haslimits[ind - 1]:
                lower = self.proxy[ind-1].read_attribute("CwLimit").value
                upper = self.proxy[ind-1].read_attribute("CcwLimit").value
            else:
                lower = 0
                upper = 0
            if lower == 1 and upper == 1:
                switchstate = 6
            elif lower == 1:
                switchstate = 4
            elif upper == 1:
                switchstate = 2
            status_string = status_template % (sta,upper,lower)
            tup = (sta,status_string,switchstate)
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self,ind):
        if self.device_available[ind-1] == 1:
            return self.proxy[ind-1].read_attribute("Position").value

    def PreStartAll(self):
        pass

    def PreStartOne(self,ind,pos):
        return True
		
    def StartOne(self,ind,pos):
        if self.device_available[ind-1] == 1:
                self.proxy[ind-1].write_attribute("Position",pos)
	
    def GetExtraAttributePar(self,ind,name):
        if self.device_available[ind-1]:
            if name == "UnitLimitMax":
                return float(self.proxy[ind-1].read_attribute("UnitLimitMax").value)
            elif name == "UnitLimitMin":
                return float(self.proxy[ind-1].read_attribute("UnitLimitMin").value)
            elif name == "PositionSim":
                return float(self.proxy[ind-1].read_attribute("PositionSim").value)
            elif name == "ResultSim":
                return str(self.proxy[ind-1].read_attribute("ResultSim").value)
            elif name == "Calibrate":
                return -1

    def SetExtraAttributePar(self,ind,name,value):
        if self.device_available[ind-1]:
            if name == "UnitLimitMax":
                self.proxy[ind-1].write_attribute("UnitLimitMax",value)
            elif name == "UnitLimitMin":
                self.proxy[ind-1].write_attribute("UnitLimitMin",value)
            elif name == "PositionSim":
                self.proxy[ind-1].write_attribute("PositionSim",value)
            elif name == "ResultSim":
                self.proxy[ind-1].write_attribute("ResultSim",value)
            elif name == "Calibrate":
                self.proxy[ind-1].command_inout("Calibrate",value)
    
    def SetAxisPar(self, ind, name, value):
        if self.device_available[ind-1]:
            name = name.lower()
            if name == "acceleration":
                self.proxy[ind-1].write_attribute("Acceleration",value)
            elif name == "deceleration":
                self.proxy[ind-1].write_attribute("Acceleration",value)
            elif name == "base_rate":
                self.proxy[ind-1].write_attribute("BaseRate",value)
            elif name == "velocity":
                self.proxy[ind-1].write_attribute("SlewRate",value)
            elif name == "step_per_unit":
                self.proxy[ind-1].write_attribute("Conversion",value)
            
    def GetAxisPar(self, ind, name):
        if self.device_available[ind-1]:
            name = name.lower()
            if name == "acceleration":
                v = self.proxy[ind-1].read_attribute("Acceleration").value
            elif name == "deceleration":
                v = self.proxy[ind-1].read_attribute("Acceleration").value
            elif name == "base_rate":
                v = self.proxy[ind-1].read_attribute("BaseRate").value
            elif name == "velocity":
                v = self.proxy[ind-1].read_attribute("SlewRate").value
            elif name == "step_per_unit":
                v = self.proxy[ind-1].read_attribute("Conversion").value
        return v
    
    def StartAll(self):
        pass

    def SendToCtrl(self,in_data):
        return "Nothing sent"
 
    def AbortOne(self, ind):
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("StopMove")

    def DefinePosition(self, ind, position):
        if  self.device_available[ind-1] == 1:
            position = float(position)
            self.proxy[ind-1].Calibrate(position)
            

    def setExtraParameterName(self, extra_parameter_name):
        self.extraparametername = extra_parameter_name

    def getExtraParameterName(self):
        return self.extraparametername
       
    def __del__(self):
        print "PYTHON -> HasylabMotorController/",self.inst_name,": dying"
