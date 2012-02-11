import math

from pool import PseudoMotorController

class TwoLeggedTable():
  """ This formulas units are: 'm' for distances and 'rad' for angles.
      This is a generic 'two legged table' class which is able to
      translate from two phyisical translation actuators to the pseudo
      common translation and rotation in a given 'center' point.
  """
  
  def get_trans_1(self, dist_1, trans, rot):
    return trans - (dist_1 * math.tan(rot))
  
  def get_trans_2(self, dist_2, trans, rot):
    return trans + (dist_2 * math.tan(rot))
  
  def get_trans(self, dist_1, dist_2, trans_1, trans_2):
    return (dist_2 * trans_1 + dist_1 * trans_2)/(dist_1 + dist_2)
  
  def get_rot(self, dist_1, dist_2, trans_1, trans_2):
    return math.atan2((trans_2 - trans_1), (dist_1 + dist_2))
  
class TwoLeggedTableController(PseudoMotorController, TwoLeggedTable):
  """ PseudoMotor controller for Two legged table's pitch and z.
      User units must be: mm for distances and mrad for angles.
      z1 is the upstream jack.
  """

  pseudo_motor_roles = ('z', 'pitch')
  motor_roles = ('z1', 'z2')

  class_prop = { 'rotToZ1Distance' : {'Type' : 'PyTango.DevDouble', 'Description' : 'Distance from rotational axis to z1 jack in mm'},
                 'rotToZ2Distance' : {'Type' : 'PyTango.DevDouble', 'Description' : 'Distance from rotational axis to z2 jack in mm'} }

  def __init__(self, inst, props):  
    PseudoMotorController.__init__(self, inst, props)
    self.dist1 = self.rotToZ1Distance / 1000
    self.dist2 = self.rotToZ2Distance / 1000

  def calc_physical(self, index, pseudos):
    return self.calc_all_physical(pseudos)[index - 1]

  def calc_pseudo(self, index, physicals):
    return self.calc_all_pseudo(physicals)[index - 1]

  def calc_all_physical(self, pseudos):
    z, pit = pseudos
    
    z_m = z / 1000.0
    pit_rad = pit / 1000.0

    z_1_m = self.get_trans_1(self.dist1, z_m, pit_rad)
    z_2_m = self.get_trans_2(self.dist2, z_m, pit_rad)

    z_1 = z_1_m * 1000
    z_2 = z_2_m * 1000
   
    return (z_1, z_2)

  def calc_all_pseudo(self, physicals):
    z_1, z_2 = physicals

    z_1_m = z_1 / 1000.0
    z_2_m = z_2 / 1000.0

    z_m = self.get_trans(self.dist1, self.dist2, z_1_m, z_2_m)
    pit_rad = self.get_rot(self.dist1, self.dist2, z_1_m, z_2_m)

    z = z_m * 1000
    pit = pit_rad * 1000

    return (z, pit)
  
