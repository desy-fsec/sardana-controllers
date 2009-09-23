#!/usr/bin/env python

#############################################################################
##
## file :        ImgBeamAanalyzrController.py
##
## description :
##
## project :     Sardana
##
## $Author: sblanch $
##
## copyleft :    Cells / Alba Synchrotron
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Tango-ds.
##
## Tango-ds is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## Tango-ds is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################

import PyTango
from pool import CounterTimerController
import time

class ImgBeamAnalyzerController(CounterTimerController):
	"""This class is the Tango Sardana CounterTimer controller for the Tango ImgBeamAnalyzer device.
	One controller only knows one device, and each counter channel responds to one specific device attribute."""

	class_prop = {'devName':{'Description' : 'ImgBeamAnalyzer Tango device','Type' : 'PyTango.DevString'}}

	MaxDevice = 10 #only one device

	gender = "ImgBeamAnalyzer"
	model = "Ccd Img processor"
	organization = "CELLS - ALBA"

	ImgBeamAnalyzerProxys = {}

	def stateBridge(self,state):
		if state == PyTango.DevState.STANDBY:
			return PyTango.DevState.ON
		if state == PyTango.DevState.RUNNING:
			return PyTango.DevState.MOVING
		if state == PyTango.DevState.FAULT:
			return PyTango.DevState.ALARM
		else:
			return PyTango.DevState.ALARM

	def __init__(self,inst,props):
		CounterTimerController.__init__(self,inst,props)
		print "[ImgBeamAnalyzerController] CounterTimerController for instance",self.inst_name," with the properties",props
		self.ch_attrs = {
			1  : 'CentroidX',
			2  : 'CentroidY',
			3  : 'RmsX',
			4  : 'RmsY',
			5  : 'XProjFitConverged',
			6  : 'YProjFitConverged',
			7  : 'XProjFitCenter',
			8  : 'YProjFitCenter',
			9  : 'XProjFitSigma',
			10 : 'YProjFitSigma'}
		self.ImgBeamAnalyzerProxys = [None,] # This controller can only connect to one device. #self.MaxDevice*[None,]
		self.readList = []#self.MaxDevice*[None,]
		self.ansList = []#self.MaxDevice*[None,]
		self.CrtlState = PyTango.DevState.ON

	def AddDevice(self,ind):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In AddDevice method for index",ind
		#if self.devList[ind-1]: #Remember this controller, only one tango device
		#	self.ImgBeamAnalyzerProxys[ind-1] = PyTango.DeviceProxy(self.devList[ind-1])
		#	print "[ImgBeamAnalyzerController]",self.inst_name,": In AddDevice method added",self.ImgBeamAnalyzerProxys[ind-1].name()
		#else:
		#	print "[ImgBeamAnalyzerController]",self.inst_name,": In AddDevice method, no element in class_prop"
		self.ImgBeamAnalyzerProxys = PyTango.DeviceProxy(self.devName)
		print "[ImgBeamAnalyzerController]",self.inst_name,": In AddDevice method added",self.ImgBeamAnalyzerProxys.name()

	def DeleteDevice(self,ind):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In DeleteDevice method for index",ind
		#del self.ImgBeamAnalyzerProxys[ind-1]
		del self.ImgBeamAnalyzerProxys

	def StateAll(self):
		localState = self.ImgBeamAnalyzerProxys.state()
		state = self.stateBridge(localState)
		self.CrtlState = state
		switchstate = 0
		#print "[ImgBeamAnalyzerController]",self.inst_name,": In StateAll method: Device State = ",localState,": PoolState = ",state
		return (int(state), switchstate)

	def StateOne(self,ind):
		#print "[ImgBeamAnalyzerController]",self.inst_name,": In StateOne method for index",ind
		#state = self.ImgBeamAnalyzerProxys[ind-1].state()
		#localState = self.ImgBeamAnalyzerProxys.state()
		#print "[ImgBeamAnalyzerController]",self.inst_name,": Device State = ",localState
		#state = self.stateBridge(localState)
		#print "[ImgBeamAnalyzerController]",self.inst_name,": PoolState = ",state
		#print "[ImgBeamAnalyzerController]",self.inst_name,": In StateOne method for index",ind,": Device State = ",localState,": PoolState = ",state
		#print "[ImgBeamAnalyzerController]",self.inst_name,": In StateOne method for index",ind,": State = ",self.CrtlState
		return (self.CrtlState, "ONE eq to ALL")
		#return (PyTango.DevState.ON,"forced ON")

	def PreReadAll(self):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In PreReadAll method"
		#clean lastest queries
		self.readList = []#self.MaxDevice*[None,]
		self.ansList = []#self.MaxDevice*[None,]

	def PreReadOne(self,ind):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In PreReadOne method for index",ind
		#store a list
		#self.readList.append(self.ImgBeamAnalyzerProxys[ind-1].name())
		self.readList.append(self.ch_attrs[ind])

	def ReadAll(self):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In ReadAll method"
		#send one transaction to tango to read multiples atributes with read_atrubuteS
		print "[ImgBeamAnalyzerController]",self.inst_name,": list",self.readList
		try:
			self.ansList = self.ImgBeamAnalyzerProxys.read_attributes(self.readList)
		except e:
			print "[ImgBeamAnalyzerController]",self.inst_name,": In ReadAll method exception ",e

	def ReadOne(self,ind):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In ReadOne method for index",ind
		#send back the exactly one that the pool asks.
		#return self.ansList[ind].value #!! This does NOT work if the PreReadOne ask the elements in a different than ReadOne!
		return self.ansList[self.readList.index(self.ch_attrs[ind])].value

	def AbortOne(self,ind):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In AbortOne method for index",ind
		pass

	def PreStartAllCT(self):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In PreStartAllCT method"
		pass

	def StartOneCT(self,ind):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In StartOneCT method for index",ind
		pass

	def StartAllCT(self):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In StartAllCT method"
		pass

	def LoadOne(self,ind,value):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In LoadOne method for index",ind," value=",value
		pass

	def GetExtraAttributePar(self,ind,name):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In GetExtraAttributePar method for IBA-ct",ind," name=",name
		pass

	def SetExtraAttributePar(self,ind,name,value):
		print "[ImgBeamAnalyzerController]",self.inst_name,": In SetExtraAttributePar method for IBA-ct",ind," name=",name," value=",value
		pass

	def SendToCtrl(self,in_data):
		print "[ImgBeamAnalyzerController]",self.inst_name,": Received value =",in_data
		return "Adios"

	def __del__(self):
		print "[ImgBeamAnalyzerController]",self.inst_name,": Destroyed"
		pass
