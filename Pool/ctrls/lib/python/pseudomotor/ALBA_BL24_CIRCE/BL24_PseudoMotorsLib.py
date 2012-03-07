from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController
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
                   'offsetG':{'Type':'PyTango.DevDouble',
                              'Description':'Offset to apply in the calculation of beta',
                              'DefaultValue':0.0
                        },
                   'offsetM':{'Type':'PyTango.DevDouble',
                              'Description':'Offset to apply in the calculation of tetha',
                              'DefaultValue':0.0
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
                                  }
                            }

    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props,*args,**kwargs)

        self.ior = PyTango.DeviceProxy(self.iorGrx)

        #self.energy = 1.0 #in order to avoid zerodivisionerror
        #self.wavelength = 1.0

        self.Cff = 0.0
        self.DiffrOrder = 1.0
        self.FixedM2Pit = False

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index - 1]
    
    def calc_all_physical(self, pseudo_pos, param=None):
        """From a given energy, we calculate the physical
         position for the real motors."""

        self.energy = pseudo_pos[0]
        self.Cff = pseudo_pos[1]

        #print("---------------------ENERGY: %f:" %self.energy)
        #print("---------------------Cff: %f:" %self.Cff)
        #self.calc_constants(energy)
        #sqrt1 = math.sqrt( (self.cffl**2.0) + (self.c2ff*self.mkl2) )
        #sqrt2 = math.sqrt((2.0 * math.fabs(self.mkl) * sqrt1) - (self.mkl2 * self.cffp))
        #cosa = sqrt2 / math.fabs(self.cffl)

        if self.energy == 0.0:
            waveLen = 0.0
        else:
            waveLen = self.hc / self.energy
        
        if not self.FixedM2Pit:
            f1 = self.Cff**2 + 1
            f2 = 1 - self.Cff**2
            K = self.DiffrOrder * waveLen * self.look_at_grx()
        
            CosAlpha = math.sqrt(-1*K**2 * f1 + 2*math.fabs(K) * math.sqrt(f2**2 + self.Cff**2 * K**2))/math.fabs(f2)

            self.alpha = math.acos(CosAlpha)
            CosBeta = self.Cff * CosAlpha
            self.beta = -math.acos(CosBeta)
            self.theta = (self.alpha - self.beta) * 0.5

            m = ((math.pi/2.0) - self.theta + self.offsetM)*1000 #angle*1000 to have it in mrad
            g = (self.beta + (math.pi/2.0) + self.offsetG)*1000
            return (m,g)
        else:
            mkl = self.DiffrOrder * self.look_at_grx() * waveLen
            #print 'MKL: %f'%mkl
            A1 = (mkl/2.0) * math.tan(self.theta)
            #print 'A1: %f'%A1
            A2 = math.sqrt(((math.cos(self.theta))**2) - ((mkl/2.0)**2))
            #print 'A2: %f'%A2

            self.beta = -math.acos(A2 - A1)
            self.alpha = (2*self.theta) + self.beta #Theta estaba sin multiplicar y antes se cogia el valor y lo dividia por 2 ?? O_o!

            #Cff = math.cos(beta) / math.cos(alpha)
            
            m = ((math.pi/2.0) - self.theta + self.offsetM)*1000 #angle*1000 to have it in mrad
            g = (self.beta + (math.pi/2.0) + self.offsetG)*1000
            return (m,g)


        #print("-----------------Alpha: %f, Beta:%f, Theta:%f, WaveLength:%f" %(self.alpha, self.beta, self.theta, waveLen))

#        if index == 2:
#            energy = pseudo_pos[1]
#            waveLen = self.hc / energy

#            Theta = self.theta #si se mueve desde icepap va a petar cosa fina! 
            
#            mkl = self.DiffrOrder * self.look_at_grx() * waveLen
#            A1 = mkl/2.0 * math.tan(Theta)
#            A2 = math.sqrt((math.cos(Theta)**2) - ((mkl/2.0)**2))

#            beta = -math.acos(A2 - A1)
#            alpha = (2*Theta) + beta #Theta estaba sin multiplicar y antes se cogia el valor y lo dividia por 2 ?? O_o!

#            Cff = math.cos(beta) / math.cos(alpha)
            
#            m = ((math.pi/2.0) - Theta/2.0 + self.offsetM)*1000 #angle*1000 to have it in mrad
#            g = (beta + (math.pi/2.0) - self.offsetG)*1000
#            return (m,g)
            
    def calc_all_pseudo(self, physical_pos, param=None):
        """From the real motor positions, we calculate the pseudomotors positions."""

        self.beta = (physical_pos[1]/1000) - (math.pi/2.0) - self.offsetG
        self.theta = (math.pi/2.0) - (physical_pos[0]/1000) - self.offsetM
        self.alpha = (2.0*self.theta) + self.beta
        wavelength = (math.sin(self.alpha) + math.sin(self.beta)) / (self.DiffrOrder * self.look_at_grx())
        #print('*******************************beta:%f, theta:%f, alpha:%f, wavelength:%f, look_at:%f ' %(self.beta, self.theta, self.alpha, wavelength, self.look_at_grx()))
        
        if wavelength == 0.0:
            self.energy = 0.0
        else:
            self.energy = self.hc / wavelength
        #if self.FixedM2Pit: 
        self.Cff = math.cos(self.beta)/math.cos(self.alpha)
        if self.energy < 0 : self.energy = self.energy *(-1) #warning: wavelength se vuelve negativo ... ??????
        return (self.energy,self.Cff)

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

    def SetExtraAttributePar(self, axis, name, value):
        if name.lower() == "diffrorder":
            self.DiffrOrder = value
        if name.lower() == "fixedm2pit":
            self.FixedM2Pit = value


    def look_at_grx(self):
            
        iorPos = self.ior['Value'].value
        
        #validEnergyRange = False

        #if iorPos == 4 and self.energy >= 100 and self.energy <= 600: return 700.0 * 1E-7
        #    validEnergyRange = True

        #elif iorPos == 3 and self.energy >= 500 and self.energy <= 1300: return 900.0 * 1E-7
        #    validEnergyRange = True
        
        #elif iorPos == 2 and self.energy >= 1100 and self.energy <= 2000: return 1200.0 * 1E-7
        #    validEnergyRange = True

        #if not validEnergyRange:
        #    self._log.debug("GRX doesn't match with the energy selected")
            #@todo Change the status of the pseudo if the energy doesn't match?
        #else: raise 'You are not on a valid energy range!!!'

        if iorPos == 4:
            return 700.0 * 1E-7
        elif iorPos == 3:
            return 900.0 * 1E-7
        elif iorPos == 2:
            return 1200.0 * 1E-7
        else:
            return 0.0


