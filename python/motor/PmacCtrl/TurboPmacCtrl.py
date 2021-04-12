#!/usr/bin/env python2.5

#############################################################################
#
# file :    PmacCtrl.py
#
# description :
#
# project :    miscellaneous/PoolControllers/MotorControllers
##
# developers history: zreszela
#
# copyleft :    Cells / Alba Synchrotron
# Bellaterra
# Spain
#
#############################################################################
#
# This file is part of Sardana.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################

import PyTango

from sardana.pool.controller import MotorController, Description, Type, \
    Access, DataAccess


class TurboPmacController(MotorController):
    """
    This class is the Tango Sardana motor controller for the Turbo Pmac motor
    controller device.
    """

    MaxDevice = 32
    class_prop = {
        'PmacEthDevName': {Type: str,
                           Description: 'Device name of the PmacEth DS'}
    }

    motor_extra_attributes = {  # First Word
        "MotorActivated": {Type: bool,
                           Access: DataAccess.ReadOnly},
        "NegativeEndLimitSet": {Type: bool,
                                Access: DataAccess.ReadOnly},
        "PositiveEndLimitSet": {Type: bool,
                                Access: DataAccess.ReadOnly},
        "ExtendedServoAlgorithmEnabled": {Type: bool,
                                          Access: DataAccess.ReadOnly},

        "AmplifierEnabled": {Type: bool,
                             Access: DataAccess.ReadWrite},
        "OpenLoopMode": {Type: bool,
                         Access: DataAccess.ReadOnly},
        "MoveTimerActive": {Type: bool,
                            Access: DataAccess.ReadOnly},
        "IntegrationMode": {Type: bool,
                            Access: DataAccess.ReadOnly},

        "DwellInProgress": {Type: bool,
                            Access: DataAccess.ReadOnly},
        "DataBlockError": {Type: bool,
                           Access: DataAccess.ReadOnly},
        "DesiredVelocityZero": {Type: bool,
                                Access: DataAccess.ReadOnly},
        "AbortDeceleration": {Type: bool,
                              Access: DataAccess.ReadOnly},

        "BlockRequest": {Type: bool,
                         Access: DataAccess.ReadOnly},
        "HomeSearchInProgress": {Type: bool,
                                 Access: DataAccess.ReadOnly},
        "User-WrittenPhaseEnable": {Type: bool,
                                    Access: DataAccess.ReadOnly},
        "User-WrittenServoEnable": {Type: bool,
                                    Access: DataAccess.ReadOnly},

        "AlternateSource_Destination": {Type: bool,
                                        Access: DataAccess.ReadOnly},
        "PhasedMotor": {Type: bool,
                        Access: DataAccess.ReadOnly},
        "FollowingOffsetMode": {Type: bool,
                                Access: DataAccess.ReadOnly},
        "FollowingEnabled": {Type: bool,
                             Access: DataAccess.ReadOnly},

        "ErrorTriger": {Type: bool,
                        Access: DataAccess.ReadOnly},
        "SoftwarePositionCapture": {Type: bool,
                                    Access: DataAccess.ReadOnly},
        "IntegratorInVelocityLoop": {Type: bool,
                                     Access: DataAccess.ReadOnly},
        "AlternateCommand-OutputMode": {Type: bool,
                                        Access: DataAccess.ReadOnly},
        # Second Word
        "CoordinateSystem": {Type: int,
                             Access: DataAccess.ReadOnly},

        "CoordinateDefinition": {Type: str,
                                 Access: DataAccess.ReadOnly},

        "AssignedToCoordinateSystem": {Type: bool,
                                       Access: DataAccess.ReadOnly},
        # Reserved for future use
        "ForegroundInPosition": {Type: bool,
                                 Access: DataAccess.ReadOnly},
        "StoppedOnDesiredPositionLimit": {Type: bool,
                                          Access: DataAccess.ReadOnly},

        "StoppedOnPositionLimit": {Type: bool,
                                   Access: DataAccess.ReadOnly},
        "HomeComplete": {Type: bool,
                         Access: DataAccess.ReadOnly},
        "PhasingSearch_ReadActive": {Type: bool,
                                     Access: DataAccess.ReadOnly},
        "PhasingReferenceError": {Type: bool,
                                  Access: DataAccess.ReadOnly},

        "TriggerMove": {Type: bool,
                        Access: DataAccess.ReadOnly},
        "IntegratedFatalFollowingError": {Type: bool,
                                          Access: DataAccess.ReadOnly},
        "I2T_amplifierFaultError": {Type: bool,
                                    Access: DataAccess.ReadOnly},
        "BacklashDirectionFlag": {Type: bool,
                                  Access: DataAccess.ReadOnly},

        "AmplifierFaultError": {Type: bool,
                                Access: DataAccess.ReadOnly},
        "FatalFollowingError": {Type: bool,
                                Access: DataAccess.ReadOnly},
        "WarningFollowingError": {Type: bool,
                                  Access: DataAccess.ReadOnly},
        "InPosition": {Type: bool,
                       Access: DataAccess.ReadOnly}}

    cs_extra_attributes = {
        "MotionProgramRunning": {Type: bool,
                                 Access: DataAccess.ReadOnly}
    }

    ctrl_extra_attributes = {}
    ctrl_extra_attributes.update(motor_extra_attributes)
    ctrl_extra_attributes.update(cs_extra_attributes)

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        try:
            self.pmacEth = PyTango.DeviceProxy(self.PmacEthDevName)
        except PyTango.DevFailed as e:
            self._log.error("__init__(): Could not create PmacEth device "
                            "proxy from %s device name. \nException: %s" %
                            (self.PmacEthDevName, e))
            raise
        self.axesList = []
        self.startMultiple = {}
        self.positionMultiple = {}
        self.attributes = {}

    def AddDevice(self, axis):
        self.axesList.append(axis)
        self.attributes[axis] = {
            "step_per_unit": 1.0, "base_rate": float("nan")}

    def DeleteDevice(self, axis):
        self.axesList.remove(axis)
        self.attributes[axis] = None

    def PreStateAll(self):
        self.pmacEthOk = False
        try:
            pmacEthState = self.pmacEth.state()
        except PyTango.DevFailed:
            self._log.error(
                "PreStateAll(): PmacEth DeviceProxy state command failed.")
        if pmacEthState == PyTango.DevState.ON:
            self.pmacEthOk = True

    def StateAll(self):
        """
        Get State of all axes with just one command to the Pmac Controller.
        """
        if not self.pmacEthOk:
            return
        try:
            motStateAns = self.pmacEth.command_inout("SendCtrlChar", "B")
        except PyTango.DevFailed:
            self._log.error("StateAll(): SendCtrlChar('B') command called on "
                            "PmacEth DeviceProxy failed.")
            self.pmacEthOk = False
            return
        motStateBinArray = [map(int, s, len(s) * [16])
                            for s in motStateAns.split()]

        try:
            csStateAns = self.pmacEth.command_inout("SendCtrlChar", "C")
        except PyTango.DevFailed:
            self._log.error("StateAll(): SendCtrlChar('C') command called on "
                            "PmacEth DeviceProxy failed.")
            self.pmacEthOk = False
            return
        csStateBinArray = [map(int, s, len(s) * [16])
                           for s in csStateAns.split()]

        for axis in self.axesList:
            # here we will work on reference to dictionary to save time in
            # accessing it
            attributes = self.attributes[axis]
            motBinState = motStateBinArray[axis - 1]
            # First Word
            attributes["MotorActivated"] = bool(motBinState[0] & 0x8)
            attributes["NegativeEndLimitSet"] = bool(motBinState[0] & 0x4)
            attributes["PositiveEndLimitSet"] = bool(motBinState[0] & 0x2)
            value = bool(motBinState[0] & 0x1)
            attributes["ExtendedServoAlgorithmEnabled"] = value

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

            attributes["AlternateSource_Destination"] = bool(motBinState[
                                                             4] & 0x8)
            attributes["PhasedMotor"] = bool(motBinState[4] & 0x4)
            attributes["FollowingOffsetMode"] = bool(motBinState[4] & 0x2)
            attributes["FollowingEnabled"] = bool(motBinState[4] & 0x1)

            attributes["ErrorTriger"] = bool(motBinState[5] & 0x8)
            attributes["SoftwarePositionCapture"] = bool(motBinState[5] & 0x4)
            attributes["IntegratorInVelocityLoop"] = bool(motBinState[5] & 0x2)
            value = bool(motBinState[5] & 0x1)
            attributes["AlternateCommand-OutputMode"] = value
            # Second Word
            # We add one because these bits together hold a value equal to the
            # Coordinate System nr minus one
            attributes["CoordinateSystem"] = motBinState[6] + 1
            value = self.translateCoordinateDefinition(motBinState[7])
            attributes["CoordinateDefinition"] = value

            value = bool(motBinState[8] & 0x8)
            attributes["AssignedToCoordinateSystem"] = value
            # Reserved for future use
            attributes["ForegroundInPosition"] = bool(motBinState[8] & 0x2)
            value = bool(motBinState[8] & 0x1)
            attributes["StoppedOnDesiredPositionLimit"] = value

            attributes["StoppedOnPositionLimit"] = bool(motBinState[9] & 0x8)
            attributes["HomeComplete"] = bool(motBinState[9] & 0x4)
            attributes["PhasingSearch_ReadActive"] = bool(motBinState[9] & 0x2)
            attributes["PhasingReferenceError"] = bool(motBinState[9] & 0x1)

            attributes["TriggerMove"] = bool(motBinState[10] & 0x8)
            value = bool(motBinState[10] & 0x4)
            attributes["IntegratedFatalFollowingError"] = value
            attributes["I2T_amplifierFaultError"] = bool(motBinState[10] & 0x2)
            attributes["BacklashDirectionFlag"] = bool(motBinState[10] & 0x1)

            attributes["AmplifierFaultError"] = bool(motBinState[11] & 0x8)
            attributes["FatalFollowingError"] = bool(motBinState[11] & 0x4)
            attributes["WarningFollowingError"] = bool(motBinState[11] & 0x2)
            attributes["InPosition"] = bool(motBinState[11] & 0x1)

            csBinState = csStateBinArray[attributes["CoordinateSystem"] - 1]
            value = bool(csBinState[5] & 0x1)
            self.attributes[axis]["MotionProgramRunning"] = value

    def StateOne(self, axis):
        switchstate = 0
        if not self.pmacEthOk:
            state = PyTango.DevState.ALARM
            status = "Ethernet connection with TurboPmac failed. \n(Check " \
                     "if PmacEth DS is running and if its state is ON)"
        elif not self.attributes[axis]["MotorActivated"]:
            state = PyTango.DevState.FAULT
            status = "Motor is deactivated - it is not under Pmac control (" \
                     "Check Ix00 variable)."
        else:
            state = PyTango.DevState.MOVING
            status = "Motor is in MOVING state."
            # motion cases
            if self.attributes[axis]["InPosition"] and (
                    not self.attributes[axis]["MotionProgramRunning"]):
                state = PyTango.DevState.ON
                status = "Motor is in ON state.\nMotor is stopped in position"
            else:
                if self.attributes[axis]["HomeSearchInProgress"]:
                    status += "\nHome search in progress."
                if self.attributes[axis]["MotionProgramRunning"]:
                    status = "\nMotor is used by active motion program."

            # amplifier fault cases
            if not self.attributes[axis]["AmplifierEnabled"]:
                state = PyTango.DevState.ALARM
                status = "Amplifier disabled."
                if self.attributes[axis]["AmplifierFaultError"]:
                    status += "\nAmplifier fault signal received."
                if self.attributes[axis]["FatalFollowingError"]:
                    status += "\nFatal Following/Integrated Following Error " \
                              "exceeded."
            # limits cases
            if self.attributes[axis]["NegativeEndLimitSet"]:
                state = PyTango.DevState.ALARM
                status += "\nAt least one of the lower/upper switches is " \
                          "activated"
                switchstate += 4
            if self.attributes[axis]["PositiveEndLimitSet"]:
                state = PyTango.DevState.ALARM
                status += "\nAt least one of the negative/positive limit is " \
                          "activated"
                switchstate += 2
        return state, status, switchstate

    def PreReadAll(self):
        self.positionMultiple = {}

    def ReadAll(self):
        try:
            motPosAns = self.pmacEth.command_inout("SendCtrlChar", "P")
        except PyTango.DevFailed as e:
            self._log.error("ReadAll(): SendCtrlChar('P') command called on "
                            "PmacEth DeviceProxy failed. \nException: %s", e)
            raise
        motPosFloatArray = [float(s) for s in motPosAns.split()]
        for axis in self.axesList:
            self.positionMultiple[axis] = motPosFloatArray[axis - 1]

    def ReadOne(self, axis):
        spu = self.attributes[axis]["step_per_unit"]
        return self.positionMultiple[axis] / spu

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
        for axis, position in self.startMultiple.items():
            position *= self.attributes[axis]["step_per_unit"]
            self.pmacEth.command_inout("JogToPos", [axis, position])

    def SetPar(self, axis, name, value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        if name.lower() == "velocity":
            pmacVelocity = (
                value * self.attributes[axis]["step_per_unit"]) / 1000
            self._log.debug("setting velocity to: %f" % pmacVelocity)
            ivar = int("%d22" % axis)
            try:
                self.pmacEth.command_inout(
                    "SetIVariable", (float(ivar), float(pmacVelocity)))
            except PyTango.DevFailed:
                self._log.error("SetPar(%d,%s,%s): SetIVariable(%d,"
                                "%d) command called on PmacEth DeviceProxy "
                                "failed.", axis, name, value, ivar,
                                pmacVelocity)
                raise

        elif name.lower() == "acceleration" or name.lower() == "deceleration":
            # here we convert acceleration time from sec(Sardana standard) to
            # msec(TurboPmac expected unit)
            pmacAcceleration = value * 1000
            self._log.debug("setting acceleration to: %f" % pmacAcceleration)
            ivar = int("%d20" % axis)
            try:
                self.pmacEth.command_inout(
                    "SetIVariable", (float(ivar), float(pmacAcceleration)))
            except PyTango.DevFailed:
                self._log.error("SetPar(%d,%s,%s): SetIVariable(%d,"
                                "%d) command called on PmacEth DeviceProxy "
                                "failed.", axis, name, value, ivar,
                                pmacAcceleration)
                raise
        elif name.lower() == "step_per_unit":
            self.attributes[axis]["step_per_unit"] = float(value)
        elif name.lower() == "base_rate":
            self.attributes[axis]["base_rate"] = float(value)
        # @todo implement base_rate

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
            except PyTango.DevFailed:
                self._log.error("GetPar(%d,%s): GetIVariable(%d) command "
                                "called on PmacEth DeviceProxy failed.",
                                axis, name, ivar)
                raise
            # pmac velocity from xxx (returned by TurboPmac) to xxx(Sardana
            # standard) conversion
            sardanaVelocity = (float(pmacVelocity) * 1000) / \
                self.attributes[axis]["step_per_unit"]
            return sardanaVelocity

        elif name.lower() == "acceleration" or name.lower() == "deceleration":
                # pmac acceleration time from msec(returned by TurboPmac) to
                # sec(Sardana standard)
            ivar = long("%d20" % axis)
            try:
                pmacAcceleration = self.pmacEth.command_inout(
                    "GetIVariable", ivar)
            except PyTango.DevFailed:
                self._log.error("GetPar(%d,%s): GetIVariable(%d) command "
                                "called on PmacEth DeviceProxy failed.",
                                axis, name, ivar)
                raise
            sardanaAcceleration = float(pmacAcceleration) / 1000
            return sardanaAcceleration

        elif name.lower() == "step_per_unit":
            return self.attributes[axis]["step_per_unit"]
            # @todo implement base_rate
        elif name.lower() == "base_rate":
            return self.attributes[axis]["base_rate"]
        else:
            return None

    def AbortOne(self, axis):
        if self.attributes[axis]["MotionProgramRunning"]:
            abortCmd = "&%da" % self.attributes[axis]["CoordinateSystem"]
            try:
                self.pmacEth.command_inout("OnlineCmd", abortCmd)
            except PyTango.DevFailed:
                self._log.error("AbortOne(%d): OnlineCmd(%s) command called "
                                "on PmacEth DeviceProxy failed." %
                                axis, abortCmd)
                raise
        else:
            try:
                self.pmacEth.command_inout("JogStop", [axis])
            except PyTango.DevFailed:
                self._log.error("AbortOne(%d): JogStop(%d) command called on "
                                "PmacEth DeviceProxy failed." %
                                axis, axis)

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

    def SendToCtrl(self, cmd):
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
                    self.pmacEth.command_inout(
                        "enableplc", int(cmd_splitted[1]))
                if cmd_splitted[0].lower() == "getmvariable":
                    return str(
                        self.pmacEth.command_inout(
                            "getmvariable", int(
                                cmd_splitted[1])))
            elif len(cmd_splitted) > 2:
                if cmd_splitted[0].lower() == "setpvariable":
                    array = [float(cmd_splitted[i])
                             for i in range(1, len(cmd_splitted))]
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
