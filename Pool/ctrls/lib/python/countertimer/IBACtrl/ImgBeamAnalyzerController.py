#!/usr/bin/env python

#############################################################################
##
## file :        ImgBeamAanalyzrController.py
##
## description :
##
## project :     Sardana/Pool/ctrls/countertimer
##
## developers history: sblanch
##
## copyleft :    Cells / Alba Synchrotron
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Sardana.
##
## This is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This software is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################

import PyTango
from pool import CounterTimerController
#from pool import PoolUtil
import time
from copy import copy

hackish_IBAProcessSleep = 0.5
hackish_IBAInitSleep = 0.5

class ImgBeamAnalyzerController(CounterTimerController):
    """This class is the Tango Sardana CounterTimer controller for the Tango ImgBeamAnalyzer device.
    One controller only knows one device, and each counter channel responds to one specific device attribute."""

    class_prop = {'devName':{'Description' : 'ImgBeamAnalyzer Tango device',
                             'Type' : 'PyTango.DevString'},
                  'attrList':{'Description':'List of attributes to read after the master channel',
                            'Type':'PyTango.DevVarStringArray'},
                            #for example any one of: '[Chamber]Centroid{X,Y},Rms{X,Y},...'
                            #The master channel is the Exp.Time of the ccd subdevice
                            }

    MaxDevice = 1024 #only one device, the ctrl device means attributes of one IBA

    kls = 'ImgBeamAnalyzerController'
    gender = 'ImgBeamAnalyzer Counter'
    model  = 'ImgBeamAnalyzer_CT'
    image = ''
    icon = ''
    organization = 'CELLS - ALBA'
    logo = 'ALBA_logo.png'

    def __init__(self,inst,props):
        CounterTimerController.__init__(self,inst,props)
        try:
            #IBA:
            self._ibaProxy = PyTango.DeviceProxy(self.devName)
            #CCD:
            self._ccdName = self._ibaProxy.get_property("ImageDevice")['ImageDevice'][0]
            #FIXME: if the iba is configured in a different tangoDB, this ImageDevice name won't have it
            self._ccdProxy = PyTango.DeviceProxy(self._ccdName)
            #internal vblees
            self._backupDict = {}
            self.expTimeValue = None#seconds
            self.attr2read = []
            self.attrValues = []
            self.__flag_loadOne = False
            self.__flag_ccdImgCt = None
            self.__flag_ibaImgCt = None
            self.__flag_backup = False
            #basic state
            self.ctrlState = [PyTango.DevState.ON,""]
            #manipulate the attrList to accept string arrays, and space separated string
            if (type(self.attrList) in [list,tuple] and len(self.attrList) == 1) or\
               (type(self.attrList) == str):
                bar = copy(self.attrList)
                if type(bar) in [list,tuple]: bar = bar[0]
                if type(bar) == str: bar = bar.split(" ")
                self.attrList = copy(bar)
                self._log.info("the attrList had to be manipulated to convert to DevVarStringArray")
            #to be check this manipulation
        except Exception,e:
            self._log.error("%s::__init__() Exception: %s"%(self.kls, str(e)))
        #import logging
        #self._log.setLevel(logging.DEBUG)

    def AddDevice(self,ind):
        """ add each counter involved"""
        if ind > len(self.attrList)+1:
            raise Exception("Not possible with the current length of attributes in the property.")

    def DeleteDevice(self,ind):
        pass

    #check state area:
    def StateAll(self):
        try:
            if self.ctrlState[0] == PyTango.DevState.MOVING:
                if not self._checkCCDacq(): return
                self._checkIBAprocess()
        except Exception,e:
            self.ctrlState = [PyTango.DevState.ALARM,str(e)]

    def StateOne(self,ind):
        if ind > len(self.attrList)+1:
            return PyTango.DevState.DISABLE,"Out of range, review attrList"
        else:
            return self.ctrlState

    ###
    #Data acquisition area:
    def LoadOne(self,ind,value):
        if ind == 1:
            self.expTimeValue = value#seconds
            self.__flag_loadOne = True

    def PreStartOneCT(self,ind):
        """Prepare the iba and the ccd for the acquisition"""
        try:
            if ind == 1 and self.__flag_loadOne:
                self._backup(self._ccdProxy, "ExposureTime", 'attr', self.expTimeValue*1000)
            if not self.__flag_backup:#ind == 1:
                self._doBackup()
                self.__flag_backup = True
            else:
                pass
            return True #I don't know why this expects a boolean feedback
        except Exception,e:
            self._log.error("PreStartOneCT(%d) exception: %s"%(ind,e))
            return False

    def StartAllCT(self):
        """Open the ccd to acquire and make process this image by the iba."""
        dictKey = self._ccdProxy.name()+'_state'
        if self._backupDict.has_key(dictKey) and self._backupDict[dictKey] == PyTango.DevState.RUNNING:
            self.__flag_ccdImgCt = 0#when snap it resets the counter, no need to read it
        else:
            self.__flag_ccdImgCt = self._ccdProxy.read_attribute('ImageCounter').value
        self._log.info("expTime %fs (ccd attr %fms)"%(self.expTimeValue,
                                                      self._ccdProxy.read_attribute('ExposureTime').value))
        #self._log.warn("ccd imgCounter %d"%self.__flag_ccdImgCt)
        self._ccdProxy.Snap()
        self.ctrlState = [PyTango.DevState.MOVING,""]

    def AbortOne(self,ind):
        if ind == 1 :#and self._ccdProxy.State() == PyTango.DevState.RUNNING:
            self._ccdProxy.Stop()
        if self.__flag_backup: self._doRestore()
        self.ctrlState = [PyTango.DevState.ON,"Aborted acquisition"]
    # end data acquisition area
    ####

    ####
    #Data collection are:

    def ReadOne(self,ind):
        #the data is already read, restoring the backup when channel 1
        try:
            if ind == 1:
                if self.expTimeValue == None:
                    self.expTimeValue = self._ccdProxy.read_attribute('ExposureTime').value/1000
                value = self.expTimeValue
            #return what has been read when the image was processed
            else:
                try:
                    value = self.attrValues[ind-2].value
                except:
                    value = self._ibaProxy.read_attribute(self.attrList[ind-2]).value
            #self._log.warn('index = %d\nexpTimeValue %f\nattrList %s\nattrValues %s'%(ind,self.expTimeValue,str(self.attrList),str(self.attrValues)))
            return float(value)
        except Exception,e:
            self._log.error('nan because of %s' % str(e))
            return float('nan')
    # end data collection area
    ####


    ####
    #extra area:
#    def GetExtraAttributePar(self,ind,name):
#        pass
#
#    def SetExtraAttributePar(self,ind,name,value):
#        pass
    # end extra area
    ####

    def send_to_ctrl(self,in_data):#SendToCtrl
        return "Adios"

#    def __del__(self):
#        pass

    ####
    # auxiliar internal methods
    def _checkCCDacq(self):
        current_ccdImgCt = self._ccdProxy.read_attribute('ImageCounter').value
        if self.__flag_ccdImgCt == None and not self.__flag_ibaImgCt == None:
            return True
        elif self.__flag_ccdImgCt < (current_ccdImgCt):#at least one image has been taken
            self._log.info("image has been taken")
            self.__flag_ccdImgCt = None#reset flag
            #due to the image is already take, can be processed
            self.__flag_ibaImgCt = self._ibaProxy.read_attribute('ImageCounter').value
            #self._log.warn("iba imgCounter %d"%self.__flag_ibaImgCt)
            self._ibaProxy.Process()
            self.expTimeValue = self._ccdProxy.read_attribute('ExposureTime').value/1000 #convert from ms to seconds
            return True
        return False
    def _checkIBAprocess(self):
        current_ibaImgCt = self._ibaProxy.read_attribute('ImageCounter').value
        if not self.__flag_ibaImgCt == None and \
        self.__flag_ibaImgCt < current_ibaImgCt:#one image has been process
            self._log.info("image has been processed")
            self.__flag_ibaImgCt = None#reset flag
            #hackish: the imgCt changes a few ms before the attr update
            time.sleep(hackish_IBAProcessSleep)
            self.attrValues = self._ibaProxy.read_attributes(self.attrList)
            if self.__flag_backup: self._doRestore()
            self.ctrlState[0] = PyTango.DevState.ON
            return True
        return False
    
    def _doBackup(self):
        self._backup(self._ccdProxy, None, 'state', None)
        self._backup(self._ibaProxy, "Mode", 'prop', 'ONESHOT')
        self._backup(self._ccdProxy, "TriggerMode", 'attr', 0)

    def _backup(self,dev,vble,vbletype,value):
        self._log.debug("backup the %s %s of the %s and set value %s"%(vbletype,vble,dev.name(),value))
        case = {'prop':self._backupProperty,
                'attr':self._backupAttribute,
                'state':self._backupState}
        case.get(vbletype,self._backupException)(dev,vble,value)

    def _backupException(self,dev,vble,value):
        raise Exception("unknown how to backup %s of %s"%(vble,dev.name()))

    def _backupProperty(self,dev,vble,value):
        dictKey = dev.name()+'_prop_'+vble
        current_value = dev.get_property(vble)[vble][0]
        if not current_value == value:#only backup and modify if it's need
            self._backupDict[dictKey] = current_value
            dev.put_property({vble:value})
            dev.Init()
            time.sleep(hackish_IBAInitSleep)

    def _backupAttribute(self,dev,vble,value):
        dictKey = dev.name()+'_attr_'+vble
        current_value = dev.read_attribute(vble).value
        if not current_value == value:
            self._backupDict[dictKey] = current_value
            dev.write_attribute(vble,value)

    def _backupState(self,dev,vble,value):
        dictKey = dev.name()+'_state'
        current_value = dev.State()
        self._backupDict[dictKey] = current_value
        if current_value == PyTango.DevState.RUNNING:
            dev.Stop()

    def _doRestore(self):
        self._restore(self._ccdProxy, "ExposureTime", "attr")
        self._restore(self._ccdProxy, "TriggerMode", "attr")
        self._restore(self._ibaProxy, "Mode", "prop")
        self._restore(self._ccdProxy, None, "state")
        self.__flag_backup = False
        self._backupDict = {}

    def _restore(self,dev,vble,vbletype):
        self._log.debug("restore the %s %s of the %s"%(vbletype,vble,dev.name()))
        case = {'prop':self._restoreProperty,
                'attr':self._restoreAttribute,
                'state':self._restoreState}
        case.get(vbletype,self._restoreException)(dev,vble)

    def _restoreException(self,dev,vble):
        raise Exception("unknown how to restore %s of %s"%(vble,dev.name()))

    def _restoreProperty(self,dev,vble):
        dictKey = dev.name()+'_prop_'+vble
        if self._backupDict.has_key(dictKey):
            value = self._backupDict[dictKey]
            dev.put_property({vble:value})
            dev.Init()
            if dev == self._ibaProxy:
                dev.Process()#FIXME: HACKISH!!!

    def _restoreAttribute(self,dev,vble):
        dictKey = dev.name()+'_attr_'+vble
        if self._backupDict.has_key(dictKey):
            value = self._backupDict[dictKey]
            dev.write_attribute(vble,value)

    def _restoreState(self,dev,vble):
        dictKey = dev.name()+'_state'
        if self._backupDict.has_key(dictKey):
            value = self._backupDict[dictKey]
            if value == PyTango.DevState.RUNNING:
                for i in range(10):
                    dev.start()
                    if dev.State() == PyTango.DevState.RUNNING: break
                if i == 9: self._log.warn("After 10 attempts, it was not possible to restart the ccd")

    # end auxiliar
    ####
