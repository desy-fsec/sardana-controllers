#!/usr/bin/env python
#############################################################################
##
## file :    BeamEnergyPMCtrl.py
##
## description : Set of Energy Pseudomotor Controller to set energies
##               moving hardware at different levels: moncromator, insertion 
##               device and optics
##
## project :    Sardana/Pool/ctrls/PseudoMotors
##
## developers history: gjover
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
import numpy as np
from scipy.constants import physical_constants

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController

# User libraries
import undulator
import mono

# Units in mm, keV, s, degrees

class E_Bragg_PMController(PseudoMotorController):
    """ This controller provides E as a function of theta."""

    gender = "Energy"
    model  = "Energy pseudomotor"
    organization = "CELLS - ALBA"
    image = "energy.png"
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ('E',)
    motor_roles = ('Bragg',)

    # axis_attributes = {'dspacing':
    #                        {'Type':'PyTango.DevDouble',
    #                         'R/W Type':'PyTango.READ',
    #                         'Description':'D spacing in Amstrongs',
    #                         'DefaultValue':3.12542188}}
 
    class_prop = { 'mono_temp':{'Type':'PyTango.DevString',
                                'Description':'Device attribute model to read the temperaturea of the monocromator crystal',
                                'DefaultValue': None
                                },
                   # 'offset_phi':{'Type':'PyTango.DevDouble',
                   #              'Description':'Vertical inclination of the undulator x-ray beam (in rad).',
                   #              'DefaultValue':0.0
                   #       },
                   # 'offset_psi':{'Type':'PyTango.DevDouble',
                   #              'Description':'Horizontal inclination of the undulator x-ray beam (in rad).',
                   #              'DefaultValue':0.0
                   #       },
                   }
    
    def __init__(self, inst, prop, *args, **kwargs):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        PseudoMotorController.__init__(self, inst, prop, *args, **kwargs)

        for p in self.class_prop:
            if not prop.has_key(p):
                prop[p] = self.class_prop[p]['DefaultValue']

        self.prop = prop

        self.mono_temp = None
        if (self.prop["mono_temp"] is not None 
            and self.prop["mono_temp"] != "None"):
            self.mono_temp = PyTango.AttributeProxy(self.prop["mono_temp"])

        # Basic user methods check
        try:
            self._log.debug("mono.e_corr(12) = %f" % mono.e_corr(12))
            self._log.debug("mono.e_ucorr(12) = %f" % mono.e_ucorr(12))
            self._log.debug("mono.DELTA = %f" % mono.DELTA)
        except Exception, e:
            self._log.error('User libraries: Exception %s' % e)
            
    def CalcPhysical(self, index, pseudos, curr_physicals):
        return self.CalcAllPhysical(pseudos, curr_physicals)

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return self.CalcAllPseudo(physicals, curr_pseudos)

    def CalcAllPhysical(self, pseudos, curr_physicals):
        e_pm, = pseudos
        # Get uncorrected set value for the actual energy
        e_pm = mono.e_ucorr(e_pm)

        hcva = physical_constants[
            'inverse meter-electron volt relationship'][0]

        temp = None
        if self.mono_temp is not None:
            temp = self.mono_temp.read().value

        d = mono.d_spacing(temp)

        bragg = np.rad2deg(np.arcsin(hcva / (2 * d * e_pm)))
        return bragg

    def CalcAllPseudo(self, physicals, curr_pseudos):
        bragg, = physicals

        hcva = physical_constants[
            'inverse meter-electron volt relationship'][0]

        temp = None
        if self.mono_temp is not None:
            temp = self.mono_temp.read().value

        d = mono.d_spacing(temp)

        e_pm = hcva / (2 * d * np.sin(np.deg2rad(bragg)))
        # Get actual energy
        e_pm = mono.e_corr(e_pm)
        return e_pm

    def SetAxisExtraPar(self, axis, name, value):
        pass

    def GetAxisExtraPar(self, axis, name):
        # if name.lower() == 'dspacing':
        #     return self.calc_d_spacing_with_temp()
        pass


class E_BraggT2_PMController(E_Bragg_PMController):
    """Energy pseudo motor controller for energy calculation given 
       the bragg angle and T2 possition.
    
       T2=d*sin(theta)/sin(2*theta)
       d is the offset (in your case 30 mm) and theta the Bragg angle 
       in degrees
    """
    pseudo_motor_roles = ("E",)
    motor_roles = ("Bragg","T2",)

    def __init__(self, inst, prop, *args, **kwargs):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        E_Bragg_PMController.__init__(self, inst, prop, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        return self.CalcAllPhysical(pseudos, curr_physicals)[index-1]

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return self.CalcAllPseudo(physicals, curr_pseudos)

    def CalcAllPhysical(self, pseudos, curr_physicals):
        bragg = E_Bragg_PMController.CalcAllPhysical(self, pseudos, 
                                                      curr_physicals)
        t2 = ((mono.DELTA * np.sin(np.deg2rad(bragg)))
              / np.sin(2 * np.deg2rad(bragg)))
        return (bragg, t2)

    def CalcAllPseudo(self, physicals, curr_pseudos):
        bragg, t2 = physicals
        e_pm = E_Bragg_PMController.CalcAllPseudo(self, [bragg], curr_pseudos)
        self._log.debug("E_Bragg %f" % e_pm)
        return e_pm


class E_Egap_PMController(PseudoMotorController):
    """ This controller provides Eugap as a function of E and ugap."""

    gender = "Energy"
    model  = "Energy pseudomotor"
    organization = "CELLS - ALBA"
    image = "energy.png"
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ('Ep',)
    motor_roles = ('Ef','gap')

    axis_attributes = {'tune':{'Type':'PyTango.DevDouble',
                               'R/W Type':'PyTango.READ_WRITE',
                               'DefaultValue':0.5},
                       'harmonic':{'Type':'PyTango.DevLong',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'DefaultValue':7},
                       'harmonicAutoSet':{'Type':bool,
                                          'R/W Type':'PyTango.READ_WRITE',
                                          'DefaultValue':False},
                       }


    def __init__(self, inst, prop, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, prop, *args, **kwargs)
        self.tune = 0.5
        self.harmonic = 7
        self.harmonicAutoSet = False

        # Basic user methods check
        try:
            self._log.debug("undulator.gap(12) = %f %d" % undulator.gap(
                    12,
                    self.harmonic,
                    self.tune,
                    self.harmonicAutoSet))
        except Exception, e:
            self._log.error('User libraries: Exception %s' % e)

        
    def CalcPhysical(self, index, pseudos, curr_physicals):
        return self.CalcAllPhysical(pseudos, curr_physicals)[index-1]

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return self.CalcAllPseudo(physicals, curr_pseudos)

    def CalcAllPhysical(self, pseudos, curr_physicals):
        e_pm, = pseudos
        self._log.debug("physical E = %s" % str(e_pm))

        gap, harmonic = undulator.gap(e_pm, self.harmonic, self.tune, 
                                      self.harmonicAutoSet)
        self.harmonic = harmonic

        return (e_pm, gap)

    def CalcAllPseudo(self, physicals, curr_pseudos):
        e_pm, gap = physicals
        return e_pm

    def SetAxisExtraPar(self, axis, name, value):
        par = name.lower()
        if par == 'tune':
            self.tune = value
        elif par == 'harmonic':
            if 1 <= value <= 21:
                self.harmonic = value
            else:
                raise Exception('Not a valid harmonic between 1 and 21.')
        elif par == 'harmonicautoset':
            self.harmonicAutoSet = value

    def GetAxisExtraPar(self, axis, name):
        par = name.lower()
        if par == 'tune':
            return self.tune
        elif par == 'harmonic':
            return self.harmonic
        elif par == 'harmonicautoset':
            return self.harmonicAutoSet


class W_E_PMController(PseudoMotorController):
    """ This controller provides wavelength as a function of E."""

    gender = "Wavelength"
    model  = "Wavelength pseudomotor"
    organization = "CELLS - ALBA"
    image = "wave.png"
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ('wavelength',)
    motor_roles = ('E',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        w_pm, = pseudos

        hcva = physical_constants['inverse meter-electron volt relationship'][0]
        energy = hcva / w_pm
        return energy

    def CalcPseudo(self, index, physicals, curr_pseudos):
        energy, = physicals

        hcva = physical_constants['inverse meter-electron volt relationship'][0]
        w_pm = hcva/energy
        return w_pm


if __name__ == '__main__':

    hwbragg = 9.176
    hwt2 = 15.1945

    e_b_ctrl = E_Bragg_PMController('e_b',{})
    physicals = [hwbragg] # degrees
    energy = e_b_ctrl.CalcAllPseudo(physicals,[])
    bragg = e_b_ctrl.CalcAllPhysical([energy],[])
    print "E_Bragg_PMController", energy, bragg

    e_bt2_ctrl = E_BraggT2_PMController('e_bt',{})
    physicals = [hwbragg, hwt2] # degrees, mm
    energy = e_bt2_ctrl.CalcAllPseudo(physicals,[])
    bragg, t2 = e_bt2_ctrl.CalcAllPhysical([energy],[])
    print "E_BraggT2_PMController", energy, bragg, t2

    e_eg_ctrl = E_Egap_PMController('e_eg',{})
    e_eg_ctrl.SetAxisExtraPar(0, 'tune', 1)
    e_eg_ctrl.SetAxisExtraPar(0, 'harmonic', 3)
    e_eg_ctrl.SetAxisExtraPar(0, 'harmonicautoset', True)
    physicals = [12.4, 6000] # keV, um
    energy = e_eg_ctrl.CalcAllPseudo(physicals,[])
    e, gap = e_eg_ctrl.CalcAllPhysical([energy],[])
    print "E_Egap_PMController", energy, e, gap

