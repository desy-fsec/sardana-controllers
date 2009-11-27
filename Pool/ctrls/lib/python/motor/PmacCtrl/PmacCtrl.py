#!/usr/bin/env python2.5

#############################################################################
##
## file :    PCctrl.py
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


class PMACController(MotorController):
    """This class is the Tango Sardana motor controller for the Pmac motor controller device."""

    class_prop = {'DevName':{'Description' : 'Device name of the PmacEth DS','Type' : 'PyTango.DevString'}}

    MaxDevice = 1

    def __init__(self,inst,props):
        MotorController.__init__(self,inst,props)
        self.pmacEth = PyTango.DeviceProxy(self.DevName)

    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass

    def StateOne(self, axis):
        self._log.info('RETURNING THE STATE OF AXIS %d'%axis)
        state = PyTango.DevState.ON
        switchstate = 0
        status = "No limits are active, motor is in position"
        if not bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d40" % axis))))):
               state = PyTango.DevState.MOVING
               status = '\nThe motor is moving'
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d21" % axis))))):
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the lower/upper switches is activated'
               switchstate += 4
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d22" % axis))))):
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the negative/positive limit is activated'
               switchstate += 2
        return (state, status, switchstate)

    def ReadOne(self, axis):
        self._log.info('Returning the current position for axis %d'%axis)
        position = self.pmacEth.command_inout("GetMotorPos",(axis))
        self._log.info('POSITION: %s'%position)
        return float(position)

    def StartOne(self, axis, position):
        self._log.info('Moving the axis %d to position %d'%(axis, position))
        self.pmacEth.command_inout("JogToPos",[axis,position])

    def SetPar(self, axis, parname, parvalue):
        pass

    def GetPar(self, axis, parname):
        return 0

    def GetExtraAttributePar(self, axis, attr_name):
        return 0

    def SetExtraAttributePar(self, axis, attr_name, value):
        pass

    def AbortOne(self, axis):
        self._log.info('Stopping the movement of axis %d'%axis)
        self.pmacEth.command_inout("JogStop",[axis])
    
    def DefinePosition(self,powerConverter, current):
        pass