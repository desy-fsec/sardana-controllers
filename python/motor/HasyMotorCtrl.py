import PyTango

import os

from sardana import DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import (Memorize, Memorized,
#                                      NotMemorized, DefaultValue)
from sardana.pool.controller import Memorize, NotMemorized


class HasyMotorCtrl(MotorController):
    """This class is the Tango Sardana Motor controller
    for standard Hasylab Motors.

    """

    axis_attributes = {
        'UnitLimitMax': {
            Type: float, Access: DataAccess.ReadWrite, Memorize: NotMemorized},
        'UnitLimitMin': {
            Type: float, Access: DataAccess.ReadWrite, Memorize: NotMemorized},
        'PositionSim': {
            Type: float, Access: DataAccess.ReadWrite},
        'ResultSim': {
            Type: str, Access: DataAccess.ReadWrite},
        # used for handling limits between TangoServer and PoolDevice
        'TangoDevice': {
            Type: str, Access: DataAccess.ReadOnly},
        'Calibrate': {Type: float, Access: DataAccess.ReadWrite},
        'Conversion': {Type: float, Access: DataAccess.ReadWrite}
    }
    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the Motor Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }
    ctrl_attributes = {
        'ExtraParameterName': {Type: str, Access: DataAccess.ReadWrite}}

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
        if self.TangoHost is None:
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
        name_dev_ask = self.RootDeviceName + "*"
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

        self.dft_UnitLimitMax = 0
        self.UnitLimitMax = []
        self.dft_UnitLimitMin = 0
        self.UnitLimitMin = []
        self.dft_PositionSim = 0
        self.PositionSim = []
        self.dft_ResultSim = " "
        self.ResultSim = []
        self.extraparametername = "None"
        self.poolmotor_proxy = []
        self.set_for_memorized_min = []
        self.set_for_memorized_max = []
        self.flag_standa = []

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
            self.UnitLimitMax.append(self.dft_UnitLimitMax)
            self.UnitLimitMin.append(self.dft_UnitLimitMin)
            self.PositionSim.append(self.dft_PositionSim)
            self.ResultSim.append(self.dft_ResultSim)
            #  Can not be created in AddDevice because
            #     the pool motor device does not exist
            self.poolmotor_proxy.append(None)
            self.set_for_memorized_min.append(1)
            self.set_for_memorized_max.append(1)
            self.flag_standa.append(0)

            self.max_device = self.max_device + 1

    def AddDevice(self, ind):
        MotorController.AddDevice(self, ind)
        if ind > self.max_device:
            print("False index")
            self.device_available[ind - 1] = 0
            return
        proxy_name = self.tango_device[ind - 1]
        if self.TangoHost is None:
            proxy_name = self.tango_device[ind - 1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(self.tango_device[ind - 1])
        if self.debugFlag:
            print("HasyMotorCtrl.AddDevice %s index %d" % (proxy_name, ind))
        self.proxy[ind - 1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind - 1] = 1

        attrs = self.proxy[ind - 1].get_attribute_list()
        cmds = [
            cmd.cmd_name for cmd in self.proxy[ind - 1].command_list_query()]
        for attrName in HasyMotorCtrl.attrNames_UnitLimitMax:
            if attrName in attrs:
                self.attrName_UnitLimitMax[ind - 1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_UnitLimitMin:
            if attrName in attrs:
                self.attrName_UnitLimitMin[ind - 1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_CwLimit:
            if attrName in attrs:
                self.attrName_CwLimit[ind - 1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_CcwLimit:
            if attrName in attrs:
                self.attrName_CcwLimit[ind - 1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_Velocity:
            if attrName in attrs:
                self.attrName_Velocity[ind - 1] = attrName
                break
        for attrName in HasyMotorCtrl.attrNames_Acceleration:
            if attrName in attrs:
                self.attrName_Acceleration[ind - 1] = attrName
                break
        # Identify Standa8smc4usb motor, not fsec server (cfel)
        if "gpioFlags" in attrs:
            self.flag_standa[ind - 1] = 1
        for cmdName in HasyMotorCtrl.cmdNames_Abort:
            if cmdName in cmds:
                self.cmdName_Abort[ind - 1] = cmdName
                break
        if self.proxy[ind - 1].info().dev_class in \
           HasyMotorCtrl.servers_ConversionIncluded:
            # there are two different GalilDMC servers used at DESY
            if not (self.proxy[ind - 1].info().dev_class == "GalilDMCMotor"
                    and self.attrName_Acceleration[ind - 1] == "SlewRate"):
                self.conversion_included[ind - 1] = True

    def DeleteDevice(self, ind):
        MotorController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        status_template = "STATE(%s) LIM+(%s) LIM-(%s)"
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            lower = 0
            upper = 0
            if self.attrName_CwLimit[ind - 1] is not None:
                lower = self.proxy[ind - 1].read_attribute(
                    self.attrName_CwLimit[ind - 1]).value
            if self.attrName_CcwLimit[ind - 1] is not None:
                upper = self.proxy[ind - 1].read_attribute(
                    self.attrName_CcwLimit[ind - 1]).value
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
        if self.device_available[ind - 1] == 1:
            if self.flag_standa[ind - 1] == 1:
                return self.proxy[ind - 1].read_attribute("curPosition").value
            return self.proxy[ind - 1].read_attribute("Position").value

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, pos):
        return True

    def StartOne(self, ind, pos):
        if self.device_available[ind - 1] == 1:
            if self.flag_standa[ind - 1] == 1:
                self.proxy[ind - 1].Move(pos)
                return
            self.proxy[ind - 1].write_attribute("Position", pos)

    def GetAxisExtraPar(self, ind, name):
        value = None
        if self.device_available[ind - 1]:
            if name == "UnitLimitMax":
                if self.flag_standa[ind - 1] == 1:
                    return 0
                if self.poolmotor_proxy[ind - 1] is None:
                    self.poolmotor_proxy[ind - 1] = PyTango.DeviceProxy(
                        self.GetAxisName(ind))
                value = float(self.proxy[ind - 1].read_attribute(
                    self.attrName_UnitLimitMax[ind - 1]).value)
                cfg = []
                config = self.poolmotor_proxy[ind - 1].get_attribute_config(
                    "Position")
                config.max_value = str(value)
                cfg.append(config)
                self.poolmotor_proxy[ind - 1].set_attribute_config(cfg)

            elif name == "UnitLimitMin":
                if self.flag_standa[ind - 1] == 1:
                    return 0
                if self.poolmotor_proxy[ind - 1] is None:
                    self.poolmotor_proxy[ind - 1] = PyTango.DeviceProxy(
                        self.GetAxisName(ind))
                value = float(self.proxy[ind - 1].read_attribute(
                    self.attrName_UnitLimitMin[ind - 1]).value)

                cfg = []
                config = self.poolmotor_proxy[ind - 1].get_attribute_config(
                    "Position")
                config.min_value = str(value)
                cfg.append(config)
                self.poolmotor_proxy[ind - 1].set_attribute_config(cfg)

            elif name == "PositionSim":
                if self.flag_standa[ind - 1] == 1:
                    return 0
                value = float(self.proxy[ind - 1].read_attribute(
                    "PositionSim").value)
            elif name == "ResultSim":
                if self.flag_standa[ind - 1] == 1:
                    return "None"
                value = str(self.proxy[ind - 1].read_attribute(
                    "ResultSim").value)
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                value = tango_device
            elif name == "Calibrate":
                value = -1
            elif name == "Conversion":
                if self.flag_standa[ind - 1] == 1:
                    return 0
                value = float(self.proxy[ind - 1].read_attribute(
                    "Conversion").value)
        return value

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if self.flag_standa[ind - 1] == 1:
                return
            if name == "UnitLimitMax":
                if self.poolmotor_proxy[ind - 1] is None:
                    self.poolmotor_proxy[ind - 1] = PyTango.DeviceProxy(
                        self.GetAxisName(ind))
                self.proxy[ind - 1].write_attribute(
                    self.attrName_UnitLimitMax[ind - 1], value)
                if not self.set_for_memorized_max[ind - 1]:
                    cfg = []
                    config = self.poolmotor_proxy[
                        ind - 1].get_attribute_config("Position")
                    config.max_value = str(value)
                    cfg.append(config)
                    self.poolmotor_proxy[ind - 1].set_attribute_config(cfg)
                self.set_for_memorized_max[ind - 1] = 0
            elif name == "UnitLimitMin":
                if self.poolmotor_proxy[ind - 1] is None:
                    self.poolmotor_proxy[ind - 1] = PyTango.DeviceProxy(
                        self.GetAxisName(ind))
                self.proxy[ind - 1].write_attribute(
                    self.attrName_UnitLimitMin[ind - 1], value)
                if not self.set_for_memorized_min[ind - 1]:
                    cfg = []
                    config = self.poolmotor_proxy[
                        ind - 1].get_attribute_config("Position")
                    config.min_value = str(value)
                    cfg.append(config)
                    self.poolmotor_proxy[ind - 1].set_attribute_config(cfg)
                self.set_for_memorized_min[ind - 1] = 0

            elif name == "PositionSim":
                self.proxy[ind - 1].write_attribute("PositionSim", value)
            elif name == "ResultSim":
                self.proxy[ind - 1].write_attribute("ResultSim", value)
            elif name == "Calibrate":
                self.proxy[ind - 1].command_inout("Calibrate", value)
            elif name == "Conversion":
                self.proxy[ind - 1].write_attribute("Conversion", value)

    def SetAxisPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            name = name.lower()
            if name == "acceleration" or name == "deceleration":
                if self.flag_standa[ind - 1] == 1:
                    try:
                        velocity = float(self.proxy[ind - 1].read_attribute(
                            "curSpeed").value)
                    except Exception:
                        velocity = 1.0
                    if value == 0.0:
                        value = 1
                    if name == "acceleration":
                        self.proxy[ind - 1].write_attribute(
                            "accel", int(velocity / value))
                    else:
                        self.proxy[ind - 1].write_attribute(
                            "decel", int(velocity / value))
                    return
                try:
                    velocity = float(self.proxy[ind - 1].read_attribute(
                        self.attrName_Velocity[ind - 1]).value)
                except Exception:
                    velocity = 1.0
                if value == 0.0:
                    value = 1.0
                self.proxy[ind - 1].write_attribute(
                    self.attrName_Acceleration[ind - 1], int(velocity / value))
            elif name == "base_rate":
                if self.flag_standa[ind - 1] == 1:
                    return
                self.proxy[ind - 1].write_attribute("BaseRate", int(value))
            elif name == "velocity":
                if self.flag_standa[ind - 1] == 1:
                    self.proxy[ind - 1].write_attribute(
                        "speed", value)
                    return
                if not self.conversion_included[ind - 1]:
                    try:
                        conversion = abs(
                            float(self.proxy[ind - 1].read_attribute(
                                "Conversion").value))
                    except Exception:
                        conversion = 1.0
                    self.proxy[ind - 1].write_attribute(
                        self.attrName_Velocity[ind - 1], (value * conversion))
                else:
                    self.proxy[ind - 1].write_attribute(
                        self.attrName_Velocity[ind - 1], value)
            elif name == "step_per_unit":
                if self.flag_standa[ind - 1] == 1:
                    return
                self.proxy[ind - 1].write_attribute("Conversion", value)

    def GetAxisPar(self, ind, name):
        value = float('nan')
        if self.device_available[ind - 1]:
            name = name.lower()
            if name == "acceleration" or name == "deceleration":
                if self.flag_standa[ind - 1] == 1:
                    if name == "acceleration":
                        value = float(self.proxy[ind - 1].read_attribute(
                            "accel").value)
                    else:
                        value = float(self.proxy[ind - 1].read_attribute(
                            "decel").value)

                    try:
                        velocity = float(self.proxy[ind - 1].read_attribute(
                            "curSpeed").value)
                    except Exception:
                        velocity = 1.0
                    if value == 0.0:
                        value = 1.0
                    value = velocity / value
                    return value
                value = float(self.proxy[ind - 1].read_attribute(
                    self.attrName_Acceleration[ind - 1]).value)
                try:
                    velocity = float(self.proxy[ind - 1].read_attribute(
                        self.attrName_Velocity[ind - 1]).value)
                except Exception:
                    velocity = 1.0
                if value == 0.0:
                    value = 1.0
                value = velocity / value
            elif name == "base_rate":
                if self.flag_standa[ind - 1] == 1:
                    return 0.0
                try:
                    value = float(self.proxy[ind - 1].read_attribute(
                        "BaseRate").value)
                    try:
                        conversion = abs(float(
                            self.proxy[ind - 1].read_attribute(
                                "Conversion").value))
                    except Exception:
                        conversion = 1.0
                    value /= conversion
                except Exception:
                    value = 0.0
            elif name == "velocity":
                if self.flag_standa[ind - 1] == 1:
                    value = float(self.proxy[ind - 1].read_attribute(
                        "curSpeed").value)
                    return value
                value = float(self.proxy[ind - 1].read_attribute(
                    self.attrName_Velocity[ind - 1]).value)
                if not self.conversion_included[ind - 1]:
                    try:
                        conversion = abs(
                            float(self.proxy[ind - 1].read_attribute(
                                "Conversion").value))
                    except Exception:
                        conversion = 1.0
                    value /= conversion
            elif name == "step_per_unit":
                if self.flag_standa[ind - 1] == 1:
                    return 1.0
                try:
                    value = float(self.proxy[ind - 1].read_attribute(
                        "Conversion").value)
                except Exception:
                    value = 1.0
        return value

    def StartAll(self):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def AbortOne(self, ind):
        if ind > self.max_device:
            pass
        if self.device_available[ind - 1] == 1:
            try:
                self.proxy[ind - 1].command_inout(self.cmdName_Abort[ind - 1])
            except Exception:
                pass

    def DefinePosition(self, ind, position):
        if self.device_available[ind - 1] == 1:
            if self.flag_standa[ind - 1] == 1:
                return
            position = float(position)
            self.proxy[ind - 1].Calibrate(position)

    def setExtraParameterName(self, extra_parameter_name):
        self.extraparametername = extra_parameter_name

    def getExtraParameterName(self):
        return self.extraparametername

    def __del__(self):
        pass
