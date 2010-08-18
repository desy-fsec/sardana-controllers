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
import math
import PyTango
from pool import PoolUtil
from PmacCtrl import PmacController

class CLAESS_DCM_PmacController(PmacController):
    """This class is a Sardana motor controller for DCM of CLAESS beamline at ALBA.
        DCM comprises many motors, and two of them: Bragg and 2ndXtalPerpendicular are controlled
        from TurboPmac Motor Controller"""
        
    MaxDevice = 2
    class_prop = {'VCMPitchName':{'Type' : 'PyTango.DevBoolean', 'Description' : 'VCM pitch pseudomotor'}}
    class_prop.update(PmacController.class_prop)
    
    ctrl_extra_attributes = {"EnergyMotion":{ "Type":"PyTango.DevBool", "R/W Type": "PyTango.READ_WRITE"}}
    ctrl_extra_attributes.update(PmacController.ctrl_extra_attributes) 
    
    def __init__(self,inst,props):
        PmacController.__init__(self,inst,props)
        self.pmacEth = PyTango.DeviceProxy(self.DevName)
        self.vcm_pitch  = PoolUtil.get_motor(self, self.VCMPitchName)
        self.superklass = PmacController 
        
    def AddDevice(self, axis):
        self.superklass.AddDevice(self, axis)
        if axis == 1:
            self.attributes[axis]["EnergyMotion"]= bool(0)
            self.energyMotion = False

    def DeleteDevice(self, axis):
        pass
    
    def SetExtraAttributePar(self, axis, name, value):
        """ Set Pmac axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        
        if name == "EnergyMotion":
            if axis == 1:
                self.attributes[axis][name]=value
                self.energyMotion = value
            else:
                PyTango.Except.throw_exception("CLAESS_DCM_PmacController.SetExtraAttributePar()", "Error setting " + name + ", this attribute is foreseen only for Bragg motor", "SetExtraAttributePar()")
        else:
            self.superklass.SetExtraAttributePar(self, axis, name, value)
         
    
    def StartAll():
        if len(self.startMultiple) > 1:
            PyTango.Except.throw_exception("CLAESS_DCM_PmacController.StartAll()", 
                                           "Error trying to start motion, this controller doesn't allow to use motors by Sardana pseudomotors composed from more than one motor",
                                            "StartAll()")
        if self.energyMotion:
            vcm_pitch_mrad = self.vcm_pitch.read_attribute("Position")
            #@todo: replace formula for exitOffset
            exitOffset = 2,5 * vcm_pitch_mrad
            bragg = self.startMultiple[1]
            self.pmacEth.command_inout("SetPVariable", [100,bragg])
            self.pmacEth.command_inout("SetPVariable", [101,exitOffset])
            self.pmacEth.command_inout("RunMotionProgram", 1)
        else:
            self.superklass.StartAll()

