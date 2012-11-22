import math
import taurus

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController

from scipy.constants import physical_constants

import undulator
import mono

class MonoEnergyEPMController(PseudoMotorController):
    """ This controller provides E as a function of theta."""

    pseudo_motor_roles = ('E',)
    motor_roles = ('theta',)

    axis_attributes = {'dspacing':
                           {'Type':'PyTango.DevDouble',
                            'R/W Type':'PyTango.READ',
                            'DefaultValue':3.12542188}}

    #class_prop = { 'temp_tgattr':{'Type':'PyTango.DevString', 'Description':'TangoAttribute for temperature d-spacing fine tuning'},
    #               'phi_0_tgattr':{'Type':'PyTango.DevString', 'Description':'TangoAttribute for temperature d-spacing fine tuning'},
    #               'psi_0_tgattr':{'Type':'PyTango.DevString', 'Description':'TangoAttribute for temperature d-spacing fine tuning'}}


    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

        ## Check properties
        #if not hasattr(self, 'temp_tgattr'):
        #    self.temp_tgattr = None
        #if not hasattr(self, 'phi_0_tgattr'):
        #    self.phi_0_tgattr = 0
        #if not hasattr(self, 'psi_0_tgattr'):
        #    self.psi_0_tgattr = 0

        # Vertical inclination of the undulator x-ray beam (in urad)
        self.phi_0 = 0
        # Horizontal inclination of the undulator x-ray beam (in urad).
        self.psi_0 = 0

    def CalcPhysical(self, index, pseudos, curr_physicals):
        e_pm, = pseudos

        # 120506 Take into account energy calibration
        e_pm = mono.Ecorr(e_pm, 'mono')

        hcva = physical_constants['inverse meter-electron volt relationship'][0]*1e7
        wavelength_pm = hcva/e_pm
        phi_0_rad = self.phi_0 * 1e6

        d = self.calc_d_spacing_with_temp()

        theta_minus_phi_0_rad = math.asin(wavelength_pm/(2 * d))
        theta_rad = theta_minus_phi_0_rad + phi_0_rad
        theta = theta_rad * (180/math.pi)

        return theta

    def CalcPseudo(self, index, physicals, curr_pseudos):
        theta, = physicals

        hcva = physical_constants['inverse meter-electron volt relationship'][0]*1e7
        d = self.calc_d_spacing_with_temp()
        theta_rad = theta * (math.pi/180)
        phi_0_rad = self.phi_0 * 1e6
        wavelength_pm = 2 * d * math.sin(theta_rad - phi_0_rad)
        e_pm = hcva / wavelength_pm

        # 120506 Take into account energy calibration
        e_pm = mono.Ecorr(e_pm, 'absolute')
        return e_pm

    def SetAxisExtraPar(self, axis, name, value):
        pass

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == 'dspacing':
            return self.calc_d_spacing_with_temp()

    def calc_d_spacing_with_temp(self):
        #fake_temp = 273.15
        mono_temp_C = taurus.Attribute("bl13/ct/eps-plc-01/mono_T4").read().value
        mono_temp_K = mono_temp_C + 273.15
        d = mono.d_spacing(mono_temp_K)
        return d


class MonoEnergyWavelengthPMController(PseudoMotorController):
    """ This controller provides wavelength as a function of E."""

    pseudo_motor_roles = ('wavelength',)
    motor_roles = ('E',)

    def __init__(self, inst, props):
        PseudoMotorController.__init__(self, inst, props)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        wavelength_pm, = pseudos

        hcva = physical_constants['inverse meter-electron volt relationship'][0]*1e7
        e_pm = hcva / wavelength_pm
        return e_pm

    def CalcPseudo(self, index, physicals, curr_pseudos):
        e, = physicals

        hcva = physical_constants['inverse meter-electron volt relationship'][0]*1e7
        wavelength_pm = hcva/e
        return wavelength_pm



class MonoEugapPMController(PseudoMotorController):
    """ This controller provides Eugap as a function of E and ugap."""

    pseudo_motor_roles = ('Eugap',)
    motor_roles = ('E','ugap')

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


    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.tune = 0.5
        self.harmonic = 7
        self.harmonicAutoSet = False
        
    def CalcPhysical(self, index, pseudos, curr_physicals):
        Eugap, = pseudos
        # New version of the library allows automatic change of the harmonic
        # Taking care of the new axis attribute harmonicAutoSet
        harmonic = self.harmonic
        if self.harmonicAutoSet:
            harmonic = -1
        ugap, new_harmonic = undulator.getugap(Eugap, harmonic, self.tune)
        self.harmonic = new_harmonic
        if index == 1:
            return Eugap
        elif index == 2:
            return ugap

    def CalcPseudo(self, index, physicals, curr_pseudos):
        E, ugap = physicals
        return E

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



class PitStrokePMController(PseudoMotorController):

    pseudo_motor_roles = ('pitang',)
    motor_roles = ('pitstroke',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        pitang, = pseudos

        pitstroke = pitang / (0.106028 * 1000)
        return pitstroke

    def CalcPseudo(self, index, physicals, curr_pseudos):
        pitstroke, = physicals

        pitang = 0.106028 * pitstroke * 1000
        return pitang


class FaPitStrokePMController(PseudoMotorController):

    pseudo_motor_roles = ('fapitang',)
    motor_roles = ('fapitstroke',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        fapitang, = pseudos

        fapitstroke = fapitang / 0.106028
        return fapitstroke

    def CalcPseudo(self, index, physicals, curr_pseudos):
        fapitstroke, = physicals

        fapitang = 0.106028 * fapitstroke
        return fapitang

if __name__ == '__main__':
    """ Jordi unit tests info:
        5 keV ~ 23 deg
        12.4 keV ~ 9 deg
        21k eV - 22 keV ~ 5 deg

        Regarding wavelength, 12.658 keV should correspond to 0.979 A
        This is OK, in calc_all_pseudo: e = 12.39841 / wavelength_pm
        
    """
    pass
    egy_ctrl = MonoEnergyEPMController('a_name', {})
    egy_ctrl.name = 'a_name'
    
    tests = [(5, 23), (12.4, 9), (21, 5)]
 
    for test in tests:
        bragg, e = test
 
        calc_bragg = egy_ctrl.CalcAllPhysical([e],[bragg])
        calc_e = egy_ctrl.CalcAllPseudo([bragg],[e])
 

        print '\n',test,'->',calc_bragg,',',calc_e,'\n'
