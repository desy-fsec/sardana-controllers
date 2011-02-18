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
#import time

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
            self._ccdProxy = PyTango.DeviceProxy(self._ccdName)
            #internal vblees
            self._backupDict = {}
            self.expTimeValue = None
            self.attr2read = []
            self.attrValues = []
            self.__flag_loadOne = False
            self.__flag_ccdImgCt = None
            self.__flag_ibaImgCt = None
            #basic state
            self.ctrlState = [PyTango.DevState.ON,""]
        except:
            self._log.error("%s::__init__() Exception"%(self.kls))
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
            if self._checkCCDacq(): return
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
        value_ms = value*1000#value is in seconds, exptime in ms!!
        self.__flag_loadOne = True
        self._backup(self._ccdProxy, "ExposureTime", 'attr', value_ms)

    def PreStartOneCT(self,ind):
        """Prepare the iba and the ccd for the acquisition"""
        try:
            if ind == 1:
                self._doBackup()
            else:
                pass
            return True #I don't know why this expects a boolean feedback
        except Exception,e:
            print "!    %s"%e

    def StartAllCT(self):
        """Open the ccd to acquire and make process this image by the iba."""
        self.ctrlState = [PyTango.DevState.MOVING,""]
        self.__flag_ccdImgCt = 0#when snap it resets the counter
        self._ccdProxy.Snap()

    def AbortOne(self,ind):
        if ind == 1 :#and self._ccdProxy.State() == PyTango.DevState.RUNNING:
            self._ccdProxy.Stop()
        self._doRestore()
        #TODO: this doesn't take care about state of the ctrl
    # end data acquisition area
    ####

    ####
    #Data collection are:

    def ReadOne(self,ind):
        #the data is already read, restoring the backup when channel 1
        try:
            if ind == 1:
                value = self.expTimeValue
            #return what has been read when the image was processed
            else:
                value = self.attrValues[ind-2].value
            return value
        except Exception,e:
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
        if self.__flag_ccdImgCt == (current_ccdImgCt-1):#one image has been taken
            self.__flag_ccdImgCt = None#reset flag
            #due to the image is already take, can be processed
            self.__flag_ibaImgCt = self._ibaProxy.read_attribute('ImageCounter').value
            self._ibaProxy.Process()
            self.expTimeValue = self._ccdProxy.read_attribute('ExposureTime').value/1000 #convert from ms to seconds
            return True
        return False
    def _checkIBAprocess(self):
        current_ibaImgCt = self._ibaProxy.read_attribute('ImageCounter').value
        if self.__flag_ibaImgCt == (current_ibaImgCt-1):#one image has been process
            self.__flag_ibaImgCt = None#reset flag
            self.attrValues = self._ibaProxy.read_attributes(self.attrList)
            self._doRestore()
            self.ctrlState[0] = PyTango.DevState.ON
            return True
        return False
    
    def _doBackup(self):
        self._backup(self._ccdProxy, "TriggerMode", 'attr', 0)
        self._backup(self._ibaProxy, "Mode", 'prop', 'ONESHOT')
        self._backup(self._ccdProxy, None, 'state', None)

    def _doRestore(self):
        self._restore(self._ccdProxy, "ExposureTime", "attr")
        self._restore(self._ccdProxy, "TriggerMode", "attr")
        self._restore(self._ibaProxy, "Mode", "prop")
        self._restore(self._ccdProxy, None, "state")

    def _backup(self,dev,vble,vbletype,value):
        print("backup the %s %s of the %s and set value %s"%(vbletype,vble,dev.name(),value))
        case = {'prop':self._backupProperty,
                'attr':self._backupAttribute,
                'state':self._backupState}
        case.get(vbletype,self._backupException)(dev,vble,value)
    def _backupException(self,dev,vble,value):
        raise Exception("unknown how to backup %s of %s"%(vble,dev.name()))
    def _backupProperty(self,dev,vble,value):
        self._backupDict[dev.name()+'_prop_'+vble] = dev.get_property(vble)[vble][0]
        dev.put_property({vble:value})
        dev.Init()
    def _backupAttribute(self,dev,vble,value):
        self._backupDict[dev.name()+'_attr_'+vble] = dev.read_attribute(vble).value
        dev.write_attribute(vble,value)
    def _backupState(self,dev,vble,value):
        self._backupDict[dev.name()+'_state'] = dev.State()
        if dev.State() == PyTango.DevState.RUNNING:
            dev.Stop()

    def _restore(self,dev,vble,vbletype):
        print("restore the %s %s of the %s"%(vbletype,vble,dev.name()))
        case = {'prop':self._restoreProperty,
                'attr':self._restoreAttribute,
                'state':self._restoreState}
        try:
            case.get(vbletype,self._restoreException)(dev,vble)
        except Exception,e:
            print("ARRR! %s"%e)
    def _restoreException(self,dev,vble):
        raise Exception("unknown how to restore %s of %s"%(vble,dev.name()))
    def _restoreProperty(self,dev,vble):
        dictKey = dev.name()+'_prop_'+vble
        if not self._backupDict.has_key(dictKey):
            raise Exception("not possible to restore property %s of %s"%(vble,dev.name()))
        value = self._backupDict[dictKey]
        dev.put_property({vble:value})
        dev.Init()
    def _restoreAttribute(self,dev,vble):
        dictKey = dev.name()+'_attr_'+vble
        if not self._backupDict.has_key(dictKey):
            raise Exception("not possible to restore attribute %s of %s"%(vble,dev.name()))
        value = self._backupDict[dictKey]
        dev.write_attribute(vble,value)
    def _restoreState(self,dev,vble):
        dictKey = dev.name()+'_state'
        if not self._backupDict.has_key(dictKey):
            raise Exception("not possible to restore state %s of %s"%(vble,dev.name()))
        value = self._backupDict[dictKey]
        if value == PyTango.DevState.RUNNING:
            i = 0
            while i < 10 and not dev.State() == PyTango.DevState.RUNNING:
                print("Start try %d"%i)
                dev.start()
                i += 1
            

    # end auxiliar
    ####