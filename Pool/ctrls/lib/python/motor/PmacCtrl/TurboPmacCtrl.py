#!/usr/bin/env python2.5

#############################################################################
##
## file :    PmacCtrl.py
##
## description : 
##
## project :    miscellaneous/PoolControllers/MotorControllers
##
## developers history: zreszela
##
## copyleft :    Cells / Alba Synchrotron
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Sardana.
##
## This is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This software is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################

import PyTango

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import MotorController


class TurboPmacController(MotorController):
    """This class is the Tango Sardana motor controller for the Turbo Pmac motor controller device."""
    MaxDevice = 32
    class_prop = {'PmacEthDevName':{'Type' : 'PyTango.DevString', 'Description' : 'Device name of the PmacEth DS'}}
    
    motor_extra_attributes = {#First Word
                             "MotorActivated":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "NegativeEndLimitSet":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "PositiveEndLimitSet":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "ExtendedServoAlgorithmEnabled":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "AmplifierEnabled":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                             "OpenLoopMode":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "MoveTimerActive":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "IntegrationMode":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "DwellInProgress":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "DataBlockError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "DesiredVelocityZero":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "AbortDeceleration":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "BlockRequest":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "HomeSearchInProgress":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "User-WrittenPhaseEnable":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "User-WrittenServoEnable":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "AlternateSource_Destination":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "PhasedMotor":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "FollowingOffsetMode":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "FollowingEnabled":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "ErrorTriger":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "SoftwarePositionCapture":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "IntegratorInVelocityLoop":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "AlternateCommand-OutputMode":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             #Second Word
                             "CoordinateSystem":{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ'},
    
                             "CoordinateDefinition":{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             
                             "AssignedToCoordinateSystem":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             #Reserved for future use
                             "ForegroundInPosition":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "StoppedOnDesiredPositionLimit":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "StoppedOnPositionLimit":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "HomeComplete":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "PhasingSearch_ReadActive":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "PhasingReferenceError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "TriggerMove":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "IntegratedFatalFollowingError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "I2T_amplifierFaultError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "BacklashDirectionFlag":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             
                             "AmplifierFaultError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "FatalFollowingError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "WarningFollowingError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "InPosition":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'}}
    
    cs_extra_attributes = {"MotionProgramRunning":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'}}
    
    ctrl_extra_attributes = {}
    ctrl_extra_attributes.update(motor_extra_attributes)
    ctrl_extra_attributes.update(cs_extra_attributes)
    
    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        try:
            self.pmacEth = PyTango.DeviceProxy(self.PmacEthDevName)
        except PyTango.DevFailed, e:
            self._log.error("__init__(): Could not create PmacEth device proxy from %s device name. \nException: %s" % (self.PmacEthDevName, e))
            raise
        self.axesList = []
        self.startMultiple = {}
        self.positionMultiple = {}
        self.attributes = {}  

    def AddDevice(self, axis):
        self.axesList.append(axis)
        self.attributes[axis] = {"step_per_unit" : 1.0, "base_rate" : float("nan")}

    def DeleteDevice(self, axis):
        self.axesList.remove(axis)
        self.attributes[axis] = None
    
    def PreStateAll(self):
        self._log.debug("Entering PreStateAll")
        self.pmacEthOk = False
        try:
            pmacEthState = self.pmacEth.state()
        except PyTango.DevFailed, e:
            self._log.error("PreStateAll(): PmacEth DeviceProxy state command failed.")
        if pmacEthState == PyTango.DevState.ON:
            self.pmacEthOk = True
        self._log.debug("Leaving PreStateAll")
            
    def StateAll(self):
        """ Get State of all axes with just one command to the Pmac Controller. """
        self._log.debug("Entering StateAll")
        if not self.pmacEthOk: return
        try:
            motStateAns = self.pmacEth.command_inout("SendCtrlChar", "B")
        except PyTango.DevFailed, e:
            self._log.error("StateAll(): SendCtrlChar('B') command called on PmacEth DeviceProxy failed.")
            self.pmacEthOk = False
            return
        motStateBinArray = [map(int,s,len(s)*[16]) for s in motStateAns.split()]        

        try:
            csStateAns = self.pmacEth.command_inout("SendCtrlChar", "C")
        except PyTango.DevFailed, e:
            self._log.error("StateAll(): SendCtrlChar('C') command called on PmacEth DeviceProxy failed.")
            self.pmacEthOk = False           
            return
        csStateBinArray = [map(int,s,len(s)*[16]) for s in csStateAns.split()]
        
        for axis in self.axesList:
            #here we will work on reference to dictionary to save time in accessing it
            attributes = self.attributes[axis]
            motBinState = motStateBinArray[axis-1]
            #First Word
            attributes["MotorActivated"] = bool(motBinState[0] & 0x8)
            attributes["NegativeEndLimitSet"] = bool(motBinState[0] & 0x4) 
            attributes["PositiveEndLimitSet"] = bool(motBinState[0] & 0x2)
            attributes["ExtendedServoAlgorithmEnabled"] = bool(motBinState[0] & 0x1)
            
            attributes["AmplifierEnabled"] = bool(motBinState[1] & 0x8)
            attributes["OpenLoopMode"] = bool(motBinState[1] & 0x4)
            attributes["MoveTimerActive"] = bool(motBinState[1] & 0x2)
            attributes["IntegrationMode"] = bool(motBinState[1] & 0x1)
            
            attributes["DwellInProgress"] = bool(motBinState[2] & 0x8)
            attributes["DataBlockError"] = bool(motBinState[2] & 0x4)
            attributes["DesiredVelocityZero"] = bool(motBinState[2] & 0x2)
            attributes["AbortDeceleration"] = bool(motBinState[2] & 0x1)
            
            attributes["BlockRequest"] = bool(motBinState[3] & 0x8)
            attributes["HomeSearchInProgress"] = bool(motBinState[3] & 0x4)
            attributes["User-WrittenPhaseEnable"] = bool(motBinState[3] & 0x2)
            attributes["User-WrittenServoEnable"] = bool(motBinState[3] & 0x1)
            
            attributes["AlternateSource_Destination"] = bool(motBinState[4] & 0x8)
            attributes["PhasedMotor"] = bool(motBinState[4] & 0x4)
            attributes["FollowingOffsetMode"] = bool(motBinState[4] & 0x2)
            attributes["FollowingEnabled"] = bool(motBinState[4] & 0x1)
            
            attributes["ErrorTriger"] = bool(motBinState[5] & 0x8)
            attributes["SoftwarePositionCapture"] = bool(motBinState[5] & 0x4)
            attributes["IntegratorInVelocityLoop"] = bool(motBinState[5] & 0x2)
            attributes["AlternateCommand-OutputMode"] = bool(motBinState[5] & 0x1)
            #Second Word
            #We add one because these bits together hold a value equal to the Coordinate System nr minus one
            attributes["CoordinateSystem"] = motBinState[6] + 1
            
            attributes["CoordinateDefinition"] = self.translateCoordinateDefinition(motBinState[7])
             
            attributes["AssignedToCoordinateSystem"] = bool(motBinState[8] & 0x8)
            #Reserved for future use
            attributes["ForegroundInPosition"] = bool(motBinState[8] & 0x2)
            attributes["StoppedOnDesiredPositionLimit"] = bool(motBinState[8] & 0x1)
            
            
            attributes["StoppedOnPositionLimit"] = bool(motBinState[9] & 0x8)
            attributes["HomeComplete"] = bool(motBinState[9] & 0x4)
            attributes["PhasingSearch_ReadActive"] = bool(motBinState[9] & 0x2)
            attributes["PhasingReferenceError"] = bool(motBinState[9] & 0x1)
            
            attributes["TriggerMove"] = bool(motBinState[10] & 0x8)
            attributes["IntegratedFatalFollowingError"] = bool(motBinState[10] & 0x4)
            attributes["I2T_amplifierFaultError"] = bool(motBinState[10] & 0x2)
            attributes["BacklashDirectionFlag"] = bool(motBinState[10] & 0x1)

            attributes["AmplifierFaultError"] = bool(motBinState[11] & 0x8)
            attributes["FatalFollowingError"] = bool(motBinState[11] & 0x4)
            attributes["WarningFollowingError"] = bool(motBinState[11] & 0x2)
            attributes["InPosition"] = bool(motBinState[11] & 0x1)
                        
            csBinState = csStateBinArray[attributes["CoordinateSystem"]-1]
            self.attributes[axis]["MotionProgramRunning"] = bool(csBinState[5] & 0x1)
        self._log.debug("Leaving StateAll")
    
    def StateOne(self, axis):
        switchstate = 0
        if not self.pmacEthOk:
            state = PyTango.DevState.ALARM
            status = "Ethernet connection with TurboPmac failed. \n(Check if PmacEth DS is running and if its state is ON)"
        elif not self.attributes[axis]["MotorActivated"]:
            state = PyTango.DevState.FAULT
            status = "Motor is deactivated - it is not under Pmac control (Check Ix00 variable)."
        else:
            state = PyTango.DevState.MOVING
            #state = PyTango.DevState.ON
            status = "Motor is in MOVING state."
            #motion cases
            if self.attributes[axis]["InPosition"] and (not self.attributes[axis]["MotionProgramRunning"]):
                state = PyTango.DevState.ON
                status = "Motor is in ON state.\nMotor is stopped in position"
            else:
                if self.attributes[axis]["HomeSearchInProgress"]:
                    status += "\nHome search in progress."
                if self.attributes[axis]["MotionProgramRunning"]:
                    status = "\nMotor is used by active motion program."

            #amplifier fault cases
            if not self.attributes[axis]["AmplifierEnabled"]:
                state = PyTango.DevState.ALARM
                status = "Amplifier disabled."
                if self.attributes[axis]["AmplifierFaultError"]:
                    status += "\nAmplifier fault signal received."
                if self.attributes[axis]["FatalFollowingError"]:
                    status += "\nFatal Following / Integrated Following Error exceeded."
            #limits cases        
            if self.attributes[axis]["NegativeEndLimitSet"]:
                   state = PyTango.DevState.ALARM
                   status += "\nAt least one of the lower/upper switches is activated"
                   switchstate += 4
            if self.attributes[axis]["PositiveEndLimitSet"]:
                   state = PyTango.DevState.ALARM
                   status += "\nAt least one of the negative/positive limit is activated"
                   switchstate += 2
        return (state, status, switchstate)
    
    def PreReadAll(self):
        self._log.debug("Entering PreReadAll")
        self.positionMultiple = {}
        self._log.debug("Leaving PreReadAll")
    
    def ReadAll(self):
        self._log.debug("Entering ReadAll")
        try:
            motPosAns = self.pmacEth.command_inout("SendCtrlChar", "P")
        except PyTango.DevFailed, e:
            self._log.error("ReadAll(): SendCtrlChar('P') command called on PmacEth DeviceProxy failed. \nException: %s", e)
            raise
        motPosFloatArray = [float(s) for s in motPosAns.split()]
        for axis in self.axesList:
            self.positionMultiple[axis] = motPosFloatArray[axis-1]
        self._log.debug("Leaving ReadAll")
            
    def ReadOne(self, axis):
        self._log.debug("Entering ReadOne")
        self._log.debug("Leaving ReadOne")
        return self.positionMultiple[axis] / self.attributes[axis]["step_per_unit"]
    
    def PreStartAll(self):
        self._log.debug("Entering PreStartAll")
        self.startMultiple = {}
        self._log.debug("Leaving PreStartAll")

    def PreStartOne(self, axis, position):
        self._log.debug("Entering PreStartOne")
        self.startMultiple[axis] = position
        self._log.debug("Leaving PreStartOne")
        return True

    def StartOne(self, axis, position):
        pass
        
    def StartAll(self):
        for axis,position in self.startMultiple.items():
            position *= self.attributes[axis]["step_per_unit"]
            self.pmacEth.command_inout("JogToPos",[axis,position])
        
    def SetPar(self, axis, name, value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        if name.lower() == "velocity":
            pmacVelocity =  (value * self.attributes[axis]["step_per_unit"]) / 1000
            self._log.debug("setting velocity to: %f" % pmacVelocity)
            ivar = int("%d22" % axis)
            try:
                self.pmacEth.command_inout("SetIVariable", (float(ivar), float(pmacVelocity)))
            except PyTango.DevFailed, e:
                #self._log.error("SetPar(%d,%s,%s): SetIVariable(%d,%d) command called on PmacEth DeviceProxy failed. \nException: %s", (axis,name,value,ivar,pmacVelocity,e))
                self._log.error("SetPar(%d,%s,%s): SetIVariable(%d,%d) command called on PmacEth DeviceProxy failed.", axis, name, value, ivar, pmacVelocity)
                raise

        elif name.lower() == "acceleration" or name.lower() == "deceleration":
            #here we convert acceleration time from sec(Sardana standard) to msec(TurboPmac expected unit)  
            pmacAcceleration =  value * 1000
            self._log.debug("setting acceleration to: %f" % pmacAcceleration)
            ivar = int("%d20" % axis)
            try:
                self.pmacEth.command_inout("SetIVariable", (float(ivar), float(pmacAcceleration)))
            except PyTango.DevFailed, e:
                #self._log.error("SetPar(%d,%s,%s): SetIVariable(%d,%d) command called on PmacEth DeviceProxy failed. \nException: %s", (axis,name,value,ivar,pmacAcceleration,e))
                self._log.error("SetPar(%d,%s,%s): SetIVariable(%d,%d) command called on PmacEth DeviceProxy failed.", axis, name, value, ivar, pmacAcceleration)
                raise
        elif name.lower() == "step_per_unit":
            self.attributes[axis]["step_per_unit"] = float(value)
        elif name.lower() == "base_rate":
            self.attributes[axis]["base_rate"] = float(value)
        #@todo implement base_rate

    def GetPar(self, axis, name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        if name.lower() == "velocity":
            ivar = long("%d22" % axis)
            try:
                pmacVelocity = self.pmacEth.command_inout("GetIVariable", ivar)
            except PyTango.DevFailed, e:
                #self._log.error("GetPar(%d,%s,%s): GetIVariable(%d) command called on PmacEth DeviceProxy failed. \nException: %s", (axis,name,ivar,e))
                self._log.error("GetPar(%d,%s): GetIVariable(%d) command called on PmacEth DeviceProxy failed.", axis, name, ivar)
                raise
            #pmac velocity from xxx (returned by TurboPmac) to xxx(Sardana standard) conversion
            sardanaVelocity = (float(pmacVelocity) * 1000) / self.attributes[axis]["step_per_unit"]
            return sardanaVelocity
    
        elif name.lower() == "acceleration" or name.lower() == "deceleration":
                #pmac acceleration time from msec(returned by TurboPmac) to sec(Sardana standard)
            ivar = long("%d20" % axis)
            try:
                pmacAcceleration = self.pmacEth.command_inout("GetIVariable",ivar) 
            except PyTango.DevFailed, e:
                #self._log.error("GetPar(%d,%s): GetIVariable(%d) command called on PmacEth DeviceProxy failed. \nException: %s", (axis,name,ivar,e))
                self._log.error("GetPar(%d,%s): GetIVariable(%d) command called on PmacEth DeviceProxy failed.", axis, name, ivar)
                raise
            sardanaAcceleration = float(pmacAcceleration) / 1000
            return sardanaAcceleration

        elif name.lower() == "step_per_unit":
            return self.attributes[axis]["step_per_unit"]
            #@todo implement base_rate
        elif name.lower() == "base_rate":
            return self.attributes[axis]["base_rate"]
        else:
            return None

    def AbortOne(self, axis):
        if self.attributes[axis]["MotionProgramRunning"]:
            abortCmd = "&%da" % self.attributes[axis]["CoordinateSystem"]
            try:
                self.pmacEth.command_inout("OnlineCmd", abortCmd)
            except PyTango.DevFailed, e:
                #self._log.error("AbortOne(%d): OnlineCmd(%s) command called on PmacEth DeviceProxy failed. \nException: %s" %(abortCmd, e))
                self._log.error("AbortOne(%d): OnlineCmd(%s) command called on PmacEth DeviceProxy failed." % axis, abortCmd)
                raise
        else:    
            try:
                self.pmacEth.command_inout("JogStop",[axis])
            except PyTango.DevFailed, e:
                #self._log.error("AbortOne(%d): JogStop(%d) command called on PmacEth DeviceProxy failed. \nException: %s" % (axis, axis, e))
                self._log.error("AbortOne(%d): JogStop(%d) command called on PmacEth DeviceProxy failed." % axis, axis)
    
    def DefinePosition(self, axis, value):
        pass
    
    def GetExtraAttributePar(self, axis, name):
        """ Get Pmac axis particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        return self.attributes[axis][name]

    def SetExtraAttributePar(self, axis, name, value):
        """ Set Pmac axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        if name == "AmplifierEnabled":
            if value:
                self.pmacEth.command_inout("JogStop", [axis])
            else:
                self.pmacEth.command_inout("KillMotor", [axis])
        
    def SendToCtrl(self,cmd):
        """ Send custom native commands.
        @param string representing the command
        @return the result received
        """
        cmd_splitted = cmd.split()
        if len(cmd_splitted) == 1: 
            self.pmacEth.command_inout(cmd)
        else:
            if len(cmd_splitted) == 2:
                if cmd_splitted[0].lower() == "enableplc":
                    self.pmacEth.command_inout("enableplc",int(cmd_splitted[1]))
                if cmd_splitted[0].lower() =="getmvariable":
                    return str(self.pmacEth.command_inout("getmvariable",int(cmd_splitted[1])))
            elif len(cmd_splitted) > 2:
                if cmd_splitted[0].lower() == "setpvariable":
                    array = [float(cmd_splitted[i]) for i in range(1, len(cmd_splitted))]
                    self.pmacEth.command_inout("setpvariable", array)
                    
    def translateCoordinateDefinition(self, nr):
        if nr == 0:
            return "No definition"
        elif nr == 1:
            return "Assigned to A-axis"
        elif nr == 2:
            return "Assigned to B-axis"
        elif nr == 3:
            return "Assigned to C-axis"
        elif nr == 4:
            return "Assigned to UVW axes"
        elif nr == 7:
            return "Assigned to XYZ axes"
