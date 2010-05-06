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
from pool import CounterTimerController
from PyTango import DevState
from pool import PoolUtil

ELCOMAT_FREQ = 25#Hz (samples per second)

class ElcomatCTCtrl(CounterTimerController):
    """CouterTimer Controller for the elcomat device server.
       One controller per elcomat device server, where each ctrl_device means
       an elcomat attribute.
       The state of any ctrl-dev is the state of the elcomat-dev
       Controller properties:
       * devName: name of the elcomat device.
       * attList: List of the attributes that will mean each ctrl_device.
       * nsamples: attr name on the elcomat-dev to setup the number of acquisitions.
    """
    
    kls = 'ElComatCTCtrl'
    
    gender = 'Elcomat Counter'
    model  = 'Elcomat_CT'
    image = ''
    icon = ''
    organization = 'CELLS - ALBA'
    logo = 'ALBA_logo.png'
    
    MaxDevice = 1024#@todo: check
    
    class_prop = {'devName':{'Description':'Elcomat Tango device',
                           'Type':'PyTango.DevString'},
                  'attrList':{'Description':'List of attributes to read after the master channel',
                            'Type':'PyTango.DevVarStringArray'},
                            #for example any one of: '{Av,Stdv}_{x,y}_ts'
                  'nsamples':{'Description':'Name of the attribute who sets the number of samples',
                            'Type':'PyTango.DevString'},
                  }
    
    #ctrl_extra_attributes = {}

    def __init__(self, inst, props):
        CounterTimerController.__init__(self, inst, props)
        try:
            self.devProxy = PyTango.DeviceProxy(self.devName)
            self.attr2read = []
            self.attrValues = []
        except:
            self._log.error("%s::__init__() Exception"%(self.kls))

    def __del__(self):
        self._log_debug("%s::__del__()"%(self.kls))
        del self.devProxy

    def AddDevice(self,axis):
        """ add each counter involved"""
        self._log.debug("%s::AddDevice(%s)"%(self.kls,axis))
        if axis > len(self.attrList)+1:
            raise Exception("Not possible with the current length of attributes in the property.")

    def DeleteDevice(self,axis):
        self._log.debug("%s::DeleteDevice(%s)"%(self.kls,axis))

    def StateAll(self):
        self._log.debug("%s::StateAll()"%(self.kls))
        try:
            self.ctrlState = self.devProxy.State(),""
        except Exception,e:
            self.ctrlState = PyTango.DevState.DISABLE,str(e)

    def StateOne(self,axis):
        self._log.debug("%s::StateOne(%s)"%(self.kls,axis))
        if axis > len(self.attrList)+1:
            return PyTango.DevState.DISABLE,"Out of range, review attrList"
        if axis == 1:
            return self.ctrlState
        else:
            return self.ctrlState

    def PreReadAll(self):
        self._log.debug("%s::PreReadAll()"%(self.kls))
        #clean the list of elements to be read
        self.attr2read = []
        self.attrValues = []
    
    def PreReadOne(self,axis):
        self._log.debug("%s::PreReadOne(%s)"%(self.kls,axis))
        #populate the list of what is wanna be read
        if axis == 1:
            self.attr2read.append(self.nsamples)
        else:
            self.attr2read.append(self.attrList[axis-2])#-1 because 1 is master channel
        self._log.debug("%s::PreReadOne(%s) attributes to read = %s"%(self.kls,axis,self.attr2read))

    def ReadAll(self):
        self._log.debug("%s::ReadAll()"%(self.kls))
        #only one grouped read of all requested
        self.attrValues = self.devProxy.read_attributes(self.attr2read)

    def ReadOne(self,axis):
        self._log.debug("%s::ReadOne(%s)"%(self.kls,axis))
        #return what has been read
        if axis == 1:
            return self.attrValues[self.attr2read.index(self.nsamples)].value/ELCOMAT_FREQ
        else:
            return self.attrValues[self.attr2read.index(self.attrList[axis-2])].value

    #there is no AbortAll, and one acts like all are aborted
    def AbortOne(self,axis):
        self._log.debug("%s::AbortOne(%s)"%(self.kls,axis))
        self.devProxy.Stop()

    def StartAllCT(self):
        self._log.debug("%s::StartAllCT()"%(self.kls))
        self.devProxy.Start()

    #to setup the integration time to the master channel
    def LoadOne(self,axis,value):
        self._log.info("%s::LoadOne(%s,%s)"%(self.kls,axis,value))
        if axis == 1:
            self.devProxy.write_attribute(self.nsamples,int(value*ELCOMAT_FREQ))#time plus samples per second
        #@todo: shall we clean this after acq? or flag this to filter startAll?

    def GetExtraAttributePar(self, axis, name):
        self._log.debug("%s::GetExtraAttributePar(%s,%s)"%(self.kls,axis,name))
#        case = {}
#        case.get(name,self.getterDefault)(axis,name)

    def SetExtraAttributePar(self, axis, name, value):
        self._log.debug("%s::SetExtraAttributePar(%s,%s,%s)"%(self.kls,axis,name,value))
#        case = {}
#        case.get(name,self.setterDefault)(axis,name,value)

    ####
    # Auxiliar methods for the extra attributes

#    def getterDefault(self,axis,name):
#        self._log.warn("Ignoring the GET on the %s extra attr"%name)
#        return None
#    def setterDefault(self,axis,name,value):
#        self._log.warn("Ignoring the SET on the %s extra attr"%name)

    # end aux for extras
    ####

    ####
    # lower level auxiliars

    # end lower level
    ####

if __name__ == "__main__":
    obj = ElcomatCTCtrl('test')

