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
from pool import MotorController


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
    
    def __init__(self,inst,props):
        MotorController.__init__(self,inst,props)
        self.pmacEth = PyTango.DeviceProxy(self.PmacEthDevName)
        self.axesList = []
        self.startMultiple = {}
        self.positionMultiple = {}
        self.attributes = {}  

    def AddDevice(self, axis):
        self.axesList.append(axis)
        self.attributes[axis] = {}

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
        csStateBinArray = [bin(int(s,16)).lstrip("0b").rjust(64,"0") for s in csStateAns.split()]
        for axis in self.axesList:
            motBinState = motStateBinArray[axis-1]
            self._log.info("Mot %d binary state: %s", axis-1,motBinState)
            #First Word
            self.attributes[axis]["MotorActivated"] = bool(int(motBinState[0]))
            self.attributes[axis]["NegativeEndLimitSet"] = bool(int(motBinState[1])) 
            self.attributes[axis]["PositiveEndLimitSet"] = bool(int(motBinState[2]))
            self.attributes[axis]["ExtendedServoAlgorithmEnabled"] = bool(int(motBinState[3]))
            
            self.attributes[axis]["AmplifierEnabled"] = bool(int(motBinState[4]))
            self.attributes[axis]["OpenLoopMode"] = bool(int(motBinState[5]))
            self.attributes[axis]["MoveTimerActive"] = bool(int(motBinState[6]))
            self.attributes[axis]["IntegrationMode"] = bool(int(motBinState[7]))
            
            self.attributes[axis]["DwellInProgress"] = bool(int(motBinState[8]))
            self.attributes[axis]["DataBlockError"] = bool(int(motBinState[9]))
            self.attributes[axis]["DesiredVelocityZero"] = bool(int(motBinState[10]))
            self.attributes[axis]["AbortDeceleration"] = bool(int(motBinState[11]))
            
            self.attributes[axis]["BlockRequest"] = bool(int(motBinState[12]))
            self.attributes[axis]["HomeSearchInProgress"] = bool(int(motBinState[13]))
            self.attributes[axis]["User-WrittenPhaseEnable"] = bool(int(motBinState[14]))
            self.attributes[axis]["User-WrittenServoEnable"] = bool(int(motBinState[15]))
            
            self.attributes[axis]["AlternateSource_Destination"] = bool(int(motBinState[16]))
            self.attributes[axis]["PhasedMotor"] = bool(int(motBinState[17]))
            self.attributes[axis]["FollowingOffsetMode"] = bool(int(motBinState[18]))
            self.attributes[axis]["FollowingEnabled"] = bool(int(motBinState[19]))
            
            self.attributes[axis]["ErrorTriger"] = bool(int(motBinState[20]))
            self.attributes[axis]["SoftwarePositionCapture"] = bool(int(motBinState[21]))
            self.attributes[axis]["IntegratorInVelocityLoop"] = bool(int(motBinState[22]))
            self.attributes[axis]["AlternateCommand-OutputMode"] = bool(int(motBinState[23]))
            #Second Word
            #We add one because these bits together hold a value equal to the Coordinate System nr minus one
            self.attributes[axis]["CoordinateSystem"] = int(motBinState[24:28],2) + 1
            
            self.attributes[axis]["CoordinateDefinition"] = self.translateCoordinateDefinition(int(motBinState[28:32],2))
             
            self.attributes[axis]["AssignedToCoordinateSystem"] = bool(int(motBinState[33]))
            #Reserved for future use
            self.attributes[axis]["ForegroundInPosition"] = bool(int(motBinState[34]))
            self.attributes[axis]["StoppedOnDesiredPositionLimit"] = bool(int(motBinState[35]))
            
            
            self.attributes[axis]["StoppedOnPositionLimit"] = bool(int(motBinState[36]))
            self.attributes[axis]["HomeComplete"] = bool(int(motBinState[37]))
            self.attributes[axis]["PhasingSearch_ReadActive"] = bool(int(motBinState[38]))
            self.attributes[axis]["PhasingReferenceError"] = bool(int(motBinState[39]))
            
            self.attributes[axis]["TriggerMove"] = bool(int(motBinState[40]))
            self.attributes[axis]["IntegratedFatalFollowingError"] = bool(int(motBinState[41]))
            self.attributes[axis]["I2T_amplifierFaultError"] = bool(int(motBinState[42]))
            self.attributes[axis]["BacklashDirectionFlag"] = bool(int(motBinState[43]))

            self.attributes[axis]["AmplifierFaultError"] = bool(int(motBinState[44]))
            self.attributes[axis]["FatalFollowingError"] = bool(int(motBinState[45]))
            self.attributes[axis]["WarningFollowingError"] = bool(int(motBinState[46]))
            self.attributes[axis]["InPosition"] = bool(int(motBinState[47]))
                        
            csBinState = csStateBinArray[self.attributes[axis]["CoordinateSystem"]-1]
            self.attributes[axis]["MotionProgramRunning"] = bool(int(csBinState[23]))
    
    def StateOne(self, axis):
        switchstate = 0
        if not self.attributes[axis]["MotorActivated"]:
            state = PyTango.DevState.FAULT
            status = "Motor is deactivated - it is not under Pmac control (Check Ix00 variable)."
        else:
            state = PyTango.DevState.ON
            status = "Motor is in ON state."
            #motion cases
            if self.attributes[axis]["MotionProgramRunning"]:
                status = "Motor is used by active motion program."
                state = PyTango.DevState.MOVING
            elif self.attributes[axis]["InPosition"]:
                status = "Motor is stopped in position"
                state = PyTango.DevState.ON
            elif not self.attributes[axis]["DesiredVelocityZero"]:
                    state = PyTango.DevState.MOVING
                    status = "Motor is moving."
                    if self.attributes[axis]["HomeSearchInProgress"]:
                        status += "\nHome search in progress."
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
        try:
            if name.lower() == "velocity":
                self.pmacEth.command_inout("SetIVariable",(float("%d22" % axis), float(value)))
            elif name.lower() == "step_per_unit":
                self.attributes[axis]["step_per_unit"] = float(value)
            #@todo implement acceleration, base_rate
        except Exception,e:
            self._log.error('SetPar(%d,%s,%s).\nException:\n%s' % (axis,name,str(value),str(e)))
            raise

    def GetPar(self, axis, name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        try:
            if name.lower() == "velocity":
                return float(self.pmacEth.command_inout("GetIVariable",(long("%d22" % axis))))
            elif name.lower() == "step_per_unit":
                return self.attributes[axis]["step_per_unit"]
	    #@todo implement acceleration, base_rate
	    else:
		return None
        except Exception,e:
            self._log.error('GetPar(%d,%s).\nException:\n%s' % (axis,name,str(e)))
            raise

    def AbortOne(self, axis):
        if self.attributes[axis]["MotionProgramRunning"]:
            self.pmacEth.command_inout("OnlineCmd", "&%da" % self.attributes[axis]["CoordinateSystem"])
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