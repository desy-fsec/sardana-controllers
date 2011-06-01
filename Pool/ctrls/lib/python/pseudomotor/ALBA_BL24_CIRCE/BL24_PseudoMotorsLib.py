from pool import PseudoMotorController
import math
import PyTango

class EnergyCffFixed(PseudoMotorController):
    """Energy pseudomotor controller. Used for scans with Cff fixed"""

    pseudo_motor_roles = ('EnergyCffFixed','EnergyIncludedAngle')
    motor_roles = ("m2", "gr")

    class_prop = { 'iorGrx':{'Type':'PyTango.DevString',
                             'Description':'IORegister for GRX: server/device/name'
                                },
                   'hc':{'Type':'PyTango.DevDouble',
                         'Description':'hc',
                         'DefaultValue':12398.41856
                        },
                   'offsetG':{'Type':'PyTango.DevDouble',
                              'Description':'Offset to apply in the calculation of beta',
                              'DefaultValue':0.0
                        },
                   'offsetM':{'Type':'PyTango.DevDouble',
                              'Description':'Offset to apply in the calculation of tetha',
                              'DefaultValue':0.0
                        },
                    }

    ctrl_extra_attributes = {"Cff":
                                  {'Type':'PyTango.DevDouble', 
                                   'R/W Type':'PyTango.READ_WRITE', 
                                   'DefaultValue':1.0
                                  },
                             "DiffrOrder":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'DefaultValue':1.0
                                  },
                             "IncludedAngle":
                                  {'Type':'PyTango.DevDouble',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'DefaultValue':1.0
                                  }
                            }

    
    def __init__(self, inst, props):
        PseudoMotorController.__init__(self,inst,props)

        self.ior = PyTango.DeviceProxy(self.iorGrx)

        self.Cff = 1.0
        self.DiffrOrder = 1.0
        self.IncludedAngle = 1.0

    #def calc_physical(self, index, pseudos):
    #    return self.calc_all_physical(pseudos)[index - 1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index - 1]
    
    def calc_physical(self, index, pseudo_pos):
        """From a given energy, we calculate the physical
         position for the real motors."""

        if index == 1:
            energy = pseudo_pos[0]
            #print("---------------------ENERGY: %f:" %energy)

            waveLen = self.hc / energy
            f1 = (self.Cff**2) + 1
            f2 = (self.Cff**2) - 1
            K = self.DiffrOrder * waveLen * self.look_at_grx()
        
            CosAlpha = math.sqrt(-1*K**2 * f1 + 2*math.fabs(K) * math.sqrt(f2**2 + self.Cff**2 * K**2))/math.fabs(f2)

            self.alpha = math.acos(CosAlpha)
            CosBeta = self.Cff * CosAlpha
            self.beta = -math.acos(CosBeta)
            self.theta = (self.alpha - self.beta) * 0.5

            #print("-----------------Alpha: %f, Beta:%f, Theta:%f, WaveLength:%f" %(self.alpha, self.beta, self.theta, waveLen))

            m = ((math.pi/2.0) - self.theta + self.offsetM)*1000 #angle*1000 to have it in mrad
            g = (self.beta + (math.pi/2.0) - self.offsetG)*1000
            return (m,g)

        if index == 2:
            energy = pseudo_pos[1]
            waveLen = self.hc / energy
            
            mkl = self.DiffrOrder * self.look_at_grx() * waveLen
            A1 = mkl/2.0 * math.tan(Theta/2)
            A2 = math.sqrt((math.cos(Theta/2)**2) - (mkl/2.0)**2)

            beta = -math.acos(A2 - A1)
            alpha = Theta + beta

            self.Cff = math.cos(beta) / math.cos(alpha)
            
            m = ((math.pi/2.0) - Theta/2.0 + self.offsetM)*1000 #angle*1000 to have it in mrad
            g = (beta + (math.pi/2.0) - self.offsetG)*1000
            return (m,g)
            
    def calc_all_pseudo(self, physical_pos, param=None):
        """From the real motor positions, we calculate the pseudomotors positions."""

        self.beta = (physical_pos[1]/1000) - (math.pi/2.0) + self.offsetG
        self.theta = (math.pi/2.0) - (physical_pos[0]/1000) + self.offsetM
        self.alpha = (2.0*self.theta) + self.beta
        wavelength = (math.sin(self.alpha) + math.sin(self.beta)) / (self.DiffrOrder * self.look_at_grx())
        #print('*******************************beta:%f, theta:%f, alpha:%f, wavelength:%f, look_at:%f ' %(self.beta, self.theta, self.alpha, wavelength, self.look_at_grx()))
        
        if wavelength == 0.0:
            energy = 0
        else:
            energy = self.hc / wavelength
        return (energy,energy) #This doesn't have to much sense but I need two pseudos for the two different modes

    def GetExtraAttributePar(self, axis, name):
        
        if name.lower() == "cff":
            return self.Cff

        if name.lower() == "diffrorder":
            return self.DiffrOrder
        
        if name.lower() == "includedangle":
            return self.IncludedAngle

    def SetExtraAttributePar(self, axis, name, value):
        if name.lower() == "cff":
            self.Cff = value

        if name.lower() == "diffrorder":
            self.DiffrOrder = value

        if name.lower() == "includedangle":
            self.IncludedAngle = value

    def look_at_grx(self):
            
        iorPos = self.ior['Value'].value
        
        energyRange = 0

        #if iorPos == 0 and energy >= 100 and energy <= 600:
        #    energyRange = True

        #if iorPos == 1 and energy >= 500 and energy <= 1300:
        #    energyRange = True
        
        #if iorPos == 2 and energy >= 1100 and energy <= 2000:
        #    energyRange = True

        #if not energyRange:
        #    self._log.debug("GRX doesn't match with the energy selected")
            #@todo Change the status of the pseudo if the energy doesn't match?

        if iorPos == 0:
            return 700.0 * 1E-7
        elif iorPos == 1:
            return 900.0 * 1E-7
        elif iorPos == 2:
            return 1200.0 * 1E-7
        else:
            return 0.0


