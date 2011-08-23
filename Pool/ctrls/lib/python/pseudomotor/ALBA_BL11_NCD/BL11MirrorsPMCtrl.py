#!/usr/bin/env python
#############################################################################
##
## file :    BL11_NCD_mirrorCurvature.py
##
## description : 
##
## project :    Sardana/Pool/ctrls/PseudoMotors
##
## developers history: sblanch
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
from pool import PseudoMotorController

#FIXMEs: image of the controllers

class Bl11MirrorCurvature(PseudoMotorController):
    """Radius pseudo for mirror benders."""
    gender = "Curvature"
    model  = "BL11-NCD mirror curvature pseudomotor"
    organization = "CELLS - ALBA"
    image = "energy.png"#FIXME
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ("Radius",)
    motor_roles = ("UpStreamBender","DownStreamBender",)
    
    def __init__(self,inst,props):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        PseudoMotorController.__init__(self,inst,props)
        self.debug = False

    def calc_physical(self, index, pseudos):
        return 0

    def calc_pseudo(self, index, physicals):
        return 0

class Bl11MirrorAngle(PseudoMotorController):
    """Pseudo to convine two motors who have the same direction
       into two pseudos with this direction and the angle.
       In the case of the ncd mirrors is Z and pitch movements,
       and for the ncd vessel is X and roll movements"""
    gender = "Angle"
    model  = "BL11-NCD mirror angle pseudomotor"
    organization = "CELLS - ALBA"
    image = "energy.png"#FIXME
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ("Translation","Angle",)
    motor_roles = ("UpperMotor","DownerMotor",)
    
    def __init__(self,inst,props):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        PseudoMotorController.__init__(self,inst,props)
        self.debug = False

    def calc_physical(self, index, pseudos):
        return 0

    def calc_pseudo(self, index, physicals):
        return 0