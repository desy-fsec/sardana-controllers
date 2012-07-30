import PyTango
import pool
from pool import MotorController
import array
import sys

#from visa import *
#from pyvisa import *

class E516:
	ERRORS = {
		0: 'No error',
		1: 'Parameter syntax error',
		5: 'Cannot set possition when servo is off',
		10: 'Controller was stopped',
		18: 'Invalid macro name',
		19: 'Error while recording macro',
		20: 'Macro not found',
		23: 'Illegal axis identifier',
		26: 'Parameter missing',
		301: 'Send buffer overflow',
		302: 'Voltage out of limits',
		303: 'Cannot set voltage when servo on',
		304: 'Received command is too long',
		307: 'Timeout while receiving command',
		209: 'Inusfficient space to store macro'
	}

	@staticmethod
	def getErrorMessage(errorcode):
		if errorcode in E516.ERRORS:
			return E516.ERRORS[errorcode]
		else:
			return "Unknown error"

	@staticmethod
	def getAxis(axis):
		if axis == 1:
			return "A"
		elif axis == 2:
			return "B"
		elif axis == 3:
			return "C"
		else:
			PyTango.Except.throw_exception("E516",E516.getErrorMessage(23) , "getAxis()")

class PIE516Controller(MotorController):
	"""This class is the Tango Sardana motor controller for the
	Physikinstrumente Computer Interface and Display Module E516"""


	ctrl_features = []

	class_prop = {'SerialCh':{'Type':'PyTango.DevString'
							  ,'Description':'Communication channel name for the serial line'}}


	ctrl_extra_attributes = {'Servo':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'
																		,'Description':'Whether the piezo is in closed loop or not.'}
													 ,'Vxmicron':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'
																		,'Description':'The ratio [100V / total um] to tranlsate linearly.'}}
	gender = "Motor"
	model = "E-516"
	organization = "Physikinstrumente"
	image = "pi_E516.png"
	logo = "Physikinstrumente.png"

	MaxDevice = 3
	com_channel = None
	#e516 = None

	SERVO = 'Servo'
	VXMICRON = 'Vxmicron'
	POS = 'POS'
	VOL = 'VOL'
	NLM = 'NLM'
	PLM = 'PLM'
	VMI = 'VMI'
	VMA = 'VMA'
	
	servoProps = {}

	def __init__(self,inst,props):
		MotorController.__init__(self,inst,props)
		#self.e516 = instrument("visa://pc023.cells.es/PIE516",term_chars=LF)
		#self.e516.write("ONL 1")


	def getComChannel(self):
		return pool.PoolUtil().get_com_channel(self.inst_name ,self.SerialCh)


### 3.1.2.4 Methods to create/remove motor from controller
	def AddDevice(self,axis):
		#print "[E516Controller]",self.inst_name,": In AddDevice method for axis",axis
		if self.com_channel == None:
			try:
				self.com_channel = self.getComChannel()
				self.com_channel.Open()
				self._writeCommand("ONL 1")
			except Exception,e:
				print "[PIE516Controller]",self.inst_name,": Could not communicate with serial channel: "+self.SerialCh
		axisName = E516.getAxis(axis)
		#self.e516.write("VCO "+axisName+"1")
		self._writeCommand("VCO "+axisName+"1")
		self.servoProps[axisName] = {self.SERVO:True,self.VXMICRON:1.0}
		self._updatePosition(axis)
		#self._updateLimits(axis)
		self._writeCommand("VCO "+axisName+"1")
		# DO A MOVEMENT SO THE ONT? COMMAND WORKS PROPERLY
		self._writeCommand("MOV "+axisName+str(self.servoProps[axisName][self.POS]))


	def DeleteDevice(self,axis):
		#print "[E516Controller]",self.inst_name,": In DeleteDevice method for axis",axis
		pass


### 3.1.2.5 Methods to move motor(s)
	def PreStartAll(self):
		#print "[E516Controller]",self.inst_name,": In PreStartAll method"
		pass


	def PreStartOne(self,axis,pos):
		#print "[E516Controller]",self.inst_name,": In PreStartOne method for axis",axis," with pos",pos
		return True


	def StartOne(self,axis,pos):
		#print "[E516Controller]",self.inst_name,": In StartOne method for axis",axis," with pos",pos
		axisName = E516.getAxis(axis)
		if self.servoProps[axisName][self.SERVO]:
			#self.e516.write("SVO "+axisName+"1")
			#self.e516.write("MOV "+axisName+str(pos))
			self._writeCommand("SVO "+axisName+"1")
			self._writeCommand("MOV "+axisName+str(pos))
		else:
			vol = pos * self.servoProps[axisName][self.VXMICRON]
			#self.e516.write("SVO "+axisName+"0");
			#self.e516.write("SVA "+axisName+str(vol))
			self._writeCommand("SVO "+axisName+"0");
			self._writeCommand("SVA "+axisName+str(vol))


	def StartAll(self):
		#print "[E516Controller]",self.inst_name,": In StartAll method"
		pass


### 3.1.2.6 Methods to read motor(s) position
	def PreReadAll(self):
		#print "[E516Controller]",self.inst_name,": In PreReadAll method"
		pass


	def PreReadOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In PreReadOne method for axis",axis
		self._updatePosition(axis)


	def ReadAll(self):
		#print "[E516Controller]",self.inst_name,": In ReadAll method"
		pass


	def ReadOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In ReadOne method for axis",axis
		axisName = E516.getAxis(axis)
		return self.servoProps[axisName][self.POS]


### 3.1.2.7 Methods to get motor(s) state
	def PreStateAll(self):
		#print "[E516Controller]",self.inst_name,": In PreStateAll method"
		pass


	def PreStateOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In PreStateOne method for axis",axis
		self._updatePosition(axis)
		#self._updateLimits(axis)
		pass


	def StateAll(self):
		#print "[E516Controller]",self.inst_name,": In StateAll method"
		pass


	def StateOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In StateOne method for axis",axis
		axisName = E516.getAxis(axis)
		status = PyTango.DevState.ON
		ont = self._writeReadCommand("ONT? "+axisName)
		if ont != None and int(ont) == 0:
			status = PyTango.DevState.MOVING

		# NOW, NO LIMITS CONTROL
		limits = 0
		return (int(status), limits)

		lower = self.servoProps[axisName][self.NLM]
		upper = self.servoProps[axisName][self.PLM]
		pos = self.servoProps[axisName][self.POS]

		# LIMITS CALCULATION
		limits = 0
		if (lower == pos) and (upper == pos):
			limits = 6
		elif (lower == pos):
			limits = 4
		elif (upper == pos):
			limits = 2
		else:
			limits = 0



### 3.1.2.8 Methods to configure a motor
	def SetPar(self,axis,name,value):
		#print "[E516Controller]",self.inst_name,": In SetPar method for axis",axis,"name=",name,"value=",value
		axisName = E516.getAxis(axis)
		name = name.lower()
		if name == "velocity":
			#self.e516.write("VCO "+axisName+"1")
			#self.e516.write("VEL "+axisName+str(value))
			self._writeCommand("VCO "+axisName+"1")
			self._writeCommand("VEL "+axisName+str(value))
		elif name == "base_rate":
			pass
		elif name == "acceleration" or name == "deceleration":
			pass
		elif name == "backlash":
			pass


	def GetPar(self,axis,name):
		#print "[E516Controller]",self.inst_name,": In GetPar method for axis",axis," name=",name
		axisName = E516.getAxis(axis)
		name = name.lower()
		if name == "velocity":
			#return float(self.e516.ask("VEL? "+axisName))
			return float(self._writeReadCommand("VEL? "+axisName))
		elif name == "base_rate":
			return 0
		elif name == "acceleration" or name == "deceleration":
			return 0
		elif name == "backlash":
			return 0
		return 0


	def GetExtraAttributePar(self,axis,name):
		# IMPLEMENTED THE EXTRA ATTRIBUTES 'Servo','Vxmicron' PER AXIS
		return self.servoProps[E516.getAxis(axis)][name]


	def SetExtraAttributePar(self,axis,name,value):
		# IMPLEMENTED THE EXTRA ATTRIBUTES 'Servo','Vxmicron' PER AXIS
		self.servoProps[E516.getAxis(axis)][name] = value


### 3.1.2.9 Methods to configure a motor
	def AbortOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In Abort for axis",axis
		#self.e516.write("STP "+E516.getAxis(axis))
		self._writeCommand("STP "+E516.getAxis(axis))


	def StopOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In StopOne for axis",axis
		#self.e516.write("STP "+E516.getAxis(axis))
		self._writeCommand("STP "+E516.getAxis(axis))


	def DefinePosition(self, axis, position):
		#print "[E516Controller]",self.inst_name,": In DefinePosition for axis",axis,"pos=",position
		pass


	def __del__(self):
		#print "[E516Controller]",self.inst_name,": Exiting..."
		# Cannot close com channel here. The pool has already shutdown the comunication device
		#self.serial.close()
		#if self.serial_state_event_id != -1:
		#	getComChannel().unsubscribe_event(self.serial_state_event_id)
		print "[DONE]"


	def _updatePosition(self,axis):
		axisName = E516.getAxis(axis)
		#pos = self.e516.ask("POS? "+axisName)		
		pos = self._writeReadCommand("POS? "+axisName)		
		self.servoProps[axisName][self.POS] = float(pos)
		#vol = self.e516.ask("VOL? "+axisName)		
		vol = self._writeReadCommand("VOL? "+axisName)		
		self.servoProps[axisName][self.VOL] = float(vol)
		if not self.servoProps[axisName][self.SERVO]:
			self.servoProps[axisName][self.POS] = float(vol) / self.servoProps[axisName][self.VXMICRON]


	def _updateLimits(self,axis):
		pass
	
		axisName = E516.getAxis(axis)
		#lower = self.e516.ask("NLM? "+axisName)		
		lower = self._writeReadCommand("NLM? "+axisName)		
		self.servoProps[axisName][self.NLM] = float(lower)
		#upper = self.e516.ask("PLM? "+axisName)		
		upper = self._writeReadCommand("PLM? "+axisName)		
		self.servoProps[axisName][self.PLM] = float(upper)
		#lowerV = self.e516.ask("VMI? "+axisName)		
		lowerV = self._writeReadCommand("VMI? "+axisName)		
		self.servoProps[axisName][self.VMI] = float(lowerV)
		if not self.servoProps[axisName][self.SERVO]:
			self.servoProps[axisName][self.NLM] = float(lowerV) / self.servoProps[axisName][self.VXMICRON]
		#upperV = self.e516.ask("PLM? "+axisName)		
		upperV = self._writeReadCommand("PLM? "+axisName)		
		self.servoProps[axisName][self.VMA] = float(upperV)
		if not self.servoProps[axisName][self.SERVO]:
			self.servoProps[axisName][self.PLM] = float(upperV) / self.servoProps[axisName][self.VXMICRON]


	def _checkError(self,cmd):
		#print "[E516Controller]",self.inst_name,": _checkError()"
		res = self._writeReadCommand("ERR?",check = False)
		if res != None and int(res) > 0:
			PyTango.Except.throw_exception("E516",E516.getErrorMessage(int(res)) , "command: "+cmd)


	def _writeCommand(self,cmd):
		#cmdarray = array.array('B',cmd).tolist()
		cmdarray = array.array('B',cmd)
		self.com_channel.Write(cmdarray)
		self._checkError(cmd)


	def _writeReadCommand(self,cmd,check = True):
		#cmdarray = array.array('B',cmd).tolist()
		cmdarray = array.array('B',cmd)
		ansarray = self.com_channel.WriteRead(cmdarray)
		ans = array.array('B',ansarray).tostring()
		if check:
			#self._checkError(cmd)
			pass
		return ans
