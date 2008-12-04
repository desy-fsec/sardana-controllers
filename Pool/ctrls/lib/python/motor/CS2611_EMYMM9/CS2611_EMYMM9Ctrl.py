import PyTango
import pool
import MotorController
import array
import sys
import time

class YMM0009:

	@staticmethod
	def getRange(level):
		if 1e-13 <= level and level < 1e-9:
			return 1
		elif 1e-9 <= level and level < 1e-8:
			return 2
		elif 1e-8 <= level and level < 1e-7:
			return 3
		elif 1e-7 <= level and level < 1e-6:
			return 4
		elif 1e-6 <= level and level < 1e-5:
			return 5
		elif 1e-5 <= level and level <= 1e-4:
			return 6
		else:
			print "YMM009","Could not calculate correct range for "+str(level)+" input."
			if level < 1e-13:
				print "Returning lowest range (1)"
				return 1
			else:
				print "Returning highest range (6)"
				return 6
		
	@staticmethod
	def getIntegrationTime(range):
		if range == 1:
			return 1
		elif range == 2:
			return 0.1
		elif range == 3:
			return 0.01
		elif range == 4:
			return 0.05
		elif range == 5:
			return 0.001
		elif range == 6:
			#return 0.0001
			# MORE TIME IS NEEDED...
			return 0.0007
		
class CS2611_EMYMM9Controller(MotorController.MotorController):
	"""This class is the Tango Sardana motor controller for the
	Keithley 2611 Current Source Motor and the Oxford Danfysik Electro Meter
	(they are not motors, but are used for a test scan)"""

	ctrl_features = []

	class_prop = {'CS_SerialCh':{'Type':'PyTango.DevString'
															 ,'Description':'Communication channel name for the CurrentSource serial line.'},
								'EM_SerialCh':{'Type':'PyTango.DevString'
															 ,'Description':'Communication channel name for the ElectroMeter serial line.'},
								'EM_CS_Ch':{'Type':'PyTango.DevString'
														,'Description':'The EM\'s Channel where CS output is connected.'
														,'DefaultValue':"2"},
								'ControllerNumber':{'Type':'PyTango.DevLong'
																		,'Description':'ControllerNumber','DefaultValue':1}}

	gender = "Motor"
	model = "2611"
	organization = "Keithley + Oxford Danfysik"
	image = "CS2611_EMYMM9.png"
	logo = "Keithley-OxfordDanfysik.png"

	MaxDevice = 3
	cs_com_channel = None
	em_com_channel = None
	em_range = 0
	em_freq = 0

	usingSerial = False
	
	DEBUG = False
	debug_pos = [10,1,100000]
	lastStartTime = time.time()
	
	def __init__(self,inst,props):
		MotorController.MotorController.__init__(self,inst,props)

	def getComChannel(self,channel):
		return pool.PoolUtil().get_com_channel(self.inst_name,channel)

	def eventReceived(self,event):
		print "[CS2611_EMYMM9Controller] Received event: ",event

### 3.1.2.4 Methods to create/remove motor from controller
	def AddDevice(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In AddDevice method for axis",axis
		if self.DEBUG:
			print "In debug, Adding device "+str(axis)
			return
		if axis == 1:
			self.cs_com_channel = self.getComChannel(self.CS_SerialCh)
			self.cs_com_channel.open()
			cmd = "smua.source.func = smua.OUTPUT_DCAMPS"
			cmd += ";smua.source.limiti = 1e-4"
			cmd += ";smua.source.leveli = 1e-5"
			cmd += ";smua.source.output = smua.OUTPUT_ON"
			self._sendSetCommand(self.cs_com_channel,cmd)
			#cmd += ";print(smua.source.leveli)"
			#level = float(self._sendCommand(self.cs_com_channel,cmd))
			print "[CS2611_EMYMM9Controller]",self.inst_name,": Added cs motor: Current Source."
		elif axis == 2:
			self.em_com_channel = self.getComChannel(self.EM_SerialCh)
			self.em_com_channel.open()
			self._sendSetCommand(self.em_com_channel,"*RST0")
			time.sleep(0.05)
			self._sendSetCommand(self.em_com_channel,":CONF0:SINGLE")
			time.sleep(0.05)
			self.em_range = float(self._sendCommand(self.em_com_channel,":CONF0:CURR:RANG?"))
			print "[CS2611_EMYMM9Controller]",self.inst_name,": Added range motor: Electrometer Range: "+str(self.em_range)
		elif axis == 3:
			self.em_freq = float(self._sendCommand(self.em_com_channel,":READ0:CURR"+self.EM_CS_Ch+"?"))
			print "[CS2611_EMYMM9Controller]",self.inst_name,": Added freq motor: Electrometer Output Frequency: "+str(self.em_freq)

	def DeleteDevice(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In DeleteDevice method for axis",axis
		pass

	### 3.1.2.5 Methods to move motor(s)
	def PreStartAll(self):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In PreStartAll method"
		pass

	def PreStartOne(self,axis,pos):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In PreStartOne method for axis",axis," with pos",pos
		return True

	def StartOne(self,axis,pos):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In StartOne method for axis",axis," with pos",pos
		if self.DEBUG:
			print "In debug, setting the axis "+str(axis)+" with position "+str(pos)
			self.debug_pos[axis - 1] = pos
			return

		if axis == 1:
			# TURN OFF THE SOURCE
			#cmd = "smua.source.output = smua.OUTPUT_OFF"
			#cmd += ";print(smua.source.leveli)"
			#self._sendCommand(self.cs_com_channel,cmd)
			self.lastStartTime = time.time()
			# FIX FREQUENCY RANGE IN ELECTROMETER IF NEEDED
			theoretical_range = YMM0009.getRange(pos)
			if self.em_range != theoretical_range:
				time.sleep(0.05)
				self._sendSetCommand(self.em_com_channel,":CONF0:CURR:RANG "+str(theoretical_range))
				time.sleep(0.05)
				self.em_range = float(self._sendCommand(self.em_com_channel,":CONF0:CURR:RANG?"))
				# The time to let the frequency settle should be bigger when changing range:
				self.lastStartTime = time.time() + 1

			# SET CURRENT SOURCE AND TURN ON
			cmd = "smua.source.leveli = "+str(pos)
			cmd += ";print(smua.source.leveli)"
			self._sendCommand(self.cs_com_channel,cmd)
		elif (axis == 2 or axis == 3):
			print "[CS2611_EMYMM9Controller]",self.inst_name,": Sorry, can't move this \"motor\""

	def StartAll(self):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In StartAll method"
		pass

### 3.1.2.6 Methods to read motor(s) position
	def PreReadAll(self):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In PreReadAll method"
		pass

	def PreReadOne(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In PreReadOne method for axis",axis
		pass

	def ReadAll(self):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In ReadAll method"
		pass

	def ReadOne(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In ReadOne method for axis",axis
		if self.DEBUG:
			print "In debug, returning "+str(self.debug_pos[axis - 1])
			return self.debug_pos[axis - 1]
		if axis == 1:
			level = float(self._sendCommand(self.cs_com_channel,"print(smua.source.leveli)"))
			return level
		elif axis == 2:
			#time.sleep(0.05)
			self.em_range = float(self._sendCommand(self.em_com_channel,":CONF0:CURR:RANG?"))
			return self.em_range
		elif axis == 3:
			#time.sleep(0.05)
			self.em_freq = float(self._sendCommand(self.em_com_channel,":READ0:CURR"+self.EM_CS_Ch+"?"))
			return self.em_freq

### 3.1.2.7 Methods to get motor(s) state
	def PreStateAll(self):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In PreStateAll method"
		pass

	def PreStateOne(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In PreStateOne method for axis",axis
		pass

	def StateAll(self):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In StateAll method"
		pass

	def StateOne(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In StateOne method for axis",axis
		if self.DEBUG:
			print "In debug, returning the same: (PyTango.DevState.ON and limits = 0)"

		status = PyTango.DevState.ON
		limits = 0
		now = time.time()
		theoretical_integTime = YMM0009.getIntegrationTime(self.em_range)
		if axis == 1 and (now - self.lastStartTime) < theoretical_integTime:
			status = PyTango.DevState.MOVING

		return (int(status), limits)

### 3.1.2.8 Methods to configure a motor
	def SetPar(self,axis,name,value):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In SetPar method for axis",axis,"name=",name,"value=",value
		pass

	def GetPar(self,axis,name):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In GetPar method for axis",axis," name=",name
		return 0

	def GetExtraAttributePar(self,axis,name):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In GetExtraAttributePar method for axis",axis," name=",name
		pass
	
	def SetExtraAttributePar(self,axis,name,value):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In SetExtraAttributePar method for axis",axis," name=",name
		pass

### 3.1.2.9 Methods to configure a motor
	def AbortOne(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In Abort for axis",axis
		if self.DEBUG:
			print "In debug, doing nothing"
			return

		if axis == 1:
			cmd = "smua.source.output = smua.OUTPUT_OFF"
			cmd += ";print(smua.source.leveli)"
			self._sendCommand(self.cs_com_channel,cmd)
		pass

	def StopOne(self,axis):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In StopOne for axis",axis
		if self.DEBUG:
			print "In debug, doing nothing"
			return

		if axis == 1:
			cmd = "smua.source.output = smua.OUTPUT_OFF"
			cmd += ";print(smua.source.leveli)"
			self._sendCommand(self.cs_com_channel,cmd)
		pass

	def DefinePosition(self, axis, position):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": In DefinePosition for axis",axis,"pos=",position
		pass

	def __del__(self):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": Exiting..."
		print "[DONE]"

	def _sendSetCommand(self,channel,cmd):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": _sendSetCommand(",channel,",",cmd,")"
		while self.usingSerial:
			print "."
			time.sleep(0.1)
		cmdarray = array.array('B', cmd).tolist()
		self.usingSerial = True
		channel.write(cmdarray)
		self.usingSerial = False

	def _sendCommand(self,channel,cmd):
		#print "[CS2611_EMYMM9Controller]",self.inst_name,": _sendCommand(",channel,",",cmd,")"
		while self.usingSerial:
			print "*"
			time.sleep(0.1)
		cmdarray = array.array('B', cmd).tolist()
		self.usingSerial = True
		res = channel.writeread(cmdarray)
		self.usingSerial = False
		#channel.write(cmdarray)
		#time.sleep(0.05)
		#res = channel.readline()
		s = array.array('B', res).tostring().strip(chr(6)+chr(10))
		if s == "":
			print "WARNING: '"+cmd+"' HAD NO ANSWER (ASSUMING 0)"
			return "0"
		return s
