import PyTango

import os

from sardana import DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description


class HasyMotorCtrl(MotorController):
    """This class is the Tango Sardana Motor controller
    for standard Hasylab Motors.
    
    """

    axis_attributes = {
        'UnitLimitMax': {Type:float,Access:DataAccess.ReadWrite},
        'UnitLimitMin' :{Type:float,Access:DataAccess.ReadWrite},
        'PositionSim': {Type:float,Access:DataAccess.ReadWrite},
        'ResultSim': {Type:str,Access:DataAccess.ReadWrite},
        'TangoDevice': {Type:str,Access:DataAccess.ReadOnly}, # used for handling limits between TangoServer and PoolDevice
        'Calibrate': {Type:float,Access:DataAccess.ReadWrite},
        'Conversion': {Type:float,Access:DataAccess.ReadWrite}
    }
    ctrl_properties = {
        'RootDeviceName': {
            Type:str,Description:'The root name of the Motor Tango devices'},
        'TangoHost': {
            Type:str,Description:'The tango host where searching the devices'}, 
    }
    ctrl_attributes = {
        'ExtraParameterName': {Type:str,Access:DataAccess.ReadWrite}}

    attrNames_UnitLimitMax = [
        "UnitLimitMax", "SoftLimitMax", "SoftLimitCw", "SoftCwLimit"]
    attrNames_UnitLimitMin = [
        "UnitLimitMin", "SoftLimitMin", "SoftLimitCcw", "SoftCcwLimit"]
    attrNames_CwLimit = [
        "CwLimit", "FlagCwLimit", "CwLimitFault"]
    attrNames_CcwLimit = [
        "CcwLimit", "FlagCcwLimit", "CcwLimitFault"]
    attrNames_Velocity = [
        "SlewDouble", "SlewRate", "VelocityUnits", "Velocity"]
    attrNames_Acceleration = [
        "AccelerationUnits", "Acceleration"]
    cmdNames_Abort = [
        "StopMove", "AbortMove", "Stop"]
    servers_ConversionIncluded = [
        "OmsMaxV", "GalilDMCMotor", "AerotechEnsembleMotor"] 

    gender = "Motor"
    model = "Hasylab Motor"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        # the next line is because of haso228k (64bit)
        self.TangoHost = None
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.db = PyTango.Database()
        self.debugFlag = False
        if os.isatty(1): 
            self.debugFlag = True
        if self.TangoHost == None:
            self.db = PyTango.Database()
        else:
            #
            # TangoHost can be hasgksspp07eh3:10000
            #
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find(':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int(lst[1])
            self.db = PyTango.Database(self.node, self.port)
        if self.debugFlag:
            print "HasyMotorCtrl.__init__, inst", self.inst_name, \
                "RootDeviceName", self.RootDeviceName
        name_dev_ask =  self.RootDeviceName + "*"
        self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.device_available = []
        self.attrName_UnitLimitMax = []
        self.attrName_UnitLimitMin = []
        self.attrName_CwLimit = []
        self.attrName_CcwLimit = []
        self.attrName_Velocity = []
        self.attrName_Acceleration = []
        self.cmdName_Abort = []
        self.conversion_included = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.attrName_UnitLimitMax.append(None)
            self.attrName_UnitLimitMin.append(None)
            self.attrName_CwLimit.append(None)
            self.attrName_CcwLimit.append(None)
            self.attrName_Velocity.append(None)
            self.attrName_Acceleration.append(None)
            self.cmdName_Abort.append(None)
            self.conversion_included.append(False)
            self.max_device = self.max_device + 1
        self.dft_UnitLimitMax = 0
        self.UnitLimitMax = []
        self.dft_UnitLimitMin = 0
        self.UnitLimitMin = []
        self.dft_PositionSim = 0
        self.PositionSim = []
        self.dft_ResultSim = " "
        self.ResultSim = []
        self.extraparametername = "None"

    def AddDevice(self, ind):
        MotorController.AddDevice(self, ind)
        if ind > self.max_device:
            print "False index"
            return
        proxy_name = self.tango_device[ind-1]
        if self.TangoHost == None:
            proxy_name = self.tango_device[ind-1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + str(self.tango_device[ind-1])
        if self.debugFlag:
            print "HasyMotorCtrl.AddDevice %s index %d" % (proxy_name, ind)
        self.proxy[ind-1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind-1] = 1
        self.UnitLimitMax.append(self.dft_UnitLimitMax)
        self.UnitLimitMin.append(self.dft_UnitLimitMin)
        self.PositionSim.append(self.dft_PositionSim)
        self.ResultSim.append(self.dft_ResultSim)
        attrs = self.proxy[ind-1].get_attribute_list()
        cmds = [cmd.cmd_name for cmd in self.proxy[ind-1].command_list_query()]
        for attrName in HasyMotorCtrl.attrNames_UnitLimitMax:
            if attrName in attrs:
                self.attrName_UnitLimitMax[ind-1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_UnitLimitMin:
            if attrName in attrs:
                self.attrName_UnitLimitMin[ind-1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_CwLimit:
            if attrName in attrs:
                self.attrName_CwLimit[ind-1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_CcwLimit:
            if attrName in attrs:
                self.attrName_CcwLimit[ind-1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_Velocity:
            if attrName in attrs:
                self.attrName_Velocity[ind-1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_Acceleration:
            if attrName in attrs:
                self.attrName_Acceleration[ind-1] = attrName
                break
        for cmdName in HasyMotorCtrl.cmdNames_Abort:
            if cmdName in cmds:
                self.cmdName_Abort[ind-1] = cmdName
                break
        if self.proxy[ind-1].info().dev_class in HasyMotorCtrl.servers_ConversionIncluded:
            # there are two different GalilDMC servers used at DESY
            if not (self.proxy[ind-1].info().dev_class == "GalilDMCMotor" and self.attrName_Acceleration[ind-1] == "SlewRate"):
                self.conversion_included[ind-1] = True

    def DeleteDevice(self, ind):
        MotorController.DeleteDevice(self, ind)
        self.proxy[ind-1] = None
        self.device_available[ind-1] = 0

    def StateOne(self, ind):
        status_template = "STATE(%s) LIM+(%s) LIM-(%s)"
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            lower = 0
            upper = 0
            if self.attrName_CwLimit[ind-1] is not None:
                lower = self.proxy[ind-1].read_attribute(self.attrName_CwLimit[ind-1]).value
            if self.attrName_CcwLimit[ind-1] is not None:
                upper = self.proxy[ind-1].read_attribute(self.attrName_CcwLimit[ind-1]).value
            switchstate = lower * 4 + upper * 2
            status_string = status_template % (sta, upper, lower)
            tup = (sta, status_string, switchstate)
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        if self.device_available[ind-1] == 1:
            return self.proxy[ind-1].read_attribute("Position").value

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, pos):
        return True

    def StartOne(self, ind, pos):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].write_attribute("Position", pos)

    def GetExtraAttributePar(self, ind, name):
        value = None
        if self.device_available[ind-1]:
            if name == "UnitLimitMax":
                value = float(self.proxy[ind-1].read_attribute(self.attrName_UnitLimitMax[ind-1]).value)
            elif name == "UnitLimitMin":
                value = float(self.proxy[ind-1].read_attribute(self.attrName_UnitLimitMin[ind-1]).value)
            elif name == "PositionSim":
                value = float(self.proxy[ind-1].read_attribute("PositionSim").value)
            elif name == "ResultSim":
                value = str(self.proxy[ind-1].read_attribute("ResultSim").value)
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + self.proxy[ind-1].name() 
                value = tango_device
            elif name == "Calibrate":
                value = -1
            elif name == "Conversion":
                value = float(self.proxy[ind-1].read_attribute("Conversion").value)
        return value

    def SetExtraAttributePar(self, ind, name, value):
        if self.device_available[ind-1]:
            if name == "UnitLimitMax":
                self.proxy[ind-1].write_attribute(self.attrName_UnitLimitMax[ind-1], value)
            elif name == "UnitLimitMin":
                self.proxy[ind-1].write_attribute(self.attrName_UnitLimitMin[ind-1], value)
            elif name == "PositionSim":
                self.proxy[ind-1].write_attribute("PositionSim", value)
            elif name == "ResultSim":
                self.proxy[ind-1].write_attribute("ResultSim", value)
            elif name == "Calibrate":
                self.proxy[ind-1].command_inout("Calibrate", value)
            elif name == "Conversion":
                self.proxy[ind-1].write_attribute("Conversion", value)

    def SetAxisPar(self, ind, name, value):
        if self.device_available[ind-1]:
            name = name.lower()
            if name == "acceleration" or name == "deceleration":
                try:
                    velocity = float(self.proxy[ind-1].read_attribute(self.attrName_Velocity[ind-1]).value)
                except:
                    velocity = 1.0
                if value == 0.0:
                    value = 1.0
                self.proxy[ind-1].write_attribute(self.attrName_Acceleration[ind-1], long(velocity / value))
            elif name == "base_rate":
                self.proxy[ind-1].write_attribute("BaseRate", long(value))
            elif name == "velocity":
                if not self.conversion_included[ind-1]:
                    try:
                        conversion = abs(float(self.proxy[ind-1].read_attribute("Conversion").value))
                    except:
                        conversion = 1.0
                    self.proxy[ind-1].write_attribute(self.attrName_Velocity[ind-1], (value * conversion))
                else:
                    self.proxy[ind-1].write_attribute(self.attrName_Velocity[ind-1], value)
            elif name == "step_per_unit":
                self.proxy[ind-1].write_attribute("Conversion", value)

    def GetAxisPar(self, ind, name):
        value = float('nan')
        if self.device_available[ind-1]:
            name = name.lower()
            if name == "acceleration" or name == "deceleration":
                value = float(self.proxy[ind-1].read_attribute(self.attrName_Acceleration[ind-1]).value)
                try:
                    velocity = float(self.proxy[ind-1].read_attribute(self.attrName_Velocity[ind-1]).value)
                except:
                    velocity = 1.0
                if value == 0.0:
                    value = 1.0
                value = velocity / value
            elif name == "base_rate":
                try:
                    value = float(self.proxy[ind-1].read_attribute("BaseRate").value)
                    try:
                        conversion = abs(float(self.proxy[ind-1].read_attribute("Conversion").value))
                    except:
                        conversion = 1.0
                    value /= conversion
                except:
                    value = 0.0
            elif name == "velocity":
                value = float(self.proxy[ind-1].read_attribute(self.attrName_Velocity[ind-1]).value)
                if not self.conversion_included[ind-1]:
                    try:
                        conversion = abs(float(self.proxy[ind-1].read_attribute("Conversion").value))
                    except:
                        conversion = 1.0
                    value /= conversion
            elif name == "step_per_unit":
                try:
                    value = float(self.proxy[ind-1].read_attribute("Conversion").value)
                except:
                    value = 1.0
        return value

    def StartAll(self):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def AbortOne(self, ind):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].command_inout(self.cmdName_Abort[ind-1])

    def DefinePosition(self, ind, position):
        if self.device_available[ind-1] == 1:
            position = float(position)
            self.proxy[ind-1].Calibrate(position)

    def setExtraParameterName(self, extra_parameter_name):
        self.extraparametername = extra_parameter_name

    def getExtraParameterName(self):
        return self.extraparametername

    def __del__(self):
        print "PYTHON -> HasyMotorCtrl/", self.inst_name, ": dying"
