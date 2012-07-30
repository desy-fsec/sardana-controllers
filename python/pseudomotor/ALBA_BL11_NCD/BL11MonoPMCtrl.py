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

from math import sin,degrees,radians
import PyTango
from pool import PseudoMotorController

import bragg #FIXME: this comes from ALBA repository, needs to be shared
#TODO: generalize to more crystals than ncds'

Delta = 0.030 #m gap between crystals
NaN = float('nan')

class Bl11Energy(PseudoMotorController):
    """Energy pseudo motor controller for handling BL11-NCD energy calculation
       given the positions of all the motors involved (and viceversa).
       From: andreas.schacht at accel.de
       To: sergi.blanch at cells.es
       Date: 2009/03/24 15:00
       Subject: AW: documentation appendix of ranges and translations
       T2=d*sin(theta)/sin(2*theta)
       d is the offset (in your case 30 mm) and theta the Bragg angle in degrees
    """
    gender = "Energy"
    model  = "BL11-NCD energy pseudomotor"
    organization = "CELLS - ALBA"
    image = "energy.png"
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ("DcmEnergy",)
    motor_roles = ("Bragg","T2")
    
    def __init__(self,inst,props):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        PseudoMotorController.__init__(self,inst,props)
        self.debug = False

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        #bragg angle is called theta to distinguish with the bragg library
        energy = pseudos[0]
        try:
            #bragg.ener2angle(E, d=None, n=1 means Si_111)
            theta_radians = bragg.ener2angle(bragg.joules(energy*1000))
            theta = degrees(theta_radians)
            t2 = ((Delta*sin(theta_radians))/sin(2*theta_radians))*1000
            return (theta,t2,)
        except Exception,e:
            self._log.error('calc_all_physical(): Exception %s'%(e))
            return (NaN,NaN,)

    def calc_all_pseudo(self, physicals):
        #bragg angle is called theta to distinguish with the bragg library
        theta,t2 = physicals
        try:
            #bragg.angle2ener(scatangle, d=None, n=1):
            return (bragg.electronvolts(bragg.angle2ener(radians(theta)))/1000,)
        except Exception,e:
            self._log.error('calc_all_pseudo(): Exception %s'%(e))
            return (NaN,)

if __name__ == '__main__':
  # Just some unit tests of the computation
  dcmTest = Bl11Energy('test_name',{})
  dcmTest.name = 'test_name'
  braggRange = [ 0.0,
                 7.5,#e=15.1 keV
                 8.0,#e=14.2 keV
                 9.0,#e=12.6 keV
                10.0,#e=11.4 keV
                12.0,#e= 9.5 keV
                15.0,#e= 7.6 keV
                17.5,#e= 6.6 keV
                20.0,#e= 5.8 keV
                22.5,#e= 5.2 keV
                25.0,#e= 4.7 keV
                27.0,#e= 4.4 keV
                28.0,#e= 4.2 keV
                29.0,#e= 4.1 keV
                29.5,#e= 4.0 keV
                30.0]#e= 4.0 keV
  t2Range = [20]
  physicalsTest = [(i,j) for i in braggRange for j in t2Range]
  for test in physicalsTest:
      energy = dcmTest.calc_all_pseudo(test)
      theta,t2 = dcmTest.calc_all_physical(energy)
      print("bragg= %3.1f\tenergy= %3.1f\t theta=%3.1f\tt2=%4.2f"%(test[0],energy[0],theta,t2))

