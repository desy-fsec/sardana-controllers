""" The standard pseudo motor controller library for the device pool """

from sardana.pool.controller import PseudoMotorController

from math import *

class PseudoIvu(PseudoMotorController):
    """ """
    
    gender = "Ivu"
    model  = "Standard"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    axis_attributes = {'Offset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'} }
    
    pseudo_motor_roles = ("Gap", "Taper")
    motor_roles = ("IL1", "IL2")
    
  
    def __init__(self,inst,props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props, *args, **kwargs)
        self.offsets = {}

    def calc_physical(self,index,pseudo_pos):
        
        gap = pseudo_pos[0]
        taper = pseudo_pos[1]
        
        IL10 = self.offsets[1]
        IL20 = self.offsets[2]
        IL1 = IL10 + gap 
        IL2 = IL20 + gap + taper
        
        if index == 1:# IL1
            return IL1
        if index == 2:# IL2
            return IL2
            
    def calc_pseudo(self,index,physical_pos):
        IL10 = self.offsets[1]
        IL20 = self.offsets[2]
        IL1 = physical_pos[0] - IL10
        IL2 = physical_pos[1] - IL20
        
        gap = IL1
        taper = IL2 - IL1
        
        if index == 1:# GAP
            return gap
        if index == 2:# TAPER
            return taper
        
    def GetExtraAttributePar(self,ind,name):
        if name == "Offset":
            return self.offsets[ind]

    def SetExtraAttributePar(self,ind,name,value):
        try:
            if name == "Offset":
                self.offsets[ind] = value
            print "Set Offset ",ind,"=",value
        except Exception,e:
            print "PseudoIvu Exception"

class PseudoXaloc(PseudoMotorController):
    """ """
    
    gender = "Undulator"
    model  = "Standard"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    axis_attributes = {'edOffset':{'Type':'PyTango.DevDouble',
                                        'R/W Type':'PyTango.READ_WRITE'},
                            'edHarmonic':{'Type':'PyTango.DevInt',
                                        'R/W Type':'PyTango.READ_WRITE'},
                            #'energy':{'Type':'PyTango.DevDouble',
                                        #'R/W Type':'PyTango.READ'}, 
                            }

        #self.energy = []
            ## R/W-Number of harmonic
        #self.edHarmonic = 7
            ## R/W-Energy offset in eV
        #self.edOffset = 0
    
    pseudo_motor_roles = ("Energy")
    motor_roles = ("Gap")
    
    def __init__(self,inst,props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props, *args, **kwargs)
    #def __init__(self,inst,props):
        #PseudoMotorController.__init__(self,inst,props)
        self.offsets = {}
        self.harmonics = {}

    def calc_physical(self, index, pseudo_pos):
        
        Energy = pseudo_pos[0]
        
        # From Energy to micra
        Gap = self.calculateGap(Energy)
        
        if index == 1:
            return Gap
            
    def calc_pseudo(self, index, physical_pos):
        
        Gap = physical_pos[0]
  
        # From micra to Energy
        Energy = self.calculateEnergy(Gap)
        
        if index == 1:
            return Energy
        
    def GetExtraAttributePar(self, ind, name):
        try:
            if name == "edOffset":
                return self.offsets[ind]
            if name == "edHarmonic":
                return self.harmonics[ind]
        except Exception,e:
            print "PseudoXaloc Exception"

    def SetExtraAttributePar(self, ind, name, value):
        try:
            if name == "edOffset":
                self.offsets[ind] = value
            if name == "edHarmonic":
                self.harmonics[ind] = value
        except Exception,e:
            print "PseudoXaloc Exception"


    def initXaloc(self): 
        # Additional Properties (Xaloc)
        self.HCEVA = 12398.419303652055 
        self.ANGS = 1E-10
        self.EMASS = 0.000510998918    
        self.Gamma  = 3/self.EMASS
        self.MaxGap = 30.0
        self.MinGap = 5.7

        """ specific calibration for XALOC """        
        self.LambdaU = 0.0216
        self.a2 = +0.0005087060
        self.a1 = -0.1592998865 
        self.A0 = np.exp(1.4508580534)
        # Initialize the energy spectrum
        #for i in range(512):
            ## Gap in mm
            #fGap = float(i)/512.0*self.MaxGap
            #self.energy.append(self.calculateEnergy(fGap))

    # From Gap in mm to Energy in eV
    def calculateEnergy(self, fGap):
        fGap = fGap/1000.0# from micra to mm
        if fGap<self.MinGap-0.001:
            return 0.0
        K = self.A0*np.exp(self.a1*fGap + self.a2*fGap**2) 
        E1 = self.HCEVA*self.ANGS*(2.0*self.Gamma**2)/(self.LambdaU*(1.0+0.5*K**2))
        En = self.edHarmonic*E1 - self.edOffset
        return En

    
    # From Energy in eV to Gap in mm
    def calculateGap(self, fEnergy):
            
        E1 = (fEnergy+self.edOffset)/self.edHarmonic
        K = np.real(np.sqrt(4.0*self.HCEVA*self.ANGS*self.Gamma**2/(self.LambdaU*E1)-2.0))    
        gap = (-self.a1 - np.sqrt(self.a1**2 + 4.0*self.a2*np.log(K/self.A0)))/(2.0*self.a2)        
        return gap*1000.0# Micra


