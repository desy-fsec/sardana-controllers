""" The standard pseudo motor controller library for the device pool """

from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue



import math
import numpy as np
import scipy
import scipy.optimize
from PseudoEnergyLib import EnergyID, EnergyIDPlus
#from PseudoEnergyLib import 

import traceback

MILI    = 1E-3
MICRO   = 1E-6

def fromRadToTau(rad):
    return math.sin(2*rad)

def fromTauToRad(tau):
    rad = 0.5*math.asin(tau)
    return rad

def fromRadToDegree(rad):
    return rad/math.pi*180.0

def fromDegreeToRad(degree):
    rad = degree/180.0*math.pi
    return rad
    

##################################### Class for PARALLEL MODE only ###########
class PseudoEnergy(PseudoMotorController):
    """ """
    
    gender = "Undulator"
    model  = "Standard"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    ctrl_properties = {"id_name":{Type:str,Description:"I don't want to describe it",DefaultValue:'xxx'},
    "pol_units":{Type:str ,Description:"True if rad unit should b eused",DefaultValue:'rad'}}
    
    #ctrl_properties = {"id_name":{Type:str,Description:"I don't want to describe it",DefaultValue:'xxx'}}

    # FB the edMAXEnergy should be only READ, but there is a bug in the pool
    ctrl_extra_attributes = {'edOffset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                            'edHarmonic':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
                            'edMaxEnergy':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                            'edEnergy':{'Type':'PyTango.DevVarDoubleArray','R/W Type':'PyTango.READ'},
                             #'Acceleration':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             #'Deceleration':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             #'Velocity':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             #'Base_rate':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'}
                            }
    
    pseudo_motor_roles = ("E","P")
    motor_roles = ("G","M")
    
    def __init__(self,inst,props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props, *args, **kwargs)

        self.offsets = {}
        self.harmonics = {}
        self.energies = {}
        self.max_energies = {}

        self.Acceleration = {}
        self.Deceleration = {}
        self.Velocity = {}
        self.Base_rate = {}
        

        if self.id_name == 'NCD':
            self.lib = EnergyID('NCD')
        elif self.id_name == 'XALOC':
            self.lib = EnergyID('XALOC')
        elif self.id_name == 'CIRCE':
            self.lib = EnergyID('CIRCE')
        elif self.id_name == 'BOREAS':
            self.lib = EnergyID('BOREAS')
        else:
            pass
        

    def calc_physical(self, index, pseudo_pos):
        
        Energy = pseudo_pos[0]
        Polarization = pseudo_pos[1]

        harm = self.harmonics[index]
        off = self.offsets[index]

        # From Energy (eV) to Gap (meter)
        try:
            if self.pol_units == "rad":
                Gap,Phase = self.lib.calculateGapPhase(Energy, Polarization, harm, off)
            elif self.pol_units == "degree":
                rad = fromDegreeToRad(Polarization)
                Gap,Phase = self.lib.calculateGapPhase(Energy, rad, harm, off)
            else:
                rad = fromTauToRad(Polarization)
                Gap,Phase = self.lib.calculateGapPhase(Energy, rad, harm, off)
                #print " From Energy = %f and Pol = %f to Gap = %f and Phase = %f (rad=%f)" %(Energy, Polarization, Gap/MICRO,Phase/MICRO, rad)
        except Exception,e:
            raise

        if index == 1:
            return Gap/MICRO
        elif index == 2:
            return Phase/MICRO
            
    def calc_pseudo(self, index, physical_pos):
        
        Gap = physical_pos[0]
        Phase = physical_pos[1]
  
        harm = self.harmonics[index]
        off = self.offsets[index]

        
        # From Gap (meter) to Energy (eV)
        Gap = Gap*MICRO
        Phase = Phase*MICRO
        Energy, Polarization = self.lib.calculateEnergyPolarization(Gap, Phase, harm, off)
        
        if self.pol_units == "rad":
            tau = Polarization
        elif self.pol_units == "degree":
            tau = fromRadToDegree(Polarization)
        else:
            tau = fromRadToTau(Polarization)
        if index == 1:
            return Energy
        elif index == 2:
            return tau

    def read_all_motors(self, ind, name):
        try:
            # FB 14Nov2013
            m1 = self.GetMotor(0)
            m2 = self.GetMotor(1)
            #m1 = self.GetMotor(1)
            #m2 = self.GetMotor(2)
            a1 = m1.get_extra_par(name)
            a2 = m2.get_extra_par(name)
            if ind == 1:
                return a1
            elif ind == 2:
                return a2
        except Exception,e:
            traceback.print_exc()

    def GetExtraAttributePar(self, ind, name):
        try:
            if name == "edOffset":
                return self.offsets[ind]
            elif name == "edHarmonic":
                return self.harmonics[ind]
            elif name == "edEnergy":
                return self.energies[ind]
            elif name == "edMaxEnergy":
                return self.max_energies[ind]
            #elif name == "Acceleration":
                #self.Acceleration[ind] = self.read_all_motors(ind, name)
                #return self.Acceleration[ind]
            #elif name == "Deceleration":
                #self.Deceleration[ind] = self.read_all_motors(ind, name)
                #return self.Deceleration[ind]
            #elif name == "Velocity":
                ## We should convert from um to eV
                #vel = self.read_all_motors(ind, name)
                #self.Velocity[ind] = vel
                #import sys
                #sys.stderr.write("%s\n" %(self.Velocity[ind],))
                #return self.Velocity[ind]
            #elif name == "Base_rate":
                #self.Base_rate[ind] = self.read_all_motors(ind, name)
                #return self.Base_rate[ind]
        except Exception,e:
            print "Exception: PseudoIDplus  GetExtraAttributePar", str(e)
            print "Exception: ind = %d,  name= %s" %(ind, name)

    def SetExtraAttributePar(self, ind, name, value):
        try:
            #print "Set Energies",ind,name,value
            if name == "edOffset":
                self.offsets[1] = value
                self.offsets[2] = value
            elif name == "edHarmonic":
                self.harmonics[1] = value
                self.harmonics[2] = value
            #elif name == "Acceleration":
                #self.Acceleration[ind] = value
            #elif name == "Deceleration":
                #self.Deceleration[ind] = value
            #elif name == "Velocity":
                #self.Velocity[ind] = value
                ##self.GetMotor(ind-1).set_par(name, value)
            #elif name == "Base_rate":
                #self.Base_rate[ind] = value
            elif name == "edMaxEnergy":
                print "The max energy is read-only "
                return



            if name == "edOffset" or name == "edHarmonic":
                # Everytime we change offset and harmonic we recalculate the two curves
                eg1 = []
                for i in range(512):
                    fPhase = 0.0
                    # Gap in mm
                    fGap = float(i)/511.0*self.lib.GapMax
                    if fGap<self.lib.GapMin-0.001:
                        eg1.append(0.0)
                    else:
                        Energy, Polarization = self.lib.calculateEnergyPolarization(fGap, fPhase, self.harmonics[1], self.offsets[1])
                        eg1.append(Energy)
                self.energies[1] = eg1
                self.max_energies[1] = max(eg1)

                
                eg2 = []
                for i in range(512):
                    fPhase = self.lib.PhaseMax
                    # Gap in mm
                    fGap = float(i)/511.0*self.lib.GapMax
                    if fGap<self.lib.GapMin-0.001:
                        eg2.append(0.0)
                    else:
                        Energy, Polarization = self.lib.calculateEnergyPolarization(fGap, fPhase, self.harmonics[2], self.offsets[2])
                        eg2.append(Energy)
                        
                self.energies[2] = eg2
                self.max_energies[2] = max(eg2)

       
        except Exception,e:
            print "Exception: PseudoID SetExtraAttributePar", str(e)
            print "Exception: ind = %d,  name= %s, value = %f" %(ind, name, value)





###################################### Class for Parallel/Antiparallel mode (there is abug in Sardana) ###########

class PseudoEnergyPlus(PseudoMotorController):
    """ """
    
    gender = "Undulator"
    model  = "Standard"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    #ctrl_properties = {"id_name":{Type:str,Description:"I don't want to describe it",DefaultValue:'xxx'}}
    

    ctrl_properties = {"id_name":{Type:str,Description:"I don't want to describe it",DefaultValue:'xxx'},
    "pol_units":{Type:str ,Description:"True if rad unit should b eused",DefaultValue:'rad'}}
    

    # FB the edMAXEnergy should be only READ, but there is a bug in the pool
    ctrl_extra_attributes = {'edOffset':{'Type':'PyTango.DevDouble', 'R/W Type':'PyTango.READ_WRITE'},
                            'edHarmonic':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ_WRITE'},
                            'edMaxEnergy':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                            'parallelMode':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                            'polarizationPlusSign':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                            'edEnergy':{'Type':'PyTango.DevVarDoubleArray','R/W Type':'PyTango.READ'}
                            }
    
    pseudo_motor_roles = ("E","P")
    motor_roles = ("G","M","N")
    
    def __init__(self,inst,props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props, *args, **kwargs)

        self.offsets = {}
        self.harmonics = {}
        self.energies = {}
        self.parallelModes = {}
        self.polarizationPlusSigns = {}
        self.max_energies = {}

        if self.id_name == 'NCD':
            self.lib = EnergyIDPlus('NCD')
        elif self.id_name == 'XALOC':
            self.lib = EnergyIDPlus('XALOC')
        elif self.id_name == 'CIRCE':
            self.lib = EnergyIDPlus('CIRCE')
        elif self.id_name == 'BOREAS':
            self.lib = EnergyIDPlus('BOREAS')
        else:
            pass
        

    def calc_physical(self, index, pseudo_pos):
        
        Energy = pseudo_pos[0]
        if pseudo_pos[1] <0:
            self.polarizationPlusSigns[1] = False
        else:
            self.polarizationPlusSigns[1] = True
        Polarization = abs(pseudo_pos[1])#FB Take the absolute value of the polarizationplus

        harm = self.harmonics[index]
        off = self.offsets[index]

        # From Energy (eV) to Gap (meter)
	try:
            if self.pol_units == "rad":
                Gap,Phase = self.lib.calculateGapPhase(Energy, Polarization, harm, off)
            elif self.pol_units == "degree":
                rad = fromDegreeToRad(Polarization)
                Gap,Phase = self.lib.calculateGapPhase(Energy, rad, harm, off)
            else:
                rad = fromTauToRad(Polarization)
                Gap,Phase = self.lib.calculateGapPhase(Energy, rad, harm, off)
                #print " From Energy = %f and Pol = %f to Gap = %f and Phase = %f (rad=%f)" %(Energy, Polarization, Gap/MICRO,Phase/MICRO, rad)
        except Exception,e:
            raise

        if self.polarizationPlusSigns[1] == False:#FB If the polarization is negative the antiphase is negative
            Phase = 0.0 - Phase

        print "calc_physical: index = %d parallelMode = %d" %(index, self.parallelModes[1])
        if index == 1:      
            print "Gap = %f" %(Gap/MICRO)
            return Gap/MICRO
        elif index == 2:    
            if self.parallelModes[1] == True:      
                print "Phase = %f" %(Phase/MICRO)
                return Phase/MICRO
            else:      
                print "Phase = %f" %(0.0)
                return 0.0
        elif index == 3:  
            if self.parallelModes[1] == False: 
                print "AntiPhase = %f"  %(Phase/MICRO)
                return Phase/MICRO
            else:        
                print "AntiPhase = %f" %(0.0)
                return 0.0
            
    def calc_pseudo(self, index, physical_pos):
        
        Gap = physical_pos[0]
        Phase = physical_pos[1]
        AntiPhase = physical_pos[2]


        if AntiPhase <0:
            self.polarizationPlusSigns[1] = False
        else:
            self.polarizationPlusSigns[1] = True
  
        harm = self.harmonics[index]
        off = self.offsets[index]

        # From Gap (meter) to Energy (eV)
        Gap = Gap*MICRO
        Phase = Phase*MICRO
        AntiPhase = AntiPhase*MICRO

        if self.parallelModes[1] == True:
            Energy, Polarization = self.lib.calculateEnergyPolarization(Gap, Phase, harm, off)
        else:
            Energy, Polarization = self.lib.calculateEnergyPolarization(Gap, AntiPhase, harm, off)    
        #print "calc_pseudo: index = %d parallelMode = %d" %(index, self.parallelModes[1])

        if self.pol_units == "rad":
            tau = Polarization
        elif self.pol_units == "degree":
            tau = fromRadToDegree(Polarization)
        else:
            tau = fromRadToTau(Polarization)
            #print " TAU = %f to RAD = %f" %(tau, Polarization)

        if self.polarizationPlusSigns[1] == False:#FB If the polarization is negative the antiphase is negative
            tau = 0.0 - tau
	    
        if index == 1:
            return Energy
        elif index == 2:
            return tau
                    
    def GetExtraAttributePar(self, ind, name):
        try:
            if name == "edOffset":
                return self.offsets[ind]
            elif name == "edHarmonic":
                return self.harmonics[ind]
            elif name == "edEnergy":
                return self.energies[ind]
            elif name == "parallelMode":
                return self.parallelModes[ind]
            elif name == "polarizationPlusSign":
                return self.polarizationPlusSigns[ind]
            elif name == "edMaxEnergy":
                return self.max_energies[ind]
        except Exception,e:
            print "ExceptionPlus: PseudoIDplus  GetExtraAttributePar", str(e)
            print "ExceptionPlus: ind = %d,  name= %s" %(ind, name)

    def SetExtraAttributePar(self, ind, name, value):
        try:
            if name == "edOffset":
                self.offsets[1] = value
                self.offsets[2] = value
                self.offsets[3] = value
            elif name == "edHarmonic":
                self.harmonics[1] = value
                self.harmonics[2] = value
                self.harmonics[3] = value
            elif name == "parallelMode":
                self.parallelModes[1] = value
                self.parallelModes[2] = value
                self.parallelModes[3] = value
                self.lib.parallelMode = value
            elif name == "polarizationPlusSign":
                self.polarizationPlusSigns[1] = value
                self.polarizationPlusSigns[2] = value
                self.polarizationPlusSigns[3] = value
            elif name == "edMaxEnergy":
                print "The max energy is read-only "
                return
                

            # Everytime we change offset, harmonic or parallel mode we recalculate the two curves
            eg1 = []
            for i in range(512):
                fPhase = 0.0
                # Gap in mm
                fGap = float(i)/511.0*self.lib.GapMax
                if fGap<self.lib.GapMin-0.001:
                    eg1.append(0.0)
                else:
                    Energy, Polarization = self.lib.calculateEnergyPolarization(fGap, fPhase, self.harmonics[1], self.offsets[1])
                    eg1.append(Energy)
            self.energies[1] = eg1
            self.max_energies[1] = max(eg1)

            
            eg2 = []
            for i in range(512):
                fPhase = self.lib.PhaseMax
                # Gap in mm
                fGap = float(i)/511.0*self.lib.GapMax
                if fGap<self.lib.GapMin-0.001:
                    eg2.append(0.0)
                else:
                    Energy, Polarization = self.lib.calculateEnergyPolarization(fGap, fPhase, self.harmonics[2], self.offsets[2])
                    eg2.append(Energy)
                     
            self.energies[2] = eg2
            self.max_energies[2] = max(eg2)

       
        except Exception,e:
            print "ExceptionPlus: PseudoIDplus  SetExtraAttributePar", str(e)
            print "ExceptionPlus: ind = %d,  name= %s, value = %f" %(ind, name, value)
