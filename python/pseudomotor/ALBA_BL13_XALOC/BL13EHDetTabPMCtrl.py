import math
from sardana import pool
from sardana.pool.controller import PseudoMotorController

class TwoLeggedTable():
  """ This formulas units are: 'm' for distances and 'rad' for angles. """
  
  def get_trans_1(self, dist_1, trans, rot):
    return trans - (dist_1 * math.tan(rot))
  
  def get_trans_2(self, dist_2, trans, rot):
    return trans + (dist_2 * math.tan(rot))
  
  def get_trans(self, dist_1, dist_2, trans_1, trans_2):
    return (dist_2 * trans_1 + dist_1 * trans_2)/(dist_1 + dist_2)
  
  def get_rot(self, dist_1, dist_2, trans_1, trans_2):
    return math.atan2((trans_2 - trans_1), (dist_1 + dist_2))
  
class DetTab_Z_and_Pitch(PseudoMotorController, TwoLeggedTable):
  """ The PseudoMotor controller for the Pilatus 6M Table pitch.
      User units must be: mm for distances and mrad for angles.
  """

  pseudo_motor_roles = ('z', 'pitch')
  motor_roles = ('z1back', 'z2front')

  DIST_1 = 117.8 # at 400 mm from sample
  DIST_2 = 1701 - DIST_1

  def __init__(self, inst, props, *args, **kwargs):
    PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

  def CalcPhysical(self, index, pseudos, curr_physicals):
    return self.CalcAllPhysical(pseudos, curr_physicals)[index - 1]

  def CalcPseudo(self, index, physicals, curr_pseudos):
    return self.CalcAllPseudo(physicals, curr_pseudos)[index - 1]

  def CalcAllPhysical(self, pseudos, curr_physicals):
    z, pit = pseudos
    
    dist_1_m = self.DIST_1 / 1000.0
    dist_2_m = self.DIST_2 / 1000.0
    
    z_m = z / 1000.0
    pit_rad = pit / 1000.0

    z_1_m = self.get_trans_1(dist_1_m, z_m, pit_rad)
    z_2_m = self.get_trans_2(dist_2_m, z_m, pit_rad)

    z_1 = z_1_m * 1000
    z_2 = z_2_m * 1000
    
    return (z_1, z_2)

  def CalcAllPseudo(self, physicals, curr_pseudos):
    z_1, z_2 = physicals

    dist_1_m = self.DIST_1 / 1000.0
    dist_2_m = self.DIST_2 / 1000.0
    
    z_1_m = z_1 / 1000.0
    z_2_m = z_2 / 1000.0

    z_m = self.get_trans(dist_1_m, dist_2_m, z_1_m, z_2_m)
    pit_rad = self.get_rot(dist_1_m, dist_2_m, z_1_m, z_2_m)

    z = z_m * 1000
    pit = pit_rad * 1000

    return (z, pit)
  
if __name__ == '__main__':
  pass
  ### z_ctrl = DetTab_Z_and_Pitch('a_name',{})
  ### z_ctrl.name = 'a_name'
  ### tests = [(0,0), (0, -1), (5, 5), (6, 4), (4, 6)]
  ### # Expected output:
  ### # (0, 0) (0.0, 0.0) (0.0, 0.0)
  ### # (0, -1) (-0.069253380364491482, -0.58788940905076137) (0.0, -1.0000000000000002)
  ### # (5, 5) (5.0, 0.0) (5.0, 5.0)
  ### # (6, 4) (5.8614932392710166, -1.1757784117362333) (6.0, 3.9999999999999991)
  ### # (4, 6) (4.1385067607289834, 1.1757784117362333) (4.0, 6.0000000000000009)
  ### 
  ### for test in tests:
  ###   pseudo = z_ctrl.calc_all_pseudo(test)
  ###   physical = z_ctrl.calc_all_physical(pseudo)
  ###   print test, pseudo, physical
