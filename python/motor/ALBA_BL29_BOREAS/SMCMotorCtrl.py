#!/usr/bin/env python

##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################


from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description

from sardana.tango.core.util import from_tango_state_to_state

import PyTango


class SMCMotorController(MotorController):
    """Controller for the TwickenhamSMC Super conducting Magnet Controller
    This version should be replaced by the more sophisticated """

    gender = ''
    model  = ''
    organization = 'CELLS - ALBA'
    image = ''
    icon = ''
    logo = 'ALBA_logo.png'

    ATTR_MODE = 'Mode'
    ATTR_RAMP_RATE = 'RampRate'

    MaxDevice = 3

    ctrl_properties = {
        'TangoDevice' : {
            Type : str,
            Description : ''
        },
        'TangoDeviceX' : {
            Type : str,
            Description : ''
        },
        'TangoDeviceY' : {
            Type : str,
            Description : ''
        },
        'TangoDeviceZ' : {
            Type : str,
            Description : ''
        },
    }

    ctrl_attributes = {
        ATTR_MODE : {
            Type : str,
            Description : '',
            Access : DataAccess.ReadWrite
        },
    }

    AXES = {
        0 : 'Bx',
        1 : 'By',
        2 : 'Bz',
    }

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.tango_vm = None
        self.smc_proxies = [None, None, None]
        #build vector magnet device proxy
        self.tango_vm = PyTango.DeviceProxy(self.TangoDevice)
        #build SMC device proxies
        for idx, dev_name in enumerate([self.TangoDeviceX, self.TangoDeviceY, self.TangoDeviceZ]):
            self.smc_proxies[idx] = PyTango.DeviceProxy(dev_name)


    def AddDevice(self, axis):
        pass


    def DeleteDevice(self, axis):
        pass


    def StateOne(self, axis):
        try:
            py_state = self.smc_proxies[axis-1].state()
#            py_state = self.tango_vm.state()
            self._log.debug('PyTango state: %s' % str(py_state))
            return (from_tango_state_to_state(py_state), '', 0)
        except Exception,e:
            msg = 'Exception getting state for axis (%d): %s' % (axis,str(e))
            self._log.error(msg)
            return (State.Alarm, msg, 0)


#    def PreReadAll(self):
#        pass
        
#    def PreReadOne(self, axis):
#        pass
#
#    def ReadAll(self):
#        pass

    def ReadOne(self, axis):
        try:
            self._log.debug('Axis: %d -- Field: %f -- DevName: %s' % (axis, self.smc_proxies[axis-1].read_attribute('Field').value, self.smc_proxies[axis-1].dev_name()) )
            return self.smc_proxies[axis-1].read_attribute('Field').value
        except Exception, e:
            msg = 'Exception reading axis (%d): %s' % (axis,str(e))
            self._log.error(msg)
            raise


#    def PreStartAll(self):
#        pass
#
#
    def PreStartOne(self, axis, pos):
        return True


#    def PreStateAll(self):
#        pass


    def StartOne(self, axis, pos):
        try:
#            print 80*'-', axis, self.smc_proxies[axis-1].read_attribute('Field').value, pos
            self.smc_proxies[axis-1].write_attribute('lower',pos)
#            self.tango_vm.write_attribute(self.AXES[axis-1], pos)
        except Exception, e:
            msg = 'Exception starting axis (%d) to pos (%f): %s' % (axis, pos, str(e))
            self._log.error(msg)
            return State.Alarm, msg, 0


    def StartAll(self):
        pass


    def AbortOne(self,axis):
        pass


    def StopOne(self,axis):
        pass


    def GetAxisPar(self, axis, name):
        name = name.lower()
        if name == 'velocity':
            return (self.smc_proxies[axis-1].read_attribute(self.ATTR_RAMP_RATE).value)

    def SetAxisPar(self, axis, name, value):
        name = name.lower()
        if name == 'velocity':
            self.smc_proxies[axis-1].write_attribute(self.ATTR_RAMP_RATE,value)
#            self.tango_vm.write_attribute("%s%s" % (self.AXES[axis-1], self.ATTR_RAMP_RATE), values)


    def GetCtrlPar(self, parameter):
#        print 80*'/', parameter
        parameter = parameter.lower()
        if parameter == self.ATTR_MODE:
            return self.tango_vm.read_attribute(self.ATTR_MODE).value


    def SetCtrlPar(self, parameter, value):
        parameter = parameter.lower()
        if parameter == self.ATTR_MODE:
            self.tango_vm.write_attribute(self.ATTR_MODE, value)
