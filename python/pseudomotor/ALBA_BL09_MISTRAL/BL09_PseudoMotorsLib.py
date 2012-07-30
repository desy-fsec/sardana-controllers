import math
import PyTango
from pool import PseudoMotorController
  
class MZ_Pseudos(PseudoMotorController):
  """ The General PseudoMotor controller class for the MISTRAL's tables.
      This Class will be used for the pseudos that handle the mz motors.
         ____________________________
    D |                                                                 |
    Y |                                            *mzr            |
    M |   *mzc                                                    |   <-------- beam direction
        |                                           *mzl             |
    X |____________________________|
                  DIM Y
  """

  def calc_physical(self, index, pseudos):
    return self.calc_all_physical(pseudos)[index - 1]

  def calc_pseudo(self, index, physicals):
    return self.calc_all_pseudo(physicals)[index - 1]

  def calc_all_physical(self, pseudos):
    z, pit, rol = pseudos
    
    dim_y_m = self.DIM_Y / 1000.0
    dim_x_m = self.DIM_X / 1000.0
    
    z_m = z / 1000.0
    pit_rad = pit / 1000.0
    rol_rad = rol / 1000.0

    mzc_m = z_m + math.tan(pit_rad) * dim_y_m / 2
    mzr_m = z_m - math.tan(pit_rad) * dim_y_m / 2 - math.tan(rol_rad) * dim_x_m / 2
    mzl_m = z_m - math.tan(pit_rad) * dim_y_m / 2 + math.tan(rol_rad) * dim_x_m / 2
    
    mzc = mzc_m * 1000
    mzl = mzl_m * 1000
    mzr = mzr_m * 1000
    
    return (mzc, mzl, mzr)

  def calc_all_pseudo(self, physicals):
    mzc, mzl, mzr = physicals

    dim_y_m = self.DIM_Y / 1000.0
    dim_x_m = self.DIM_X / 1000.0
    
    mzc_m = mzc / 1000.0
    mzl_m = mzl / 1000.0
    mzr_m = mzr / 1000.0

    pit_rad = math.atan2((mzc_m - (mzr_m + mzl_m) / 2), dim_y_m)
    rol_rad = math.atan2((mzl_m - mzr_m), dim_x_m)
    z_m = mzc_m / 2 + (mzl_m + mzr_m) / 4

    z = z_m * 1000
    pit = pit_rad * 1000
    rol = rol_rad * 1000

    return (z, pit, rol)

class M1_Z_Pitch_Roll(MZ_Pseudos):
  """ The PseudoMotor controller for the MISTRAL's M1 table: Z, Pitch, Roll.
      User units must be: mm for distances and mrad for angles.
      Pitch rotational axis is in the middle of Y dimension.
      Roll rotational axis is in the middle of X dimension.
         ____________________________
    D |                                                                 |
    Y |                                            *mzr            |
    M |   *mzc                                                    |   <-------- beam direction
        |                                           *mzl             |
    X |____________________________|
                  DIM Y

      Increasing pitch angle of 1 mrad should increase mzc of 0.57250019083340975 mm 
                                              decrease mzl and mzr of 0.57250019083340975 mm 
      Increasing roll angle of 1 mrad should increase mzl of 0.11000003666668135 mm    
                                             decrease mzr of 0.11000003666668135 mm  
  """
  
  pseudo_motor_roles = ('z', 'pitch', 'roll')
  motor_roles = ('mzc', 'mzl', 'mzr')
  
  class_prop = {'DIM_Y':{'Description':'Y dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':1145
                                            },
                            'DIM_X':{'Description':'X dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':220
                                            }
                            }
  
  
class M2_Z_Yaw_Roll(MZ_Pseudos):
  """ The PseudoMotor controller for the MISTRAL's M2 table: Z, Yaw, Roll.
      User units must be: mm for distances and mrad for angles.
      Pitch rotational axis is in the middle of Y dimension.
      Roll rotational axis is in the middle of X dimension.
         ____________________________
    D |                                                                 |
    Y |                                            *mzr            |
    M |   *mzc                                                    |   <-------- beam direction
        |                                           *mzl             |
    X |____________________________|
                  DIM Y


      Increasing yaw angle of 1 mrad should increase mzc of 0.72250024083342975  mm    
                                              decrease mzl and mzr of 0.72250024083342975  mm
      Increasing roll angle of 1 mrad should increase mzl of 0.11000003666668135 mm    
                                             decrease mzr of 0.11000003666668135 mm 

  """
  
  pseudo_motor_roles = ('z', 'yaw', 'roll')
  motor_roles = ('mzc', 'mzl', 'mzr')

  class_prop = {'DIM_Y':{'Description':'Y dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':1445
                                            },
                            'DIM_X':{'Description':'X dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':220
                                            }
                            }

class M4_Z_Pitch_Roll(MZ_Pseudos):
  """ The PseudoMotor controller for the MISTRAL's M4 table: Z, Pitch, Roll.
      User units must be: mm for distances and mrad for angles.
      Pitch rotational axis is in the middle of Y dimension.
      Roll rotational axis is in the middle of X dimension.
         ____________________________
    D |                                                                 |
    Y |                                            *mzr            |
    M |   *mzc                                                    |   <-------- beam direction
        |                                           *mzl             |
    X |____________________________|
                  DIM Y

      Increasing pitch angle of 1 mrad should increase mzc of 0.5442501814167393 mm
                                              decrease mzl and mzr of 5442501814167393 mm
      Increasing roll angle of 1 mrad should increase mzl of 0.11000003666668135 mm    
                                             decrease mzr of 0.11000003666668135 mm  
  """

  pseudo_motor_roles = ('z', 'pitch', 'roll')
  motor_roles = ('mzc', 'mzl', 'mzr')

  class_prop = {'DIM_Y':{'Description':'Y dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':1088.50
                                            },
                            'DIM_X':{'Description':'X dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':220
                                            }
                            }

class MX_Pseudos(PseudoMotorController):
  """ The General PseudoMotor controller class for the MISTRAL's tables.
      This Class will be used for the pseudos that handle the mx motors.

     ____________________________
    |                                                                 |
    |                                                                 |
    |                                                                 |   <-------- beam direction
    |                                                                 |
    |____________________________|
      ^ mx1                  ^ mx2
      
  """

  def calc_physical(self, index, pseudos):
    return self.calc_all_physical(pseudos)[index - 1]

  def calc_pseudo(self, index, physicals):
    return self.calc_all_pseudo(physicals)[index - 1]

  def calc_all_physical(self, pseudos):
    x, yaw = pseudos
    
    dim_y_m = self.DIM_Y / 1000.0
    
    x_m = x / 1000.0
    yaw_rad = yaw / 1000.0

    mx1_m = x_m - math.tan(yaw_rad) * dim_y_m / 2
    mx2_m = x_m + math.tan(yaw_rad) * dim_y_m / 2

    mx1 = mx1_m * 1000
    mx2 = mx2_m * 1000

    return (mx1, mx2)

  def calc_all_pseudo(self, physicals):
    mx1, mx2 = physicals

    dim_y_m = self.DIM_Y / 1000.0
    
    mx1_m = mx1 / 1000.0
    mx2_m = mx2 / 1000.0

    x_m = (mx1_m + mx2_m) / 2
    yaw_rad = math.atan2((mx2_m - mx1_m), dim_y_m)

    x = x_m * 1000
    yaw = yaw_rad * 1000

    return (x, yaw)
  
class M1_X_and_Yaw(MX_Pseudos): 
  """
    The PseudoMotor controller for the MISTRAL's M1 table: X, Yaw.
    User units must be: mm for distances and mrad for angles.
    Yaw rotational axis is in the middle of Y dimension.
    
     ____________________________
    |                                                                 |
    |                                                                 |
    |                                                                 |   <-------- beam direction
    |                                                                 |
    |____________________________|
      ^ mx1                  ^ mx2
      
    Increasing yaw angle of 1 mrad should increase mx2 of 0.57250019083340975 mm    
                                          decrease mx1 of 0.57250019083340975 mm  
  """

  pseudo_motor_roles = ('x', 'yaw')
  motor_roles = ('mx1', 'mx2')

  class_prop = {'DIM_Y':{'Description':'Y dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':1145
                                            }
                            }
  
  #DIM_Y =1145

class M2_X_and_Pitch(MX_Pseudos):
  """
    The PseudoMotor controller for the MISTRAL's M2 table: X, Pitch.
    User units must be: mm for distances and mrad for angles.
    Pitch rotational axis is in the middle of Y dimension.
    
     ____________________________
    |                                                                 |
    |                                                                 |
    |                                                                 |   <-------- beam direction
    |                                                                 |
    |____________________________|
      ^ mx1                  ^ mx2
      
    Increasing pitch angle of 1 mrad should increase mx2 of 0.72250024083342975 mm    
                                          decrease mx1 of 0.72250024083342975 mm  
  """

  pseudo_motor_roles = ('x', 'pitch')
  motor_roles = ('mx1', 'mx2')


  class_prop = {'DIM_Y':{'Description':'Y dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':1445
                                            }
                            }

  #DIM_Y = 1445

class M4_X_and_Yaw(MX_Pseudos):
  """
    The PseudoMotor controller for the MISTRAL's M4 table: X, Yaw.
    User units must be: mm for distances and mrad for angles.
    Yaw rotational axis is in the middle of Y dimension.
    
     ____________________________
    |                                                                 |
    |                                                                 |
    |                                                                 |   <-------- beam direction
    |                                                                 |
    |____________________________|
      ^ mx1                  ^ mx2
      
    Increasing yaw angle of 1 mrad should increase mx2 of 0.5442501814167393 mm    
                                          decrease mx1 of 0.5442501814167393 mm  
  """

  pseudo_motor_roles = ('x', 'yaw')
  motor_roles = ('mx1', 'mx2')

  class_prop = {'DIM_Y':{'Description':'Y dimension for the table (in mm)',
                                            'Type':'PyTango.DevDouble',
                                            'DefaultValue':1088.50
                                            }
                            }

  #DIM_Y = 1088.50 
  
  
class EnergyCffFixed(PseudoMotorController):
    """Energy pseudomotor controller. Used for scans with Cff fixed"""

    pseudo_motor_roles = ('EnergyCffFixed',)#,'EnergyIncludedAngle')
    motor_roles = ("m3", "gr")

    class_prop = { 'hc':{'Type':'PyTango.DevDouble',
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
                                  }
                            }

    
    def __init__(self, inst, props):
        PseudoMotorController.__init__(self,inst,props)

        self.Cff = 1.0
        self.DiffrOrder = 1.0
        self.IncludedAngle = 1.0
        self.lineDensity = 600.0* 1E-7

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)
    
    def calc_all_physical(self, pseudo_pos, param=None):
        """From a given energy, we calculate the physical
         position for the real motors."""

        energy = pseudo_pos[0]

        waveLen = self.hc / energy
        f1 = self.Cff**2 + 1
        f2 = 1 - self.Cff**2
        K = self.DiffrOrder * waveLen * self.lineDensity
        
        CosAlpha = math.sqrt(-1*K**2 * f1 + 2*math.fabs(K) * math.sqrt(f2**2 + self.Cff**2 * K**2))/math.fabs(f2)

        self.alpha = math.acos(CosAlpha)
        CosBeta = self.Cff * CosAlpha
        self.beta = -math.acos(CosBeta)
        self.theta = (self.alpha - self.beta) * 0.5

        m = ((math.pi/2.0) - self.theta + self.offsetM)*1000 #angle*1000 to have it in mrad
        g = (self.beta + (math.pi/2.0) + self.offsetG)*1000
        return (m,g)

#        if index == 2:
#            energy = pseudo_pos[1]
#            waveLen = self.hc / energy

#            Theta = self.theta
            
#            mkl = self.DiffrOrder * self.lineDensity * waveLen
#            A1 = mkl/2.0 * math.tan(Theta/2)
#            A2 = math.sqrt((math.cos(Theta/2)**2) - (mkl/2.0)**2)

#            beta = -math.acos(A2 - A1)
#            alpha = Theta + beta

#            self.Cff = math.cos(beta) / math.cos(alpha)
            
#            m = ((math.pi/2.0) - Theta/2.0 + self.offsetM)*1000 #angle*1000 to have it in mrad
#            g = (beta + (math.pi/2.0) - self.offsetG)*1000
#            return (m,g)
            
    def calc_all_pseudo(self, physical_pos, param=None):
        """From the real motor positions, we calculate the pseudomotors positions."""

        beta = (physical_pos[1]/1000) - (math.pi/2.0) - self.offsetG
        theta = (math.pi/2.0) - (physical_pos[0]/1000) - self.offsetM
        alpha = (2.0*theta) + beta
        wavelength = (math.sin(alpha) + math.sin(beta)) / (self.DiffrOrder * self.lineDensity)
        
        if wavelength == 0.0:
            energy = 0
        else:
            energy = self.hc / wavelength
        return energy

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

    def SetExtraAttributePar(self, axis, name, value):
        if name.lower() == "cff":
            self.Cff = value

        if name.lower() == "diffrorder":
            self.DiffrOrder = value
  