from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import MemorizedNoInit, NotMemorized, Memorized

import math
import PyTango

class EnergyCffFixed(PseudoMotorController):
    """Energy pseudomotor controller. Used for scans with Cff fixed"""

    pseudo_motor_roles = ('Energy','Cff')
    motor_roles = ("m2", "gr")

    class_prop = { 'iorGrx':{'Type':'PyTango.DevString',
                             'Description':'IORegister for GRX: server/device/name'
                                },
                   'hc':{'Type':'PyTango.DevDouble',
                         'Description':'hc',
                         'DefaultValue':12398.41856
                        },
                    }

    ctrl_extra_attributes = {"DiffrOrder":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'DefaultValue':1.0
                                  },
                             "Alpha":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ',
                                  },
                             "Beta":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ',
                                  },
                             "Theta":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ',
                                  },
                             "FixedM2Pit":
                                  {'Type':'PyTango.DevBoolean',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'DefaultValue':False
                                  },
                             "offsetGrLE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMLE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetGrME":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMME":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetGrHE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMHE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                            }

    
    def __init__(self, inst, props):
        PseudoMotorController.__init__(self,inst,props)

        self.ior = PyTango.DeviceProxy(self.iorGrx)

        self.Cff = 0.0
        self.DiffrOrder = 1.0
        self.FixedM2Pit = False

        self.offsetGrLE = 0.0
        self.offsetMLE = 0.0
        self.offsetGrHE = 0.0
        self.offsetMHE = 0.0
        self.offsetGrME = 0.0
        self.offsetMME = 0.0

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index - 1]
    
    def calc_all_physical(self, pseudo_pos, param=None):
        """From a given energy, we calculate the physical
         position for the real motors."""

        energy = pseudo_pos[0]
        #self.Cff = pseudo_pos[1]
        Cff = pseudo_pos[1]

        if energy == 0.0:
            waveLen = 0.0
        else:
            waveLen = self.hc / energy
        
        offsetG,offsetM = self.checkOffset()

        if not self.FixedM2Pit:
            #f1 = self.Cff**2 + 1
            #f2 = 1 - self.Cff**2
            f1 = Cff**2 + 1
            f2 = 1 - Cff**2
            K = self.DiffrOrder * waveLen * self.look_at_grx()
        
            #CosAlpha = math.sqrt(-1*K**2 * f1 + 2*math.fabs(K) * math.sqrt(f2**2 + self.Cff**2 * K**2))/math.fabs(f2)
            CosAlpha = math.sqrt(-1*K**2 * f1 + 2*math.fabs(K) * math.sqrt(f2**2 + Cff**2 * K**2))/math.fabs(f2)

            self.alpha = math.acos(CosAlpha)
            CosBeta = Cff * CosAlpha
            #CosBeta = self.Cff * CosAlpha
            self.beta = -math.acos(CosBeta)
            self.theta = (self.alpha - self.beta) * 0.5

            m = ((math.pi/2.0) - self.theta + offsetM)*1000 #angle*1000 to have it in mrad
            g = (self.beta + (math.pi/2.0) + offsetG)*1000
            #txt = "%.2f %.5f %.6f %.6f" %(energy, self.Cff, m, g)
            txt = "%.2f %.5f %.6f %.6f" %(energy, Cff, m, g)
            print txt 
            return (m,g)
        else:
            mkl = self.DiffrOrder * self.look_at_grx() * waveLen
            A1 = (mkl/2.0) * math.tan(self.theta)
            A2 = math.sqrt(((math.cos(self.theta))**2) - ((mkl/2.0)**2))
            
            self.beta = -math.acos(A2 - A1)
            self.alpha = (2*self.theta) + self.beta #Theta estaba sin multiplicar y antes se cogia el valor y lo dividia por 2 ?? O_o!

            m = ((math.pi/2.0) - self.theta + offsetM)*1000 #angle*1000 to have it in mrad
            g = (self.beta + (math.pi/2.0) + offsetG)*1000
            return (m,g)
            
    def calc_all_pseudo(self, physical_pos, param=None):
        """From the real motor positions, we calculate the pseudomotors positions."""

        offsetG,offsetM = self.checkOffset()
        self.beta = (physical_pos[1]/1000) - (math.pi/2.0) - offsetG
        self.theta = (math.pi/2.0) - (physical_pos[0]/1000) + offsetM
        self.alpha = (2.0*self.theta) + self.beta
        wavelength = (math.sin(self.alpha) + math.sin(self.beta)) / (self.DiffrOrder * self.look_at_grx())
        
        if wavelength == 0.0:
            energy = 0.0
        else:
            energy = self.hc / wavelength
        
        self.Cff = math.cos(self.beta)/math.cos(self.alpha)
        if energy < 0 : energy = energy *(-1) #warning: wavelength se vuelve negativo ... ??????
        return (energy,self.Cff)

    def GetExtraAttributePar(self, axis, name):
        
        if name.lower() == "diffrorder":
            return self.DiffrOrder
        
        if name.lower() == "alpha":
            return self.alpha
        if name.lower() == "beta":
            return self.beta
        if name.lower() == "theta":
            return self.theta
        
        if name.lower() == "fixedm2pit":
            return self.FixedM2Pit
            
        if name.lower() == "offsetgrle":
            return self.offsetGrLE 
        
        if name.lower() == "offsetmle":
            return self.offsetMLE 

        if name.lower() == "offsetgrme":
            return self.offsetGrME 
        
        if name.lower() == "offsetmme":
            return self.offsetMME
        
        if name.lower() == "offsetgrhe":
            return self.offsetGrHE 
        
        if name.lower() == "offsetmhe":
            return self.offsetMHE
             
    def SetExtraAttributePar(self, axis, name, value):
        if name.lower() == "diffrorder":
            self.DiffrOrder = value
        if name.lower() == "fixedm2pit":
            self.FixedM2Pit = value

        if name.lower() == "offsetgrle":
            self.offsetGrLE = value
        
        if name.lower() == "offsetmle":
            self.offsetMLE = value

        if name.lower() == "offsetgrme":
            self.offsetGrME = value
        
        if name.lower() == "offsetmme":
            self.offsetMME = value
             
        if name.lower() == "offsetgrhe":
            self.offsetGrHE = value
        
        if name.lower() == "offsetmhe":
            self.offsetMHE = value

    def look_at_grx(self):
            
        iorPos = self.ior['Value'].value
        
        energyRange = 0

        #if iorPos == 4 and energy >= 100 and energy <= 600:
        #    energyRange = True

        #if iorPos == 3 and energy >= 500 and energy <= 1300:
        #    energyRange = True
        
        #if iorPos == 2 and energy >= 1100 and energy <= 2000:
        #    energyRange = True

        #if not energyRange:
        #    self._log.debug("GRX doesn't match with the energy selected")
            #@todo Change the status of the pseudo if the energy doesn't match?

        if iorPos == 4:
            return 700.0 * 1E-7
        elif iorPos == 3:
            return 900.0 * 1E-7
        elif iorPos == 2:
            return 1200.0 * 1E-7
        else:
            return 0.0

    def checkOffset(self):
        offsetGrating,offsetMirror = 0.0, 0.0
        
        if self.ior['Value'].value == 4:
            offsetGrating = self.offsetGrLE/1000.0
            offsetMirror = self.offsetMLE/1000.0
        
        elif self.ior['Value'].value == 3:
            offsetGrating = self.offsetGrME/1000.0
            offsetMirror = self.offsetMME/1000.0
        
        if self.ior['Value'].value == 2:
            offsetGrating = self.offsetGrHE/1000.0
            offsetMirror = self.offsetMHE/1000.0
        
        return offsetGrating, offsetMirror

        

#########################

class EnergyAtFixedCff(PseudoMotorController):
    """
    With respect to the above energy:
    1) We remove the Cff from the "pseudo_motor_roles
    2) We define a new ctrl_extra_attributes named "Cff"
    """

    pseudo_motor_roles = ('Energy',)
    motor_roles = ("m2", "gr")

    class_prop = { 'iorGrx':{'Type':'PyTango.DevString',
                             'Description':'IORegister for GRX: server/device/name'
                                },
                   'hc':{'Type':'PyTango.DevDouble',
                         'Description':'hc',
                         'DefaultValue':12398.41856
                        },
                    }

    ctrl_extra_attributes = {"Cff":
                                  {'Type':'PyTango.DevDouble', 
                                   'R/W Type':'PyTango.READ_WRITE', 
                                   'DefaultValue':2.25
                                  },
                             "DiffrOrder":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'DefaultValue':1.0
                                  },
                             "Alpha":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ',
                                  },
                             "Beta":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ',
                                  },
                             "Theta":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ',
                                  },
                             "FixedM2Pit":
                                  {'Type':'PyTango.DevBoolean',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'DefaultValue':False
                                  },
                             "offsetGrLE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMLE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetGrME":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMME":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetGrHE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                             "offsetMHE":
                                  {'Type':'PyTango.DevDouble',
                                   'memorized':Memorized,
                                   'R/W Type':'PyTango.READ_WRITE',
                                  },
                            }

    
    def __init__(self, inst, props):
        PseudoMotorController.__init__(self,inst,props)

        self.ior = PyTango.DeviceProxy(self.iorGrx)

        self.Cff = 2.25
        self.DiffrOrder = 1.0
        self.FixedM2Pit = False

        self.offsetGrLE = 0.0
        self.offsetMLE = 0.0
        self.offsetGrHE = 0.0
        self.offsetMHE = 0.0
        self.offsetGrME = 0.0
        self.offsetMME = 0.0

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index - 1]
    
    def calc_all_physical(self, pseudo_pos, param=None):
        """From a given energy, we calculate the physical
         position for the real motors."""

        energy = pseudo_pos[0]
        
        # Cff = pseudo_pos[1] # FB Now it is not a pseudoMotor_role!!!

        if energy == 0.0:
            waveLen = 0.0
        else:
            waveLen = self.hc / energy
        
        offsetG,offsetM = self.checkOffset()

        if not self.FixedM2Pit:
            f1 = self.Cff**2 + 1
            f2 = 1 - self.Cff**2
            # FB f1 = Cff**2 + 1 # FB 
            # FB f2 = 1 - Cff**2
            K = self.DiffrOrder * waveLen * self.look_at_grx()
        
            CosAlpha = math.sqrt(-1*K**2 * f1 + 2*math.fabs(K) * math.sqrt(f2**2 + self.Cff**2 * K**2))/math.fabs(f2)
            # FB CosAlpha = math.sqrt(-1*K**2 * f1 + 2*math.fabs(K) * math.sqrt(f2**2 + Cff**2 * K**2))/math.fabs(f2)

            self.alpha = math.acos(CosAlpha)
            # FB CosBeta = Cff * CosAlpha
            CosBeta = self.Cff * CosAlpha
            self.beta = -math.acos(CosBeta)
            self.theta = (self.alpha - self.beta) * 0.5

            m = ((math.pi/2.0) - self.theta + offsetM)*1000 #angle*1000 to have it in mrad
            g = (self.beta + (math.pi/2.0) + offsetG)*1000
            txt = "%.2f %.5f %.6f %.6f" %(energy, self.Cff, m, g)
            # FB txt = "%.2f %.5f %.6f %.6f" %(energy, Cff, m, g)
            print txt 
            return (m,g)
        else:
            mkl = self.DiffrOrder * self.look_at_grx() * waveLen
            A1 = (mkl/2.0) * math.tan(self.theta)
            A2 = math.sqrt(((math.cos(self.theta))**2) - ((mkl/2.0)**2))
            
            self.beta = -math.acos(A2 - A1)
            self.alpha = (2*self.theta) + self.beta #Theta estaba sin multiplicar y antes se cogia el valor y lo dividia por 2 ?? O_o!

            m = ((math.pi/2.0) - self.theta + offsetM)*1000 #angle*1000 to have it in mrad
            g = (self.beta + (math.pi/2.0) + offsetG)*1000
            return (m,g)
            
    def calc_all_pseudo(self, physical_pos, param=None):
        """From the real motor positions, we calculate the pseudomotors positions."""
        offsetG,offsetM = self.checkOffset()
        self.beta = (physical_pos[1]/1000) - (math.pi/2.0) - offsetG
        self.theta = (math.pi/2.0) - (physical_pos[0]/1000) + offsetM
        self.alpha = (2.0*self.theta) + self.beta
        wavelength = (math.sin(self.alpha) + math.sin(self.beta)) / (self.DiffrOrder * self.look_at_grx())
        
        print "wavelength",  wavelength
        if wavelength == 0.0:
            energy = 0.0
        else:
            energy = self.hc / wavelength
        
        
        if energy < 0 : energy = energy *(-1) #warning: wavelength se vuelve negativo ... ??????

        # FB self.Cff = math.cos(self.beta)/math.cos(self.alpha)
        # FB return (energy,self.Cff)

        print "energy",  energy
        return [energy,]

    def GetExtraAttributePar(self, axis, name):


        if name.lower() == "cff":
            return self.Cff
        
        if name.lower() == "diffrorder":
            return self.DiffrOrder
        
        if name.lower() == "alpha":
            return self.alpha
        if name.lower() == "beta":
            return self.beta
        if name.lower() == "theta":
            return self.theta
        
        if name.lower() == "fixedm2pit":
            return self.FixedM2Pit
            
        if name.lower() == "offsetgrle":
            return self.offsetGrLE 
        
        if name.lower() == "offsetmle":
            return self.offsetMLE 

        if name.lower() == "offsetgrme":
            return self.offsetGrME 
        
        if name.lower() == "offsetmme":
            return self.offsetMME
        
        if name.lower() == "offsetgrhe":
            return self.offsetGrHE 
        
        if name.lower() == "offsetmhe":
            return self.offsetMHE
             
    def SetExtraAttributePar(self, axis, name, value):
        if name.lower() == "cff":
            self.Cff = value
        if name.lower() == "diffrorder":
            self.DiffrOrder = value
        if name.lower() == "fixedm2pit":
            self.FixedM2Pit = value

        if name.lower() == "offsetgrle":
            self.offsetGrLE = value
        
        if name.lower() == "offsetmle":
            self.offsetMLE = value

        if name.lower() == "offsetgrme":
            self.offsetGrME = value
        
        if name.lower() == "offsetmme":
            self.offsetMME = value
             
        if name.lower() == "offsetgrhe":
            self.offsetGrHE = value
        
        if name.lower() == "offsetmhe":
            self.offsetMHE = value

    def look_at_grx(self):
        iorPos = self.ior['Value'].value
        
        energyRange = 0

        #if iorPos == 4 and energy >= 100 and energy <= 600:
        #    energyRange = True

        #if iorPos == 3 and energy >= 500 and energy <= 1300:
        #    energyRange = True
        
        #if iorPos == 2 and energy >= 1100 and energy <= 2000:
        #    energyRange = True

        #if not energyRange:
        #    self._log.debug("GRX doesn't match with the energy selected")
            #@todo Change the status of the pseudo if the energy doesn't match?

        if iorPos == 4:
            return 700.0 * 1E-7
        elif iorPos == 3:
            return 900.0 * 1E-7
        elif iorPos == 2:
            return 1200.0 * 1E-7
        else:
            return 0.0

    def checkOffset(self):
        offsetGrating,offsetMirror = 0.0, 0.0
        
        if self.ior['Value'].value == 4:
            offsetGrating = self.offsetGrLE/1000.0
            offsetMirror = self.offsetMLE/1000.0
        
        elif self.ior['Value'].value == 3:
            offsetGrating = self.offsetGrME/1000.0
            offsetMirror = self.offsetMME/1000.0
        
        if self.ior['Value'].value == 2:
            offsetGrating = self.offsetGrHE/1000.0
            offsetMirror = self.offsetMHE/1000.0
        
        
        return offsetGrating, offsetMirror




