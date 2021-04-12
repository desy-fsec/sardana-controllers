#!/usr/bin/env python2.5

#############################################################################
#
# file :    PmacCtrl.py
#
# description :
#
# project :    miscellaneous/PoolControllers/MotorControllers
#
# developers history: zreszela
#
# copyleft :    Cells / Alba Synchrotron
#               Bellaterra
#               Spain
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
import math
import PyTango
import numpy as np
from sardana.pool.controller import Type, FSet, FGet, Access, Description, \
    DataAccess, DefaultValue
from TurboPmacCtrl import TurboPmacController


class DcmTurboPmacController(TurboPmacController):
    """
    This class is a Sardana motor controller for DCM of CLAESS beamline at
    ALBA.
    DCM comprises many motors, and two of them: Bragg and
    2ndXtalPerpendicular are controlled from TurboPmac Motor Controller
    """

    ctrl_attributes = {
        'MoveBraggOnly': {
            Type: bool,
            DefaultValue: False,
            Description: "Move only bragg, without perp",
            Access: DataAccess.ReadWrite,
            FGet: 'get_move_bragg',
            FSet: 'set_move_bragg'},
        # Implement solution to solve problem with motor group on sep6
        'UseqExafs': {
            Type: bool,
            DefaultValue: False,
            Description: "Flag to use the protection",
            Access: DataAccess.ReadWrite,
            FGet: 'get_use_qExafs',
            FSet: 'set_use_qExafs'},
        'NextPosition': {
            Type: [float, ],
            Description: "Values of bragg and perp",
            Access: DataAccess.ReadWrite,
            FGet: 'get_next_position',
            FSet: 'set_next_position'}
    }

    MaxDevice = 2

    def __init__(self, inst, props, *args, **kwargs):
        TurboPmacController.__init__(self, inst, props, *args, **kwargs)
        self.move_bragg_only = False
        self.user_qExafs = False
        self.next_position = []
        self.move_started = {1: False, 3: False}

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
        elif not self.move_started[axis]:
            state = PyTango.DevState.ON
            status = "Motor is in ON state.\nMotor is stopped in position"
        else:
            state = PyTango.DevState.MOVING
            # state = PyTango.DevState.ON
            status = "Motor is in MOVING state."
            # motion cases
            if self.move_started[axis] and \
                    self.attributes[axis]["ForegroundInPosition"] and \
                    (not self.attributes[axis]["MotionProgramRunning"]):
                state = PyTango.DevState.ON
                self.move_started[axis] = False
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
                    status += "\nFatal Following / Integrated Following " \
                              "Error exceeded."
            # limits cases
            if self.attributes[axis]["NegativeEndLimitSet"]:
                state = PyTango.DevState.ALARM
                status += "\nAt least one of the lower/upper switches is " \
                          "activated"
                switchstate += 4
            if self.attributes[axis]["PositiveEndLimitSet"]:
                state = PyTango.DevState.ALARM
                status += "\nAt least one of the negative/positive limit " \
                          "is activated"
                switchstate += 2
        return state, status, switchstate

    def StartAll(self):
        self._log.debug("Entering StartAll")
        # @todo: here we should use some extra_attribute of energy
        # pseudomotor saying if we want to do energy motion or single axis
        # motion, cause len(self.startMultiple) > 1 is true if we move a
        # MotorGroup(e.g. mv macro with bragg and perp)
        if len(self.startMultiple) > 1:
            bragg_deg = self.startMultiple[1]
            perp = self.startMultiple[3]
            self._log.info('StartAll bragg_deg: %r prep: %r' %
                           (bragg_deg, perp))

            # Workaround to avoid problems
            if self.user_qExafs and (self.next_position != []):
                try:
                    w_pos = (bragg_deg, perp)
                    np.testing.assert_almost_equal(w_pos,
                                                   self.next_position,
                                                   5)
                except Exception:
                    self._log.error('The positions set were wrong %r. '
                                    'Use backup position '
                                    '%r' % (w_pos, self.next_position))
                    bragg_deg, perp = self.next_position

            self.user_qExafs = False
            self.next_position = []

            bragg_rad = math.radians(bragg_deg)

            # we calculate exit offset form the current position of the
            # perpendicular motor, during energy motion program pmac will
            # try to keep this fixed
            exitOffset = 2 * perp * math.cos(bragg_rad)
            self.pmacEth.command_inout("SetPVariable", [100, bragg_deg])
            self.pmacEth.command_inout("SetPVariable", [101, exitOffset])
            program = 11
            if self.move_bragg_only:
                program = 12
            self.pmacEth.command_inout("RunMotionProg", program)
        else:
            super(DcmTurboPmacController, self).StartAll()
        for axis in self.startMultiple:
            self.move_started[axis] = True
        self._log.debug("Leaving StartAll")

    def set_move_bragg(self, value):
        self.move_bragg_only = value

    def get_move_bragg(self):
        return self.move_bragg_only

    def set_use_qExafs(self, value):
        self.user_qExafs = value

    def get_use_qExafs(self):
        return self.user_qExafs

    def set_next_position(self, value):
        self._log.info('Write NextPostion %r' % value)
        self.next_position = value

    def get_next_position(self):
        return self.next_position
