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
  
class DiffTab_Z_and_Pitch(PseudoMotorController, TwoLeggedTable):
  """ The PseudoMotor controller for the MD2M Table pitch.
      User units must be: mm for distances and mrad for angles.
  """

  pseudo_motor_roles = ('z', 'pitch')
  motor_roles = ('z1', 'z2')

  DIST_1 = 1179.75
  DIST_2 = 286.25

  def calc_physical(self, index, pseudos):
    return self.calc_all_physical(pseudos)[index - 1]

  def calc_pseudo(self, index, physicals):
    return self.calc_all_pseudo(physicals)[index - 1]

  def calc_all_physical(self, pseudos):
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

  def calc_all_pseudo(self, physicals):
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

class DiffTab_X_and_Yaw(PseudoMotorController):
  """
  From: 	Jordi Juanhuix <juanhuix@cells.es>
  To: 	'Guifre Cuni' <gcuni@cells.es>
  Subject: 	Transformacions x i yaw per DIFFTAB
  Date: 	05/13/2010 10:44:38 AM
  Transformacions Motor->Pseudomotor
  diftabx = diftabxf
  diftabyaw = ArcTan[(diftabxb-diftabxf)/1157.50]    (* rad *)
  Transformacions Pseudomotor ->Motor
  diftabxf = diftabx;
  diftabxb = Tan[diftabyaw]*1157.50+diftabx
  """

  pseudo_motor_roles = ('x', 'yaw')
  motor_roles = ('x1back', 'x2front')

  DIST_1 = 1157.50

  def calc_physical(self, index, pseudos):
    return self.calc_all_physical(pseudos)[index - 1]

  def calc_pseudo(self, index, physicals):
    return self.calc_all_pseudo(physicals)[index - 1]

  def calc_all_physical(self, pseudos):
    x, yaw = pseudos
    
    dist_1_m = self.DIST_1 / 1000.0
    
    x_m = x / 1000.0
    yaw_rad = yaw / 1000.0

    x_1_back_m = x_m + (dist_1_m * math.tan(yaw_rad))
    x_2_front_m = x_m

    x_1_back = x_1_back_m * 1000
    x_2_front = x_2_front_m * 1000

    return (x_1_back, x_2_front)

  def calc_all_pseudo(self, physicals):
    x_1_back, x_2_front = physicals

    dist_1_m = self.DIST_1 / 1000.0
    
    x_1_back_m = x_1_back / 1000.0
    x_2_front_m = x_2_front / 1000.0

    x_m = x_2_front_m
    yaw_rad = math.atan2((x_1_back_m - x_2_front_m), dist_1_m)

    x = x_m * 1000
    yaw = yaw_rad * 1000

    return (x, yaw)


  
if __name__ == '__main__':
  # Just some unit tests of the computation
  
  z_ctrl = DiffTab_Z_and_Pitch('a_name',{})
  z_ctrl.name = 'a_name'

	# Carles Colldelram: inc z 1mm => PIT = 0.68 mrad
	# Jordi: z1=11, z2=10 => Z = 10.1953 mm
  tests = [(0,0), (0, 1), (11,10), (-10, 10)]
  for test in tests:
    pseudo = z_ctrl.calc_all_pseudo(test)
    physical = z_ctrl.calc_all_physical(pseudo)
    print test, pseudo, physical


  print '\n'*5
  x_ctrl = DiffTab_X_and_Yaw('a_name',{})
  x_ctrl.name = 'a_name'
	
	# Carles Colldelram: inc x 1mm => YAW = 0.86 mrad
	# Jordi: x1=11, x2=10 => X = 10 mm
	#        X=2 mm, YAW=2 mrad => x1=4.315 mm, x2=2mm
  tests = [(0,0), (0, 1), (11,10), (-10, 10)]
  for test in tests:
    pseudo = x_ctrl.calc_all_pseudo(test)
    physical = x_ctrl.calc_all_physical(pseudo)
    print test, pseudo, physical
    print test, pseudo, physical
    print x_ctrl.calc_all_physical([2,2])
  
