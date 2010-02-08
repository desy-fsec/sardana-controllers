#!/usr/bin/env python2.5

#############################################################################
##
## file :    PmacLTPCtrl.py
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
from PmacCtrl import PmacController
from pool import MotorController

class PmacLTPController(PmacController):
    """This class is the Tango Sardana motor controller for the Pmac motor controller device in LTP."""

    def __init__(self,inst,props):
        PmacController.__init__(self,inst,props)

    def StateOne(self, axis):
        state = PyTango.DevState.ON
        switchstate = 0
        status = "No limits are active, motor is in position"
        if not bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d40" % axis))))):
               state = PyTango.DevState.MOVING
               status = '\nThe motor is moving'
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d21" % axis))))):
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the negative/positive limit is activated'
               switchstate += 2
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d22" % axis))))):
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the negative/positive limit is activated'
               switchstate += 4
        if not bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d39" % axis))))):
               state = PyTango.DevState.ALARM
               status = '''\nMotor's amplifier is not enabled'''
        return (state, status, switchstate)
