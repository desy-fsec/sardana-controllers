import math, logging

import PyTango
from sardana import pool 
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController

#def siliconBondLength(ior_value):
    #"""Returns silicon bond length depending on the ior_value parameter. 
       #Allowed values for ior_value parameter are: 311, 1111. When receives other value raise
       #ValueError exception. 

       #:param ior_value: (int) representing silicon type, 311 coresponds to si311 and 111 do si111

       #:return: (float) silicon bond length in Angstroms units (1e-10m) """

    #if ior_value == 311:
        #return 1.637418 #Angstroms
    #elif ior_value == 111:
        #return 3.1354161 #Angstroms
    #else:
        #raise ValueError("Wrong ior value")

class DCM_Energy_Controller(PseudoMotorController):
    """This pseudomotor controller does the calculation of Bragg
    and 2nd Xtal perpendicular position according to desired energy in eV.
    It works only with ClaesDcmTurboPmacCtrl motors"""
    
    pseudo_motor_roles = ('energy',)
    motor_roles = ('bragg', 'perp')
    
    class_prop = { 'VCMPitchName':{'Type' : 'PyTango.DevString', 'Description' : 'VCM_pitch pseudomotor'},
                   'DCMCrystalIORName' :{'Type' : 'PyTango.DevString', 'Description' : 'DCM_crystal IOR'}}
   
    ctrl_extra_attributes = {"ExitOffset":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE"},
                             "dSi111":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE"},
                             "dSi311":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE"}}
     
    hc = 12398.419 #eV *Angstroms
                             
    def __init__(self, inst, props, *args, **kwargs):    
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.attributes = {}
        self.attributes[1] = {'ExitOffset':18.5, 'dSi311':1.637418, 'dSi111':3.1354161}
        try:
            self.vcm_pitch = PoolUtil().get_motor(self.inst_name, self.VCMPitchName)
        except Exception, e:
            self._log.debug("Couldn't create DeviceProxy for %s motor." % self.VCMPitchName, exc_info=1)
            raise e

        try:
            self.dcm_crystal = PoolUtil().get_ioregister(self.inst_name, self.DCMCrystalIORName)
        except Exception, e:
            self._log.debug("Couldn't create DeviceProxy for %s ior." % self.DCMCrystalIORName)
            raise e

    def calc_physical(self, index, pseudos):
        self._log.debug("Entering calc_physical")
        ret = self.calc_all_physical(pseudos)[index - 1]
        self._log.debug("Leaving calc_physical")
        return ret
    
    def calc_pseudo(self, index, physicals):
        self._log.debug("Entering calc_pseudo")
        ret = self.calc_all_pseudo(physicals)[index - 1]
        self._log.debug("Leaving calc_pseudo")
        return ret
    
    def calc_all_physical(self, pseudos):
        self._log.debug("Entering calc_all_physical")
        energy, = pseudos

        try:
            vcm_pitch_mrad = self.vcm_pitch.Position
        except PyTango.DevFailed, e:
            self._log.debug("Couldn't read %s motor position." % self.VCMPitchName)
            raise e
        vcm_pitch_rad = vcm_pitch_mrad / 1000
        self._log.debug("       VCM pitch: %f rad." % vcm_pitch_rad)

        try:
            crystal_ior = self.dcm_crystal.Value
            d = self.siliconBondLength(crystal_ior)
        except PyTango.DevFailed, e:
            self._log.debug("Couldn't read %s ior value." % self.DCMCrystalIORName)
            raise e
        self._log.debug("       d: %f Angstroms." % d)
        
        try:
            bragg_rad = math.asin(self.hc/2/d/energy) + 2 * vcm_pitch_rad
        except ZeroDivisionError,e:
            bragg_rad = float('nan')
        bragg_deg = math.degrees(bragg_rad)
        
        try: 
            exitOffset = self.attributes[1]["ExitOffset"]
            #@todo also include P178 - perp axis offset for fixed exit move
            #                   P179 - crystal separation offset
            #to calculate perp position
            perp = exitOffset/2/math.cos(bragg_rad) #mm
        except ZeroDivisionError,e:
            perp = float('nan')
        self._log.debug("Leaving calc_all_physical")    
        return (bragg_deg,perp)
        
    def calc_all_pseudo(self, physicals):
        self._log.debug("Entering calc_all_pseudo")
        bragg_deg,perp_mm = physicals
        bragg_rad = math.radians(bragg_deg)
        self._log.debug("       Bragg: %f rad." % bragg_rad)
        try:
            vcm_pitch_mrad = self.vcm_pitch.Position
        except PyTango.DevFailed, e:
            self._log.debug("Couldn't read %s motor position." % self.VCMPitchName)
            raise e
        vcm_pitch_rad = vcm_pitch_mrad / 1000
        self._log.debug("       VCM pitch: %f rad." % vcm_pitch_rad)
        try:
            crystal_ior = self.dcm_crystal.Value
            d = self.siliconBondLength(crystal_ior)
        except PyTango.DevFailed, e:
            self._log.debug("Couldn't read %s ior value." % self.DCMCrystalIORName)
            raise e
        self._log.debug("       d: %f Angstroms." % d)
        try:
            energy = self.hc / (2 * d * math.sin(bragg_rad - 2 * vcm_pitch_rad))
        except ZeroDivisionError, e:
            energy = float('nan')
        self._log.debug("Leaving calc_all_pseudo")
        return (energy,)
        
    def GetExtraAttributePar(self, axis, name):
        """Get Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to get an extra attribute
        :param name: (string) attribute name to retrieve

        :return: value of the attribute
        """
        #if axis == 1 and name.lower() == 'exitoffset':
        #    self._log.debug("&&&&&&&&&" + repr(self.get_motor_role(1)))
        #    return 2 * PoolUtil().get_motor(self.get_motor_role(1)).position * math.cos(math.radians(PoolUtil().get_motor(self.get_motor_role(0)).position)) #mm
        return self.attributes[axis][name]

    def SetExtraAttributePar(self, axis, name, value):
        """Set Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to set an extra attribute
        :param name: (string) attribute name to retrieve
        :param value: an extra attribute value to be set

        """
        self.attributes[axis][name] = value

    def siliconBondLength(self, ior_value):
        if ior_value == 311:
            return self.attributes[1]['dSi311'] #Angstroms
        elif ior_value == 111:
            return self.attributes[1]['dSi111'] #Angstroms
        else:
            raise ValueError("Wrong ior value")
