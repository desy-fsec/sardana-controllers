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
from TurboPmacCtrl import TurboPmacController
from pool import MotorController

class LtpTurboPmacController(TurboPmacController):
    """This class is the Tango Sardana motor controller for the Turbo Pmac motor controller device in LTP."""
    
    MaxDevice = 2

    ctrl_extra_attributes = dict(TurboPmacController.ctrl_extra_attributes)
    ctrl_extra_attributes['FeedbackMode'] = {'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'}

    def __init__(self,inst,props):
        TurboPmacController.__init__(self, inst, props)
	self.superklass = TurboPmacController    

    def GetExtraAttributePar(self, axis, name):
        """ Get Pmac axis particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        if name == "FeedbackMode":
            if axis == 1:
                mode = self.pmacEth.command_inout("OnlineCmd", "I103")
		if mode == "$3501":
		    return 1
		elif mode == "$3503":
		    return 2
		else:
		    self._log.error("While getting feedback mode TurboPmac returned some inconsistent value, please report it to controls division.")
		    PyTango.Except.throw_exception("Value error",
					"TurboPmac returned some inconsistent value, please report it to controls division.",
					"LtpTurboPmacController.GetExtraAttribute()")
            if axis == 2:
                self._log.warning("Various feedback mode feature is reserved only for top axis.")
		PyTango.Except.throw_exception("Value error",
                                           "Axis nr 2 does not support various feedback mode.",
                                           "LtpTurboPmacController.GetExtraAttribute()")
        else:
            return self.superklass.GetExtraAttributePar(self, axis, name)

    def SetExtraAttributePar(self, axis, name, value):
        """ Set Pmac axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        if name == "FeedbackMode":
            if axis == 1:
                if value == 1:
                    self.pmacEth.command_inout("OnlineCmd","I103=$3501")
                elif value == 2:
                    self.pmacEth.command_inout("OnlineCmd","I103=$3503")
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
            self.superklass.SetExtraAttributePar(self, axis, name, value)
