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
from pool import PseudoMotorController

#Conversion Energy [keV] <-> wavelength lambda [Angstroem] :   lambda= 
#12.3984 / Energy

#Conversion dcm_bragg [deg] -lambda [Ang] : lamdba  = 
#2*d_Si111*sin(dcm_bragg) with d_Si111=3.135 [Ang]

#Relationship between dcm_bragg [deg] and dcm_t2  [mm] : dcm_t2= 
#Offset/2/cos(dcm_bragg) where Offset = 20 [mm]

d = 3.135 # si111 [Ang]
NaN = float('nan')


class Energy(PseudoMotorController):
    """Energy pseudo motor controller for BL04-MSPD energy calculation
    """
    class_prop = {'exitOffset' : {'Type' : 'PyTango.DevDouble', 'Description' : 'Fixed exit offset'}}
    
    pseudo_motor_roles = ("energy",)
    motor_roles = ("bragg","t2")
    
    def __init__(self,inst,props):
        PseudoMotorController.__init__(self,inst,props)
        #self._log.setLevel(logging.DEBUG)

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        #bragg angle is called theta to distinguish with the bragg library
        energy, = pseudos #[keV]
        try:
            bragg_rad = math.asin(12.3984/(2*d*energy))
            self._log.debug("bragg_rad %f",bragg_rad)
            bragg = math.degrees(bragg_rad)
            self._log.debug("bragg %f",bragg)
            t2 = self.exitOffset/2/math.cos(bragg_rad)
            self._log.debug("t2 %f",t2)
            return (bragg,t2)
        except Exception,e:
            self._log.error('calc_all_physical(): Exception %s'%(e))
            bragg = NaN
            t2 = NaN
        return (bragg,t2)

    def calc_all_pseudo(self, physicals):
        bragg,t2 = physicals
        try:       
            bragg_rad = math.radians(bragg)
            self._log.debug("bragg_rad %f",bragg_rad)
            energy = 12.3984/(2*d*math.sin(bragg_rad))    
            self._log.debug("energy %f",energy)
        except Exception,e:
            self._log.error('calc_all_pseudo(): Exception %s'%(e))
            energy = NaN
        return (energy,)


