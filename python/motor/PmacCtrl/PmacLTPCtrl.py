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
    
    ctrl_extra_attributes = dict(PmacController.ctrl_extra_attributes)
    ctrl_extra_attributes['FeedbackMode'] = {'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'}

    def __init__(self,inst,props):
        PmacController.__init__(self,inst,props)
        self._superklass = PmacController

    def StateOne(self, axis):
	#self._log.info("StateOne 1")
        state = PyTango.DevState.ON
        switchstate = 0
        status = "No limits are active, motor is in position"
        if not bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d40" % axis))))):
               #self._log.info("StateOne 2")
               state = PyTango.DevState.MOVING
               status = '\nThe motor is moving'
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d21" % axis))))):
               #self._log.info("StateOne 3")
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the negative/positive limit is activated'
               switchstate += 2
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d22" % axis))))):
               #self._log.info("StateOne 4")
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the negative/positive limit is activated'
               switchstate += 4
        if not bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d39" % axis))))):
               #self._log.info("StateOne 5")
               state = PyTango.DevState.ALARM
               status = '''\nMotor's amplifier is not enabled'''
        #self._log.info("StateOne 6")
        return (state, status, switchstate)

    def GetPar(self, axis, name):
        return self._superklass.GetPar(self, axis, name)    

    def GetExtraAttributePar(self, axis, name):
        """ Get Pmac axis particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        name = name.lower()
        if name == "feedbackmode":
            if axis == 1:
                i103value = self.pmacEth.command_inout("GetIVariable", int("%d03" % axis))
                try:
                    if int(i103value) == 13569:
                        return 1
                    elif int(i103value) == 13571:
                        return 2
                    else:
                        self._log.error("While getting feedback mode Pmac returned some inconsistent value, please report it to controls division.")
			PyTango.Except.throw_exception("Value error",
                                           "Pmac returned some inconsistent value, please report it to controls division.",
                                           "PmacLTPCtrl.GetExtraAttribute()")
                except ValueError:
                    self._log.error("While gettinh feedback mode Pmac returned some inconsistent value, please report it to controls division.")
                    PyTango.Except.throw_exception("Value error",
                                           "Pmac returned some inconsistent value, please report it to controls division.",
                                           "PmacLTPCtrl.GetExtraAttribute()")
            if axis == 2:
                self._log.warning("Various feedback mode feature is reserved only for top axis.")
		PyTango.Except.throw_exception("Value error",
                                           "Axis nr 2 does not support various feedback mode.",
                                           "PmacLTPCtrl.GetExtraAttribute()")
        else:
            return self._superklass.GetExtraAttributePar(self, axis, name)

    def SetExtraAttributePar(self, axis, name, value):
        """ Set Pmac axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        name = name.lower()
        if name == "feedbackmode":
            if axis == 1:
                if value == 1:
                    self.pmacEth.command_inout("SetIVariable",[int("%d03" % axis), 13569])
                elif value == 2:
                    self.pmacEth.command_inout("SetIVariable",[int("%d03" % axis), 13571])
                else:
                    self._log.warning("Feedback supports only two modes: use 1 for single feedback mode or 2 for dual feedback mode.")
                    PyTango.Except.throw_exception("Value error",
                                           "Wrong value, use 1 for single feedback mode or 2 for dual feedback mode.",
                                           "PmacLTPCtrl.SetExtraAttribute()")
            else:
                self._log.warning("Various feedback mode feature is reserved only for top axis.")
                PyTango.Except.throw_exception("Value error",
                                           "Axis nr 2 does not support various feedback mode.",
                                           "PmacLTPCtrl.SetExtraAttribute()")

                return
        else:
            self._superklass.SetExtraAttributePar(self, axis, name, value)
