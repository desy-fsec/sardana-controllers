import math

from pool import PseudoMotorController
  
class M1_Z_Pitch_Roll_Controller(PseudoMotorController):
  """ The PseudoMotor controller for the MSPD's M1 table: Z, Pitch, Roll.
      User units must be: mm for distances and mrad for angles.
      Pitch rotational axis is in the middle of Y dimension.
      Roll rotational axis is in the middle of X dimension.
     ____________________________
    |                           |
    |                   *mzr    |
    |   *mzc                    |   <-------- beam direction
    |                   *mzl    |
    |___________________________|

      Increasing pitch angle of 1 mrad should increase mzc of 0.63125021041675084 mm    
                                              decrease mzl and mzr of 0.63125021041675084 mm
      Increasing roll angle of 1 mrad should increase mzl of 0.13050004350001742 mm    
                                             decrease mzr of 0.13050004350001742 mm  
  """

  pseudo_motor_roles = ('z', 'pitch', 'roll')
  motor_roles = ('mzc', 'mzl', 'mzr')

  DIM_Y = 1262.5
  DIM_X = 261
#  DIM_Y = 1000
#  DIM_X = 500

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

class M1_X_Yaw_Controller(PseudoMotorController):
  """
    The PseudoMotor controller for the MSPD's M1 table: X, Yaw.
    User units must be: mm for distances and mrad for angles.
    Yaw rotational axis is in the middle of Y dimension.
    
     ____________________________
    |                           |
    |                           |
    |                           |   <-------- beam direction
    |                           |
    |___________________________|
      ^ mx2                  ^ mx1
      
    Increasing yaw angle of 1 mrad should increase mx2 of 0.63125021041675084 mm    
                                          decrease mx1 of 0.63125021041675084 mm  
  """

  pseudo_motor_roles = ('x', 'yaw')
  motor_roles = ('mx1', 'mx2')

  DIM_Y = 1262.50
#  DIM_Y = 1000

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
  
