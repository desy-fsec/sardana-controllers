""" A pseudo motor controller library for the pool used by the test procedure. N
    Not for installation"""

from pool import PseudoMotorController

class DummyGarbage:
	def __init__(self):
		print "Nothing here on DummyGarbage :-("

class DummyMotor01(PseudoMotorController):
	"""Just a silly pseudo motor. It doesn't actually do anything."""
	
	motor_roles = ("Motor on upper Blade","Motor on lower Blade")
	parameters = {}
		
	def calc_physical(self,pseudo_pos,params = None):
		return [5]
	
	def calc_pseudo(self,physical_pos,params = None):
		return [1,1]



class Silly(PseudoMotorController):
	"""Just a silly pseudo motor. It doesn't actually do anything."""
	
	pseudo_motor_roles = ("psd 01", "psd 02", "psd 03", "psd 04")
	motor_roles = ("real 01", "real 02", "real 03", "real 04")
	parameters = {}
		
	def calc_physical(self,pseudo_pos,params):
		return pseudo_pos
	
	def calc_pseudo(self,physical_pos,params):
		return physical_pos

class Silly02(PseudoMotorController):
	"""Just a silly pseudo motor. It doesn't actually do anything."""
	
	pseudo_motor_roles = ("psd 01", "psd 02", "psd 03", "psd 04")
	motor_roles = ("real 01", "real 02", "real 03", "real 04")
	parameters = {}
		
	def calc_physical(self,pseudo_pos,params):
		return pseudo_pos
	
	def calc_pseudo(self,physical_pos,params):
		return physical_pos


class TableHeight(PseudoMotorController):
	"""Controllertable-height pseudomotor with mnemonic t1z that is the average height 
	    of the three real motors t1f, t1b1 and t1b2 that correspond to the table legs. When the height is moved, 
	    each leg is moved by an amount equal to the difference of the current height and the target height. The 
	    current average height needs to be calculated from the current real-motor positions before the new 
	    positions are assigned."""
	
	pseudo_motor_roles = ("t1z",)
	motor_roles = ("t1f", "t1b1", "t1b2")
	class_prop = { 'weight' : {
				       'Description' : 'The table weight',
				       'Type' : 'PyTango.DevDouble',
				       'DefaultValue' : 0.0
				       },
				   'table color' : {
				       'Description' : 'Color value',
				       'Type' : 'PyTango.DevLong',
				       'DefaultValue' : 0
				       },
				   'leg color' : {
				       'Description' : 'Color value',
				       'Type' : 'PyTango.DevLong',
				       'DefaultValue' : 0
				       }
				 }

	def calc_physical(self,index,pseudo_pos):
		# get last known real positions
		# calculate the pseudo position by calling calc_pseudo
		# calculate 
		pass
	
	def calc_pseudo(self,index,physical_pos):
		return (physical_pos[0] + physical_pos[1] + physical_pos[2]) / 3.0
	
	
class SlitV2(PseudoMotorController):
	"""A Slit pseudo motor system for controlling gap and offset pseudo motors."""
	
	gender = "Slit"
	model  = "Enhanced Slit"
	organization = "CELLS - ALBA"
	image = "slit.png"
	logo = "ALBA_logo.png"	
	
	pseudo_motor_roles = ("Gap", "Offset")
	motor_roles = ("sl2t", "sl2b")
	class_prop = { 'print_string' : {
				       'Description' : 'A property for demonstrating a long property',
				       'Type' : 'PyTango.DevString',
				       'DefaultValue' : 'Somebody told me to print a default value'
				       },
				 }
				       	
	def calc_physical(self,index,pseudo_pos):
		half_gap = pseudo_pos[0]/2.0
		if index == 1:
			return pseudo_pos[1] - half_gap
		else:
			return pseudo_pos[1] + half_gap
	
	def calc_pseudo(self,index,physical_pos):
		print self.print_string
		if index == 0:
			return physical_pos[1] - physical_pos[0]
		else:
			return (physical_pos[0] + physical_pos[1])/2.0
	
			
class PropSlit(PseudoMotorController):
	"""A Slit pseudo motor system for controlling gap and offset pseudo motors."""
	
	gender = "Slit"
	model  = "Property filled Slit"
	organization = "CELLS - ALBA"
	image = "slit.png"
	logo = "ALBA_logo.png"	
	
	pseudo_motor_roles = ("Gap", "Offset")
	motor_roles = ("sl2t", "sl2b")
	class_prop = { 'p_long' : {
				       'Description' : 'A property for demonstrating a long property\nActually is more than that:\nIt is to test a multiline description also',
				       'Type' : 'PyTango.DevLong',
				       'DefaultValue' : 987654321
				       },
				   'p_double' : {
				       'Description' : 'A property for demonstrating a double property',
				       'Type' : 'PyTango.DevDouble',
				       'DefaultValue' : 123456.654321
				       },
				   'p_bool' : {
				       'Description' : 'A property for demonstrating a boolean property',
				       'Type' : 'PyTango.DevBoolean',
				       'DefaultValue' : True
				       },
				   'p_string' : {
				       'Description' : 'A property for demonstrating a string property',
				       'Type' : 'PyTango.DevString',
				       'DefaultValue' : 'Some silly default content for a string property'
				       },
				   'p_longArray_tuple' : {
				       'Description' : 'A property for demonstrating a long array property',
				       'Type' : 'PyTango.DevVarLongArray',
				       'DefaultValue' : (9876,12345)
				       },
				   'p_longArray_list' : {
				       'Description' : 'A property for demonstrating a long array property',
				       'Type' : 'PyTango.DevVarLongArray',
				       'DefaultValue' : [9876,54321]
				       },
				   'p_doubleArray_tuple' : {
				       'Description' : 'A property for demonstrating a double array property',
				       'Type' : 'PyTango.DevVarDoubleArray',
				       'DefaultValue' : (5.1,0.44,333.3)
				       },
				   'p_doubleArray_list' : {
				       'Description' : 'A property for demonstrating a double array property',
				       'Type' : 'PyTango.DevVarDoubleArray',
				       'DefaultValue' : [5.1,0.44,333]
				       },
				   'p_boolArray_tuple' : {
				       'Description' : 'A property for demonstrating a boolean array property',
				       'Type' : 'PyTango.DevVarBooleanArray',
				       'DefaultValue' : (True,False)
				       },
				   'p_boolArray_list' : {
				       'Description' : 'A property for demonstrating a boolean array property',
				       'Type' : 'PyTango.DevVarBooleanArray',
				       'DefaultValue' : [True,False]
				       },
				   'p_stringArray_tuple' : {
				       'Description' : 'A property for demonstrating a string array property',
				       'Type' : 'PyTango.DevVarStringArray',
				       'DefaultValue' : ('Some silly default content for a string array property','as a tuple!')
				       },
				   'p_stringArray_list' : {
				       'Description' : 'A property for demonstrating a string array property',
				       'Type' : 'PyTango.DevVarStringArray',
				       'DefaultValue' : ['Some silly default content for a string array property','as a list!']
				       },
				   'p_long_wo_dft' : {
				       'Description' : 'A property for demonstrating a long property without default value',
				       'Type' : 'PyTango.DevLong'
				       }
				 }
				  
	def calc_physical(self,index,pseudo_pos):
		half_gap = pseudo_pos[0]/2.0
		if index == 1:
			return pseudo_pos[1] - half_gap
		else:
			self.deviation	* 5		
			return pseudo_pos[1] + half_gap
	
	def calc_pseudo(self,index,physical_pos):
		print self.p_stringArray_list
		if index == 1:
			return physical_pos[1] - physical_pos[0]
		else:
			return (physical_pos[0] + physical_pos[1])/2.0

