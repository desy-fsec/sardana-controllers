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
import math, logging, time
import PyTango
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import MotorController
import TurboPmacCtrl

class DcmTurboPmacController(TurboPmacCtrl.TurboPmacController):
    """This class is a Sardana motor controller for DCM of CLAESS beamline at ALBA.
        DCM comprises many motors, and two of them: Bragg and 2ndXtalPerpendicular are controlled
        from TurboPmac Motor Controller"""

    superklass = TurboPmacCtrl.TurboPmacController    
    MaxDevice = 2
    
    def __init__(self, inst, props, *args, **kwargs):
        self.superklass.__init__(self, inst, props, *args, **kwargs)

    def StateOne(self, axis):
        self._log.debug("Entering StateOne")
        attributes = self.attributes[axis]
        switchstate = 0
        if not self.pmacEthOk:
            state = PyTango.DevState.ALARM
            status = "Ethernet connection with TurboPmac failed. \n(Check if PmacEth DS is running and if its state is ON)"
        elif not attributes["MotorActivated"]:
            state = PyTango.DevState.FAULT
            status = "Motor is deactivated - it is not under Pmac control (Check Ix00 variable)."
        else:
            #motion cases           
            if attributes["MotionProgramRunning"]:
                state = PyTango.DevState.MOVING
                status = "Motor is used by active motion program."                
            elif not attributes["DesiredVelocityZero"]:
                state = PyTango.DevState.MOVING
                status = "Motor is moving."
            else:
                state = PyTango.DevState.ON
                status = "Motor is holding it's position."
            if state == PyTango.DevState.MOVING and attributes["HomeSearchInProgress"]:
                status += "Home search in progress."

            #amplifier fault cases
            if not attributes["AmplifierEnabled"]:
                state = PyTango.DevState.ALARM
                status = "Amplifier disabled."
                if attributes["AmplifierFaultError"]:
                    status += "\nAmplifier fault signal received."
                if attributes["FatalFollowingError"]:
                    status += "\nFatal Following / Integrated Following Error exceeded."
            #limits cases        
            if attributes["NegativeEndLimitSet"]:
                   state = PyTango.DevState.ALARM
                   status += "\nAt least one of the lower/upper switches is activated"
                   switchstate += 4
            if attributes["PositiveEndLimitSet"]:
                   state = PyTango.DevState.ALARM
                   status += "\nAt least one of the negative/positive limit is activated"
                   switchstate += 2
        self._log.debug("Leaving StateOne")
        return (state, status, switchstate)
       
    def StartAll(self):
        self._log.debug("Entering StartAll")
        #@todo: here we should use some extra_attribute of energy pseudomotor saying if we want to do energy motion or single axis motion, cause len(self.startMultiple) > 1 is true if we move a MotorGroup(e.g. mv macro with bragg and perp) 
        if len(self.startMultiple) > 1:
            bragg_deg = self.startMultiple[1]
            bragg_rad = math.radians(bragg_deg)
            perp = self.startMultiple[3]
            #we calculate exit offset form the current position of the perpendicular motor, during energy motion program pmac will try to keep this fixed
            exitOffset = 2 * perp * math.cos(bragg_rad)
            self._log.debug('Starting energy movement with bragg: %f, exitOffset: %f' %(bragg_deg,exitOffset))
            self.pmacEth.command_inout("SetPVariable", [100,bragg_deg])
            self.pmacEth.command_inout("SetPVariable", [101,exitOffset])
            self.pmacEth.command_inout("RunMotionProg", 11)
        else:
            self.superklass.StartAll(self)
        self._log.debug("Leaving StartAll")
