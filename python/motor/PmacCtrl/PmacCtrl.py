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
from sardana.pool.controller import MotorController



class PmacController(MotorController):
    """This class is the Tango Sardana motor controller for the Pmac motor controller device."""
    MaxDevice = 32
    class_prop = {'PmacEthDevName':{'Type' : 'PyTango.DevString', 'Description' : 'Device name of the PmacEth DS'}}
    attributeNames = ["motoractivated", "negativeendlimitset", "positiveendlimitset", "handwheelenabled",
                      "phasedmotor", "openloopmode", "runningdefine-timemove", "integrationmode",
                      "dwellinprogress", "datablockerror", "desiredvelocityzero", "abortdeceleration", 
                      "blockrequest", "homesearchinprogress", "assignedtocoordinatesystem","coordinatesystem", "amplifierenabled",
                      "stoppedonpositionlimit", "homecomplete", "phasingsearcherror", "triggermove",
                      "integratedfatalfollowingerror", "i2t_amplifierfaulterror", "backlashdirectionflag",
                      "amplifierfaulterror", "fatalfollowingerror", "warningfollowingerror", "inposition",
                      "motionprogramrunning"]
    
    motor_extra_attributes = {"MotorActivated":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "NegativeEndLimitSet":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "PositiveEndLimitSet":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "HandwheelEnabled":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "PhasedMotor":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "OpenLoopMode":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "RunningDefine-timeMove":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "IntegrationMode":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "DwellInProgress":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "DataBlockError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "DesiredVelocityZero":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "AbortDeceleration":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "BlockRequest":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "HomeSearchInProgress":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "AssignedToCoordinateSystem":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "CoordinateSystem":{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ'},
                             "AmplifierEnabled":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                             "StoppedOnPositionLimit":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "HomeComplete":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             "PhasingSearchError":{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
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
        MotorController.__init__(self, inst, props,  *args, **kwargs)
        self.pmacEth = PyTango.DeviceProxy(self.PmacEthDevName)
        self.axesList = []
        self.startMultiple = {}
        self.positionMultiple = {}
        self.attributes = {}  

    def AddDevice(self, axis):
        self._log.error("AddDevice entering...")
        self.axesList.append(axis)
        self.attributes[axis] = {"step_per_unit" : 1.0, "base_rate" : float("nan")}
        self._log.error("AddDevice leaving...")

    def DeleteDevice(self, axis):
        self.axesList.remove(axis)
        self.attributes[axis] = None
    
    def PreStateAll(self):
        for axis in self.axesList:
            self.attributes[axis] = {}
            
    def StateAll(self):
        """ Get State of all axes with just one command to the Pmac Controller. """
        motStateAns = self.pmacEth.command_inout("SendCtrlChar", "B")
        motStateBinArray = [bin(int(s,16)).lstrip("0b").rjust(48,"0") for s in motStateAns.split()]
        csStateAns = self.pmacEth.command_inout("SendCtrlChar", "C")
        csStateBinArray = [bin(int(s,16)).lstrip("0b").rjust(48,"0") for s in csStateAns.split()]
        for axis in self.axesList:
            motBinState = motStateBinArray[axis-1]
            #first word
            self.attributes[axis]["motoractivated"] = bool(int(motBinState[0]))
            self.attributes[axis]["negativeendlimitset"] = bool(int(motBinState[1])) 
            self.attributes[axis]["positiveendlimitset"] = bool(int(motBinState[2]))
            self.attributes[axis]["handwheelenabled"] = bool(int(motBinState[3]))
            self.attributes[axis]["phasedmotor"] = bool(int(motBinState[4]))
            self.attributes[axis]["openloopmode"] = bool(int(motBinState[5]))
            self.attributes[axis]["runningdefine-timemove"] = bool(int(motBinState[6]))
            self.attributes[axis]["integrationmode"] = bool(int(motBinState[7]))
            self.attributes[axis]["dwellinprogress"] = bool(int(motBinState[8]))
            self.attributes[axis]["datablockerror"] = bool(int(motBinState[9]))
            self.attributes[axis]["desiredvelocityzero"] = bool(int(motBinState[10]))
            self.attributes[axis]["abortdeceleration"] = bool(int(motBinState[11]))
            self.attributes[axis]["blockrequest"] = bool(int(motBinState[12]))
            self.attributes[axis]["homesearchinprogress"] = bool(int(motBinState[13]))
            #second word
            self.attributes[axis]["assignedtocoordinatesystem"] = bool(int(motBinState[24]))
            #We add one because these bits together hold a value equal to the Coordinate System nr minus one
            self.attributes[axis]["coordinatesystem"] = int(motBinState[25:28],2) + 1 
            self.attributes[axis]["amplifierenabled"] = bool(int(motBinState[33]))
            self.attributes[axis]["stoppedonpositionlimit"] = bool(int(motBinState[36]))
            self.attributes[axis]["homecomplete"] = bool(int(motBinState[37]))
            self.attributes[axis]["phasingsearcherror"] = bool(int(motBinState[39]))
            self.attributes[axis]["triggermove"] = bool(int(motBinState[40]))
            self.attributes[axis]["integratedfatalfollowingerror"] = bool(int(motBinState[41]))
            self.attributes[axis]["i2t_amplifierfaulterror"] = bool(int(motBinState[42]))
            self.attributes[axis]["backlashdirectionflag"] = bool(int(motBinState[43]))
            self.attributes[axis]["amplifierfaulterror"] = bool(int(motBinState[44]))
            self.attributes[axis]["fatalfollowingerror"] = bool(int(motBinState[45]))
            self.attributes[axis]["warningfollowingerror"] = bool(int(motBinState[46]))
            self.attributes[axis]["inposition"] = bool(int(motBinState[47]))
            
            csBinState = csStateBinArray[self.attributes[axis]["coordinatesystem"]-1]
            self.attributes[axis]["motionprogramrunning"] = bool(int(csBinState[23]))
    
    def StateOne(self, axis):
        switchstate = 0
        if not self.attributes[axis]["motoractivated"]:
            state = PyTango.DevState.FAULT
            status = "Motor is deactivated - it is not under Pmac control (Check Ix00 variable)."
        else:
            state = PyTango.DevState.ON
            status = "Motor is in ON state."
            #motion cases
            if self.attributes[axis]["motionprogramrunning"]:
                status = "Motor is used by active motion program."
                state = PyTango.DevState.MOVING
            elif self.attributes[axis]["inposition"]:
                status = "Motor is stopped in position"
                state = PyTango.DevState.ON
            elif not self.attributes[axis]["desiredvelocityzero"]:
                    state = PyTango.DevState.MOVING
                    status = "Motor is moving."
                    if self.attributes[axis]["homesearchinprogress"]:
                        status += "\nHome search in progress."
            #amplifier fault cases
            if not self.attributes[axis]["amplifierenabled"]:
                state = PyTango.DevState.ALARM
                status = "Amplifier disabled."
                if self.attributes[axis]["amplifierfaulterror"]:
                    status += "\nAmplifier fault signal received."
                if self.attributes[axis]["fatalfollowingerror"]:
                    status += "\nFatal Following / Integrated Following Error exceeded."
            #limits cases        
            if self.attributes[axis]["negativeendlimitset"]:
                   state = PyTango.DevState.ALARM
                   status += "\nAt least one of the lower/upper switches is activated"
                   switchstate += 2
            if self.attributes[axis]["positiveendlimitset"]:
                   state = PyTango.DevState.ALARM
                   status += "\nAt least one of the negative/positive limit is activated"
                   switchstate += 4
        return (state, status, switchstate)
    
    def PreReadAll(self):
        self.positionMultiple = {}
    
    def ReadAll(self):
        motPosAns = self.pmacEth.command_inout("SendCtrlChar", "P")
        motPosFloatArray = [float(s) for s in motPosAns.split()]
        for axis in self.axesList:
            self.positionMultiple[axis] = motPosFloatArray[axis-1]
            
    def ReadOne(self, axis):
        return self.positionMultiple[axis]
    
    def PreStartAll(self):
        self.startMultiple = {}

    def PreStartOne(self, axis, position):
        self.startMultiple[axis] = position
        return True

    def StartOne(self, axis, position):
    	pass
        
    def StartAll(self):
        for axis,position in self.startMultiple.items():
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
        if self.attributes[axis]["motionprogramrunning"]:
            self.pmacEth.command_inout("OnlineCmd", "&%da" % self.attributes[axis]["coordinatesystem"])
        else:    
            self.pmacEth.command_inout("JogStop",[axis])
    
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
        name = name.lower()
        if name == "amplifierenabled":
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

