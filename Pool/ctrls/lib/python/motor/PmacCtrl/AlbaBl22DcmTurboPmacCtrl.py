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
from pool import PoolUtil, MotorController
import TurboPmacCtrl

class DcmTurboPmacController(TurboPmacCtrl.TurboPmacController):
    """This class is a Sardana motor controller for DCM of CLAESS beamline at ALBA.
        DCM comprises many motors, and two of them: Bragg and 2ndXtalPerpendicular are controlled
        from TurboPmac Motor Controller"""

    superklass = TurboPmacCtrl.TurboPmacController    
    MaxDevice = 2
    #class_prop = {'EnergyDeviceName':{'Type' : 'PyTango.DevString', 'Description' : 'Energy pseudomotor device name'}}
    #class_prop.update(superklass.class_prop)
    
    def __init__(self,inst,props):
        self.superklass.__init__(self,inst,props)
        #self._log.setLevel(logging.DEBUG)
        #self.energyPseudoMotor = PyTango.DeviceProxy(self.EnergyDeviceName) 
    
    def PreStartAll(self):
        self.startMultiple = {}

    def PreStartOne(self, axis, position):
        self.startMultiple[axis] = position
        return True

    def StartOne(self, axis, position):
        pass
       
    def StartAll(self):
        #@todo: here we should use some extra_attribute of energy pseudomotor saying if we want to do energy motion or single axis motion, cause len(self.startMultiple) > 1 is true if we move a MotorGroup(e.g. mv macro with bragg and perp) 
        if len(self.startMultiple) > 1:
            #@todo: this is only a workaroud, if we try to read an attribute from PseudoMotor it throws a serialization exception, to be fixed by tcoutinho. To use this workaround be sure that you set an ExitOffset attribute for energy pseudomotor at least one in it its lifetime
            #exitOffset = self.energyPseudoMotor.ExitOffset
            exitOffset = float(PyTango.Database().get_device_attribute_property('pm/dcm_energy_ctrl/1', "ExitOffset")["ExitOffset"]["__value"][0])
            bragg = self.startMultiple[1]
            self._log.debug('Starting energy movement with bragg: %f, exitOffset: %f' %(bragg,exitOffset))
            self.pmacEth.command_inout("SetPVariable", [100,bragg])
            self.pmacEth.command_inout("SetPVariable", [101,exitOffset])
            self.pmacEth.command_inout("RunMotionProg", 1)
            #self.pmacEth.command_inout("RunMotionProg", 11)
        else:
            self.superklass.StartAll(self)
