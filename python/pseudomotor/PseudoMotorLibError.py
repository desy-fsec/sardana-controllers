""" A pseudo motor controller library for the pool with a python syntax error.
    This file is to be used in the test procedure only. Not for installation"""

from pool import PseudoMotorController
#import PseudoMotor

class ErrorPseudoMotor(PseudoMotorController):
	some syntax error
	"""Just a silly pseudo motor. It doesn't actually do anything."""
	
	motor_roles = ("Motor on upper Blade","Motor on lower Blade")
	parameters = {}
		
	def calc_physical(self,pseudo_pos,params = None):
		return [5]
	
	def calc_pseudo(self,physical_pos,params = None):
		return [1,1]

