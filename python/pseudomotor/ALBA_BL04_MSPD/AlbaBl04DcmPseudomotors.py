#!/usr/bin/env python
#############################################################################
##
## file :    BL11_NCD_dcmEnergy.py
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
import logging, math
import PyTango
from pool import PseudoMotorController, PoolUtil

#Conversion Energy [keV] <-> wavelength lambda [Angstroem] :   lambda= 
#12.3984 / Energy

#Conversion dcm_bragg [deg] -lambda [Ang] : lamdba  = 
#2*d_Si111*sin(dcm_bragg) with d_Si111=3.135 [Ang]

#Relationship between dcm_bragg [deg] and dcm_t2  [mm] : dcm_t2= 
#Offset/2/cos(dcm_bragg) where Offset = 20 [mm]

#d = 3.135 # si111 [Ang]
NaN = float('nan')


class Energy(PseudoMotorController):
    """Energy pseudo motor controller for BL04-MSPD energy calculation
    """
    class_prop = {'exitOffset' : {'Type' : 'PyTango.DevDouble', 'Description' : 'Fixed exit offset'},
                  'mirrorPitchName' : {'Type' : 'PyTango.DevString', 'Description' : 'Name of the mirror pitch pseudomotor'},
                  'mirrorZName' : {'Type' : 'PyTango.DevString', 'Description' : 'Name of the mirror z pseudomotor'},
                  'mirrorZLimit' : {'Type' : 'PyTango.DevDouble', 'Description' : 'Limit for mirror z pseudomotor mirrored/unmirrored mode'}}

    ctrl_extra_attributes = {"dSpacing":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE"}}

    pseudo_motor_roles = ("energy",)
    motor_roles = ("bragg","t2")
    
    def __init__(self,inst,props):
        PseudoMotorController.__init__(self,inst,props)
        #self._log.setLevel(logging.DEBUG)

        self.attributes = {}
        self.attributes[1] = {'dspacing':3.135}

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        #bragg angle is called theta to distinguish with the bragg library
        mirror_z_mot = PoolUtil().get_motor(self.inst_name, self.mirrorZName)
        mirror_pitch_mot = PoolUtil().get_motor(self.inst_name, self.mirrorPitchName)
        energy, = pseudos #[keV]
        d = self.attributes[1]['dspacing']
        try:
            if mirror_z_mot.position < self.mirrorZLimit:
                bragg_rad = math.asin(12.3984/(2*d*energy))
                self._log.debug("bragg_rad %f",bragg_rad)
                t2 = self.exitOffset/2/math.cos(bragg_rad)
                self._log.debug("t2 %f",t2)
            else:
                mirror_pitch = mirror_pitch_mot.position
                mirror_pitch_rad = mirror_pitch/1000
                bragg_rad = math.asin(12.3984/(2*d*energy)) + 2*mirror_pitch_rad
                self._log.debug("bragg_rad %f",bragg_rad)
                t2 = self.exitOffset/2/math.cos(bragg_rad)
                self._log.debug("t2 %f",t2)
            bragg = math.degrees(bragg_rad)
            self._log.debug("bragg %f",bragg)
            return (bragg,t2)
        except Exception,e:
            self._log.error('calc_all_physical(): Exception %s'%(e))
            bragg = NaN
            t2 = NaN
        return (bragg,t2)
        return (0,0)
    def calc_all_pseudo(self, physicals):
        mirror_z_mot = PoolUtil().get_motor(self.inst_name, self.mirrorZName)
        mirror_pitch_mot = PoolUtil().get_motor(self.inst_name, self.mirrorPitchName)
        bragg,t2 = physicals
        d = self.attributes[1]['dspacing']
        try:       
            bragg_rad = math.radians(bragg)
            self._log.debug("bragg_rad %f",bragg_rad)
            if mirror_z_mot.position < self.mirrorZLimit:
                energy = 12.3984/(2*d*math.sin(bragg_rad))    
            else:
                mirror_pitch = mirror_pitch_mot.position
                mirror_pitch_rad = mirror_pitch/1000
                energy = 12.3984/(2*d*math.sin(bragg_rad-2*mirror_pitch_rad))    
            self._log.debug("energy %f",energy)
        except Exception,e:
            self._log.error('calc_all_pseudo(): Exception %s'%(e))
            energy = NaN
        return (energy,)
        return (0,)
    def GetExtraAttributePar(self, axis, name):
        """Get Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to get an extra attribute
        :param name: (string) attribute name to retrieve

        :return: value of the attribute
        """
        return self.attributes[axis][name.lower()]

    def SetExtraAttributePar(self, axis, name, value):
        """Set Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to set an extra attribute
        :param name: (string) attribute name to retrieve
        :param value: an extra attribute value to be set

        """
        self.attributes[axis][name.lower()] = value
