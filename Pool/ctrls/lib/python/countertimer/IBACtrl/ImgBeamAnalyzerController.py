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
from pool import PoolUtil
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
        self.ImgBeamAnalyzerProxys = None
        self.readList = []
        self.readIndex = {}
        self.ansList = []
        self.CrtlState = PyTango.DevState.ON

    def getIBA(self):
        return PoolUtil().get_device(self.inst_name, self.devName)

    def AddDevice(self,ind):
        if ind > 10:
            raise Exception("This IBA controller only supports 10 axis")

    def DeleteDevice(self,ind):
        pass
    
    def StateAll(self):
        iba = self.getIBA()
        
        try:
            localState = iba.state()
        except Exception,e:
            self.CrtlState = PyTango.DevState.ALARM, str(e)
            return
        
        state = self.stateBridge(localState)
        self.CrtlState = state, "ONE eq to ALL"

    def StateOne(self,ind):
        return self.CrtlState

    def PreReadAll(self):
        # we try to get IBA proxy to check for errors.
        iba = self.getIBA()

        self.readList = []
        self.readIndex = {}
        self.ansList = []

    def PreReadOne(self,ind):
        ch_name = self.ch_attrs[ind]
        self.readList.append(ch_name)
        self.readIndex[ind] = len(self.readList)-1

    def ReadAll(self):
        iba = self.getIBA()
        
        try:
            self.ansList = iba.read_attributes(self.readList)
        except Exception, e:
            print "[ImgBeamAnalyzerController]",self.inst_name,": In ReadAll method exception ",e

    def ReadOne(self,ind):
        return self.ansList[self.readIndex[ind]].value

    def AbortOne(self,ind):
        pass

    def PreStartAllCT(self):
        pass

    def StartOneCT(self,ind):
        pass

    def StartAllCT(self):
        pass

    def LoadOne(self,ind,value):
        pass

    def GetExtraAttributePar(self,ind,name):
        pass

    def SetExtraAttributePar(self,ind,name,value):
        pass

    def SendToCtrl(self,in_data):
        return "Adios"

    def __del__(self):
        pass
