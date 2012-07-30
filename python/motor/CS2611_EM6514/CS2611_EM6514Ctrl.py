import PyTango
import pool
import MotorController
import array
import sys
import time

from visa import *
from pyvisa import *

class CS2611_EM6514Controller(MotorController.MotorController):
	"""This class is the Tango Sardana motor controller for the
	Keithley 2611 Current Source Motor and the Keithley 6514 Electro Meter
	(they are not motors, but are used for a test scan)"""

	ctrl_features = []

	gender = "Motor"
	model = "2611"
	organization = "Keithley"
	image = "CS2611_EM6514.png"
	logo = "Keithley.png"

	MaxDevice = 3
	cs = None
	em = None
	
	DEBUG = False
	debug_pos = [10,1,100000]
	
	def __init__(self,inst,props):
		MotorController.MotorController.__init__(self,inst,props)

	def eventReceived(self,event):
		print "[CS2611_EM6514Controller] Received event: ",event

### 3.1.2.4 Methods to create/remove motor from controller
	def AddDevice(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In AddDevice method for axis",axis
		if self.DEBUG:
			print "In debug, Adding device "+str(axis)
			return
		if axis == 1:
			self.cs = instrument("visa://pc023.cells.es/Keithley2611CS")
			cmd = "smua.source.func = smua.OUTPUT_DCAMPS"
			cmd += ";smua.source.limiti = 1e-3"
			cmd += ";smua.source.leveli = 1e-5"
			cmd += ";smua.source.output = smua.OUTPUT_ON"
			self.cs.write(cmd)
			level = float(self.cs.ask("print(smua.source.leveli)"))
			print "[CS2611_EM6514Controller]",self.inst_name,": Added cs motor: Current Source: "+str(level)
		elif axis == 2:
			self.em = instrument("visa://pc023.cells.es/Keithley6514EM")
			cmd = "FUNC 'CURR'"
			cmd += ";CURR:RANG:AUTO ON"
			cmd += ";ARM:SOUR IMM"
			cmd += ";ARM:COUN 1"
			cmd += ";ARM:TIM 0.001"
			cmd += ";TRIG:SOUR IMM"
			cmd += ";TRIG:COUN 1"
			cmd += ";TRIG:DEL:AUTO OFF"
			cmd += ";TRIG:DEL 0"
			self.em.write(cmd)
			em_range = float(self.em.ask("CURR:RANG?"))
			print "[CS2611_EM6514Controller]",self.inst_name,": Added em_range motor: Electrometer Range: "+str(em_range)
		elif axis == 3:
			em_curr = float(self.em.ask("MEAS:CURR?").split(",")[0])
			print "[CS2611_EM6514Controller]",self.inst_name,": Added em_curr motor: Electrometer Input Current: "+str(em_curr)

	def DeleteDevice(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In DeleteDevice method for axis",axis
		pass

	### 3.1.2.5 Methods to move motor(s)
	def PreStartAll(self):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In PreStartAll method"
		pass

	def PreStartOne(self,axis,pos):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In PreStartOne method for axis",axis," with pos",pos
		return True

	def StartOne(self,axis,pos):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In StartOne method for axis",axis," with pos",pos
		if self.DEBUG:
			print "In debug, setting the axis "+str(axis)+" with position "+str(pos)
			self.debug_pos[axis - 1] = pos
			return

		if axis == 1:
			self.cs.write("smua.source.leveli = "+str(pos))
		elif (axis == 2 or axis == 3):
			print "[CS2611_EM6514Controller]",self.inst_name,": Sorry, can't move this \"motor\""

	def StartAll(self):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In StartAll method"
		pass

### 3.1.2.6 Methods to read motor(s) position
	def PreReadAll(self):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In PreReadAll method"
		pass

	def PreReadOne(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In PreReadOne method for axis",axis
		pass

	def ReadAll(self):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In ReadAll method"
		pass

	def ReadOne(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In ReadOne method for axis",axis
		if self.DEBUG:
			print "In debug, returning "+str(self.debug_pos[axis - 1])
			return self.debug_pos[axis - 1]
		if axis == 1:
			level = float(self.cs.ask("print(smua.source.leveli)"))
			return level
		elif axis == 2:
			em_range = float(self.em.ask("CURR:RANG?"))
			return em_range
		elif axis == 3:
			em_curr = float(self.em.ask("MEAS:CURR?").split(",")[0])
			return em_curr

### 3.1.2.7 Methods to get motor(s) state
	def PreStateAll(self):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In PreStateAll method"
		pass

	def PreStateOne(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In PreStateOne method for axis",axis
		pass

	def StateAll(self):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In StateAll method"
		pass

	def StateOne(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In StateOne method for axis",axis
		if self.DEBUG:
			print "In debug, returning the same: (PyTango.DevState.ON and limits = 0)"

		status = PyTango.DevState.ON
		limits = 0

		return (int(status), limits)

### 3.1.2.8 Methods to configure a motor
	def SetPar(self,axis,name,value):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In SetPar method for axis",axis,"name=",name,"value=",value
		pass

	def GetPar(self,axis,name):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In GetPar method for axis",axis," name=",name
		return 0

	def GetExtraAttributePar(self,axis,name):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In GetExtraAttributePar method for axis",axis," name=",name
		pass
	
	def SetExtraAttributePar(self,axis,name,value):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In SetExtraAttributePar method for axis",axis," name=",name
		pass

### 3.1.2.9 Methods to configure a motor
	def AbortOne(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In Abort for axis",axis
		if self.DEBUG:
			print "In debug, doing nothing"
			return

		if axis == 1:
			self.cs.write("smua.source.output = smua.OUTPUT_OFF")
		pass

	def StopOne(self,axis):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In StopOne for axis",axis
		if self.DEBUG:
			print "In debug, doing nothing"
			return

		if axis == 1:
			self.cs.write("smua.source.output = smua.OUTPUT_OFF")
		pass

	def DefinePosition(self, axis, position):
		#print "[CS2611_EM6514Controller]",self.inst_name,": In DefinePosition for axis",axis,"pos=",position
		pass

	def __del__(self):
		#print "[CS2611_EM6514Controller]",self.inst_name,": Exiting..."
		self.cs.write("smua.source.output = smua.OUTPUT_OFF")
		print "[DONE]"
