import math

import PyTango
from pool import PseudoMotorController, PoolUtil
  
class DCM_energy(PseudoMotorController):
    """This pseudomotor controller does the calculation of Bragg
    and 2nd Xtal perpendicular position according to desired energy in keV."""
    
    pseudo_motor_roles = ('energy')
    motor_roles = ('bragg')
    
    class_prop = { 'VCMPitchName':{'Type' : 'PyTango.DevString', 'Description' : 'VCM_pitch pseudomotor'}}
    
    ctrl_extra_attributes = {"Silicon":{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'}}
    
    hc = 12398.419 #eV *Angstroms
    si111 = 3.1354161 #Angstroms            
    si311 =  1.637418 #Angstroms
                             
    def __init__(self, inst, props):    
        PseudoMotorController.__init__(self, inst, props)
        self.attributes = {}
        self.attributes[1] = {"Silicon":"si311", "VCM_pitch_pseudomotor":"vcm_pitch"}
        self.d = self.si311
        try:
            self.vcm_pitch = PoolUtil.get_motor(self, self.VCMPitchName)
        except Exception, e:
            self._log.error("Couldn't create DeviceProxy for vcm_pitch motor, please check this class property.")
            self._log.error(repr(e))
            
    def calc_physical(self, index, pseudos):
        self.calc_all_physical(pseudos)[index - 1]
    
    def calc_pseudo(self, index, physicals):
        self.calc_all_pseudos(physicals)[index - 1]
    
    def calc_all_physical(self, pseudos):
        energy = pseudos
        bragg = math.asin(self.hc/2/self.d/energy)
        return (bragg,)
        
    def calc_all_pseudos(self, physicals):
        bragg = physicals
        vcm_pitch_mrad = self.vcm_pitch.read_attribute("Position")
        vcm_pitch_deg = math.degrees(vcm_pitch_mrad * 1000) 
        energy = hc / (2 * self.d * math.sin(bragg + 2 * vcm_pitch_deg))
        return (energy,)
        
    def GetExtraAttributePar(self, axis, name):
        """ Get Energy pseudo motor particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        return self.attributes[axis][name]

    def SetExtraAttributePar(self, axis, name, value):
        """ Set Pmac axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        if name == "Silicon":
            value = value.lower()
            if value == "si111":
                self.attributes[axis][value]
                self.d = self.si111
            elif value == "si311":
                self.attributes[axis][value]
                self.d = self.si311
            else:
                PyTango.Except.throw_exception("DCM_energy_SetExtraAttributePar()", "Error setting " + name + ", value should be either si111 or si311 ", "SetExtraAttributePar()") 
        
        