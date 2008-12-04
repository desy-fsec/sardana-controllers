import PyTango
import pool
from pool import MotorController
import array
import sys


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

class E516Controller(MotorController):
	"""This class is the Tango Sardana motor controller for the
	Physikinstrumente Computer Interface and Display Module E516"""

	ctrl_features = []

	class_prop = {'SerialCh':{'Type':'PyTango.DevString'
							  ,'Description':'Communication channel name for the serial line'},
								'ControllerNumber':{'Type':'PyTango.DevLong'
									  ,'Description':'ControllerNumber'
									  ,'DefaultValue':1}}

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

	SERVO = 'Servo'
	VXMICRON = 'Vxmicron'
	POS = 'POS'
	VOL = 'VOL'
	NLM = 'NLM'
	VMI = 'VMI'
	PLM = 'PLM'
	VMA = 'VMA'
	
	servoProps = {}

	def __init__(self,inst,props):

		MotorController.MotorController.__init__(self,inst,props)

#			#print "[E516Controller] registering for communication channel events"
#			#self.serial_state_event_id = com_channel.subscribe_event("State",PyTango.EventType.CHANGE,self.eventReceived,[])
#			#self.serial_state_event_id = -1

	def getComChannel(self):
		return pool.PoolUtil().get_com_channel(self.inst_name ,self.SerialCh)

	def eventReceived(self,event):
		print "[E516Controller] Received event"

### 3.1.2.4 Methods to create/remove motor from controller
	def AddDevice(self,axis):
		#print "[E516Controller]",self.inst_name,": In AddDevice method for axis",axis
		#print "[E516Controller] getting communication channel"
		com_channel = self.getComChannel()
		# THIS SHOULD BE FIXED WHEN THE POOL ACCEPTS A COMMUNICATION CHANNEL WITH STATE OFF
		#if com_channel.status() == PyTango.DevState.OFF:
		com_channel.open()
		self._setCommand("ONL",1)

		axisName = E516.getAxis(axis)
		self._setCommand("VCO", axisName+"1")
		self.servoProps[axisName] = {self.SERVO:False,self.VXMICRON:1.0}

	def DeleteDevice(self,axis):
		#print "[E516Controller]",self.inst_name,": In DeleteDevice method for axis",axis
		pass

### 3.1.2.5 Methods to move motor(s)
	def PreStartAll(self):
		#print "[E516Controller]",self.inst_name,": In PreStartAll method"
		pass

	def PreStartOne(self,axis,pos):
		#print "[E516Controller]",self.inst_name,": In PreStartOne method for axis",axis," with pos",pos
		# IT IS QUITE TRICKY TO TRY TO MOVE AT THE SAME TIME BECAUSE OF SERVO...
		# LET IT BE DONE IN THE StartOne
		return True

	def StartOne(self,axis,pos):
		#print "[E516Controller]",self.inst_name,": In StartOne method for axis",axis," with pos",pos
		axisName = E516.getAxis(axis)
		if self.servoProps[axisName][self.SERVO]:
			self._setCommand("SVO",axisName+"1")
			self._setCommand("MOV",axisName+str(pos))
		else:
			vol = pos * self.servoProps[axisName][self.VXMICRON]
			self._setCommand("SVO",axisName+"0");
			self._setCommand("SVA",axisName+str(vol))

	def StartAll(self):
		#print "[E516Controller]",self.inst_name,": In StartAll method"
		#print "[E516Controller]",self.inst_name,": The hardware controller accepts doing all together (MOV A [B] [C])"
		# IT SHOULD BE BETTER TO STORE ALL INFO AT STARTONE() AND THEN JUST SET ALL TOGETHER HERE
		pass

### 3.1.2.6 Methods to read motor(s) position
	def PreReadAll(self):
		#print "[E516Controller]",self.inst_name,": In PreReadAll method"
		pass

	def PreReadOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In PreReadOne method for axis",axis
		pass

	def ReadAll(self):
		#print "[E516Controller]",self.inst_name,": In ReadAll method"
		self._updatePositions()

	def ReadOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In ReadOne method for axis",axis
		# VALUES HAVE BEEN UPDATED IN THE ReadAll() METHOD ABOVE.
		axisName = E516.getAxis(axis)
		return self.servoProps[axisName][self.POS]

### 3.1.2.7 Methods to get motor(s) state
	def PreStateAll(self):
		#print "[E516Controller]",self.inst_name,": In PreStateAll method"
		pass

	def PreStateOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In PreStateOne method for axis",axis
		pass

	def StateAll(self):
		#print "[E516Controller]",self.inst_name,": In StateAll method"
		self._updatePositions()
		self._updateLimits()
		pass

	def StateOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In StateOne method for axis",axis
		# VALUES HAVE EEN UPDATED IN THE StateAll() METHOD ABOVE.

		axisName = E516.getAxis(axis)
		status = PyTango.DevState.ON
		# WE CAN ASSUME PIEZZOS CAN'T BE IN THE 'MOVING' STATE

		# TO GET THE LIMITS VALUE RETRIEVE NLM?|VMI? AND PLM?|VMA?
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

		return (int(status), limits)

### 3.1.2.8 Methods to configure a motor
	def SetPar(self,axis,name,value):
		#print "[E516Controller]",self.inst_name,": In SetPar method for axis",axis,"name=",name,"value=",value
		name = name.lower()
		if name == "velocity":
			self._setCommand("VCO",E516.getAxis(axis)+"1")
			self._setCommand("VEL",E516.getAxis(axis)+str(value))
		elif name == "base_rate":
			pass
		elif name == "acceleration" or name == "deceleration":
			pass
		elif name == "backlash":
			pass

	def GetPar(self,axis,name):
		#print "[E516Controller]",self.inst_name,": In GetPar method for axis",axis," name=",name
		name = name.lower()
		if name == "velocity":
			return float(self._queryCommand("VEL?",E516.getAxis(axis)))
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
		self._setCommand("STP",E516.getAxis(axis))

	def StopOne(self,axis):
		#print "[E516Controller]",self.inst_name,": In StopOne for axis",axis
		self._setCommand("STP",E516.getAxis(axis))

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

	def _updatePositions(self):
		allLines = self._sendMultiCommand("POS?")
		axis = 1
		for pos in allLines.split(" "):
			axisName = E516.getAxis(axis)
			self.servoProps[axisName][self.POS] = float(pos)
			# IF SERVO IS OFF, THE POS VALUE IS NOT REAL, IT WILL BE
			# UPDATED WHEN QUERYING "VOL?"
			axis = axis + 1

		allLines = self._sendMultiCommand("VOL?")
		axis = 1
		for vol in allLines.split(" "):
			axisName = E516.getAxis(axis)
			self.servoProps[axisName][self.VOL] = float(vol)
			if not self.servoProps[axisName][self.SERVO]:
				self.servoProps[axisName][self.POS] = float(vol) / self.servoProps[axisName][self.VXMICRON]
			axis = axis + 1

	def _updateLimits(self):
		allLines = self._sendMultiCommand("NLM?")
		axis = 1
		for lower in allLines.split(" "):
			axisName = E516.getAxis(axis)
			self.servoProps[axisName][self.NLM] = float(lower)
			# IF SERVO IS OFF, THE NLM VALUE IS NOT REAL, IT WILL BE
			# UPDATED WHEN QUERYING "VMI?"
			axis = axis + 1

		allLines = self._sendMultiCommand("VMI?")
		axis = 1
		for lowerV in allLines.split(" "):
			axisName = E516.getAxis(axis)
			self.servoProps[axisName][self.VMI] = float(lowerV)
			if not self.servoProps[axisName][self.SERVO]:
				self.servoProps[axisName][self.NLM] = float(lowerV) / self.servoProps[axisName][self.VXMICRON]
			axis = axis + 1

		allLines = self._sendMultiCommand("PLM?")
		axis = 1
		for upper in allLines.split(" "):
			axisName = E516.getAxis(axis)
			self.servoProps[axisName][self.PLM] = float(upper)
			# IF SERVO IS OFF, THE PLM VALUE IS NOT REAL, IT WILL BE
			# UPDATED WHEN QUERYING "VMA?"
			axis = axis + 1

		allLines = self._sendMultiCommand("VMA?")
		axis = 1
		for upperV in allLines.split(" "):
			axisName = E516.getAxis(axis)
			self.servoProps[axisName][self.VMA] = float(upperV)
			if not self.servoProps[axisName][self.SERVO]:
				self.servoProps[axisName][self.PLM] = float(upperV) / self.servoProps[axisName][self.VXMICRON]
			axis = axis + 1

	def _setCommand(self, cmd, val):
		#print "[E516Controller]",self.inst_name,": _setCommand(",cmd,",",val,")"
		self._sendSetCommand(cmd+" "+str(val))
		self._checkError()

	def _queryCommand(self, cmd, val):
		#print "[E516Controller]",self.inst_name,": _queryCommand(",cmd,",",val,")"
		res = self._sendCommand(cmd+" "+str(val))
		return  res

	def _queryMultiCommand(self, cmd):
		#print "[E516Controller]",self.inst_name,": _queryMultiCommand(",cmd,")"
		allLines = self._sendMultiCommand(cmd)
		return allLines
		
	def _checkError(self):
		#print "[E516Controller]",self.inst_name,": _checkError()"
		res = self._sendCommand("ERR?")
		if int(res) > 0:
			PyTango.Except.throw_exception("E516",E516.getErrorMessage(int(res)) , "_command()")


	def _sendSetCommand(self, cmd):
		#print "[E516Controller]",self.inst_name,": _sendSetCommand(",cmd,")"
		cmdarray = array.array('B', cmd)
		com_channel = self.getComChannel()
		com_channel.write(cmdarray)  

	def _sendCommand(self, cmd):
		#print "[E516Controller]",self.inst_name,": _sendCommand(",cmd,")"
		cmdarray = array.array('B', cmd)
		com_channel = self.getComChannel()
		res = com_channel.writeread(cmdarray)
		s = array.array('B', res).tostring()
		return s

	def _sendMultiCommand(self, cmd):
		#print "[E516Controller]",self.inst_name,": _sendMultiCommand(",cmd,")"
		cmdarray = array.array('B', cmd)
		com_channel = self.getComChannel()
		com_channel.write(cmdarray)
		moreLines = True
		allLines = ""
		while moreLines:
			line = com_channel.readline();
			allLines = allLines + array.array('B',line).tostring().replace("\n","")
			if line.count(32) == 0:
				moreLines = False
		return allLines
