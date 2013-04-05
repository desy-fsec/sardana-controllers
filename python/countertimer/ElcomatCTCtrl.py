#############################################################################
##
## file :    ElcomatCTCtrl.py
##
## description : 
##
## project :    Sardana/Pool/ctrls/countertimer
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
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import CounterTimerController

class ElcomatCTCtrl(CounterTimerController):
    """CouterTimer Controller for the elcomat device server.
       One controller per elcomat device server, where each ctrl_device means
       an elcomat attribute.
       The state of any ctrl-dev is the state of the elcomat-dev
       Controller properties:
       * devName: name of the elcomat device.
       * attList: List of the attributes that will mean each ctrl_device.
       * acqTimer: attr name on the elcomat-dev to setup the acquisition time.
    """
    
    kls = 'ElComatCTCtrl'
    
    gender = 'Elcomat Counter'
    model  = 'Elcomat_CT'
    image = ''
    icon = ''
    organization = 'CELLS - ALBA'
    logo = 'ALBA_logo.png'
    
    MaxDevice = 1024#@todo: check
    
    ctrl_properties = {'devName':{'Description':'Elcomat Tango device',
                                  'Type':str},
                       'attrList':{'Description':'List of attributes to read after the master channel',
                                   'Type':(str,)},
                                   #for example any one of: '{Av,Stdv}_{x,y}_ts'
                       'acqTimer':{'Description':'Name of the attribute who sets the seconds to acquire',
                                   'Type':str},
                      }
    
    #axis_attributes = {}

    def __init__(self, inst, props,*args,**kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        try:
            self._devProxy = PyTango.DeviceProxy(self.devName)
            self.attr2read = []
            self.attrValues = []
            self.__loadOne = False
        except:
            self._log.error("%s::__init__() Exception"%(self.kls))
        import logging
        self._log.setLogLevel(logging.DEBUG)

    def AddDevice(self,axis):
        """ add each counter involved"""
        if axis > len(self.attrList)+1:
            raise Exception("Not possible with the current length of attributes in the property.")

    def DeleteDevice(self,axis):
        pass

    def StateAll(self):
        try:
            self.ctrlState = [self._devProxy.State(),""]
            if self.ctrlState[0] == PyTango.DevState.RUNNING:
                self.ctrlState[0] = PyTango.DevState.MOVING
        except Exception,e:
            self.ctrlState = [PyTango.DevState.DISABLE,str(e)]

    def StateOne(self,axis):
        if axis > len(self.attrList)+1:
            return PyTango.DevState.DISABLE,"Out of range, review attrList"
        else:
            return self.ctrlState

    def PreReadAll(self):
        #clean the list of elements to be read
        self.attr2read = []
        self.attrValues = []
    
    def PreReadOne(self,axis):
        #populate the list of what is wanna be read
        if axis == 1:
            self.attr2read.append(self.acqTimer)
        else:
            self.attr2read.append(self.attrList[axis-2])#-1 because 1 is master channel

    def ReadAll(self):
        #only one grouped read of all requested
        self.attrValues = self._devProxy.read_attributes(self.attr2read)

    def ReadOne(self,axis):
        #return what has been read
        if axis == 1:
            value = self.attrValues[self.attr2read.index(self.acqTimer)].value
        else:
            value = self.attrValues[self.attr2read.index(self.attrList[axis-2])].value
        return value

    def AbortOne(self,ind):
        if self._devProxy.State() == PyTango.DevState.RUNNING:
            self._devProxy.Stop()

    def StartOneCT(self,axis):
        if axis == 1:
            if self.__loadOne == False:
                self._devProxy.write_attribute(self.acqTimer,600.0) #something like continuous
            else:
                self.__loadOne = False

    def StartAllCT(self):
        if self._devProxy.State() == PyTango.DevState.ON:
            self._devProxy.Start()

    #to setup the integration time to the master channel
    def LoadOne(self,axis,value):
        if axis == 1:
            self.__loadOne = True
            self._devProxy.write_attribute(self.acqTimer,float(value))

    def GetAxisExtraPar(self, axis, name):
        pass

    def SetAxisExtraPar(self, axis, name, value):
        pass
