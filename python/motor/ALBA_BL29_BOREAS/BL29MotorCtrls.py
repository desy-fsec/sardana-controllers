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

import time

from sardana import DataAccess
from sardana.pool import PoolUtil 
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Description, Access, Memorize, NotMemorized, DefaultValue
from sardana.tango.core.util import State, from_tango_state_to_state

import PyTango
from IcePAPCtrl import IcepapController


class BL29MaresMagnet(IcepapController):
    """This controller will behave exactly the same as an IcepapController
    except that it will disengage/engage the vertical magnet brake when
    starting/stopping the movement"""

    ctrl_properties = dict(IcepapController.ctrl_properties) #copy dictionary
    ctrl_properties.update({'BrakeAttribute':
        {
            Type : str,
            Description : 'The attribute from which to read/write brake status'
        }})

    axis_attributes = dict(IcepapController.axis_attributes) #copy dictionary
    axis_attributes.update({
        'timeout' : {
            Type : float,
            Description : 'Time in seconds to wait before assuming that magnet brake was not engaged/disengaged',
            Access : DataAccess.ReadWrite,
            DefaultValue : False
        }})

    gender = 'Motor'
    model  = 'BL29_MARES_MagnetBrake'
    organization = 'ALBA'
    image = 'ALBA_logo.png'
    logo = 'ALBA_logo.png'
    icon = 'ALBA_logo.png'
    state = ''
    status = ''

    def __init__(self, inst, props, *args, **kwargs):
        """Do the default init"""
        IcepapController.__init__(self, inst, props, *args, **kwargs)
        self.disengaged = PyTango.AttributeProxy(self.BrakeAttribute)
        self.timeout = 3 #default time to wait for brake to disengage

    def StartAll(self):
        """Disengage and check before moving motors"""
        try:
            self.disengaged.write(True)
            start = time.time()
            while self.disengaged.read().value != True:
                if time.time() - start < self.timeout:
                    time.sleep(0.3)
                else:
                    raise Exception('unable to check if motor was correctly disengaged')
        except Exception, e:
            raise Exception('Unable to disengage magnet brake. Details:%s' % str(e))
        super(BL29MaresMagnet,self).StartAll()

    def StopOne(self, axis):
        """Engage brake after stopping motor"""
        super(BL29MaresMagnet,self).StopOne(axis)
        try:
            self.disengaged.write(False)
            if self.disengaged.read().value != False: #brake was not engaged
                raise Exception('unable to check if motor was correctly engaged')
        except Exception, e:
            raise Exception('Failed to check if magnet brake was engaged, please check!')

    def AbortOne(self, axis):
        """Engage brake after stopping motor"""
        super(BL29MaresMagnet,self).AbortOne(axis)
        try:
            self.disengaged.write(False)
            while self.disengaged.read().value != False:
                if time.time() - start < self.timeout:
                    time.sleep(0.3)
                else:
                    raise Exception('unable to check if motor was correctly engaged')
        except Exception, e:
            raise Exception('Failed to check if magnet brake was engaged, please check!')

    def GetAxisExtraPar(self, axis, name):
        """
        Get extra controller parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to get (always one)
        @param name of the parameter to retrieve
        @return the value of the parameter
        """
        if name.lower() == 'timeout':
            return self.timeout
        else:
            return super(BL29MaresMagnet,self).GetAxisExtraPar(axis,name)

    def SetAxisExtraPar(self, axis, name, value):
        """
        Set extra axis parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to set (always one)
        @param name of the parameter to set
        @param value to be set
        """
        if name.lower() == 'timeout':
            self.timeout = value
        else:
            super(BL29MaresMagnet,self).SetAxisExtraPar(axis,name,value)


class BL29XMCDVectorMagnet(MotorController):
    """..."""

    ctrl_properties = {
        'Device' : {
            Type : str,
            Description : 'The device to connect to'
        },
        'AttrB' : {
            Type : str,
            Description : 'Attribute for B vector modulus'
        },
        'AttrTheta' : {
            Type : str,
            Description : 'Attribute for theta angle'
        },
        'AttrPhi' : {
            Type : str,
            Description : 'Attribute for phi angle'
        },
        'AttrBx' : {
            Type : str,
            Description : 'Attribute for field in x axis'
        },
        'AttrBy' : {
            Type : str,
            Description : 'Attribute for field in y axis'
        },
        'AttrBz' : {
            Type : str,
            Description : 'Attribute for field in z axis'
        },
        'CmdRampVector' : {
            Type : str,
            Description : 'Command for ramping'
        },
    }

    ctrl_attributes = {
        'Mode' : {
            Type : str,
            Description : 'Mode: single axis or vectorial',
            Memorize : NotMemorized
        },
        'StrictCheck' : {
            Type : str,
            Description : 'StrictCheck: the device will be strict and complain if not all SMCs are up and running',
            Memorize : NotMemorized
        },
    }

    gender = 'Motor'
    model  = 'BL29_XMCD_Vector_Magnet'
    organization = 'CELLS - ALBA'
    image = 'ALBA_logo.png'
    logo = 'ALBA_logo.png'
    icon = 'ALBA_logo.png'
    state = ''
    status = ''

    MaxDevice = 6

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the icepap connection
        @param inst instance name of the controller
        @param properties of the controller
        """
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.attrs = [self.AttrB, self.AttrTheta, self.AttrPhi, self.AttrBx, self.AttrBy, self.AttrBz]
        self.dev = PoolUtil.get_device(inst, self.Device)
        self.state = from_tango_state_to_state(self.dev.state())
        self.last_update = 0
        self.last_stop = 0
        self.timeout = 0.5

    def AddDevice(self,axis):
        """ Nothing special to do.
        @param axis to be added
        """
        if (axis<1) or (axis > self.MaxDevice):
            raise Exception('Invalid axis %s devices allowed' % str(axis))

    def DeleteDevice(self,axis):
        """ Nothing special to do.
        @param axis to be deleted
        """
        pass

    def StateAll(self):
        """ Get state from hardware for all axes
        """
        self.state = from_tango_state_to_state(self.dev.state())
        self.status = str(self.state)
        self.last_update = time.time()

    def StateOne(self, axis):
        """ Get state from hardware for a single axis
        """
        return self.state, self.status, MotorController.NoLimitSwitch

    def ReadOne(self, axis):
        try:
            return self.dev.read_attribute(self.attrs[axis-1]).value
        except:
            raise Exception('Error reading position, axis %s not available' % str(axis))

    def PreStartAll(self):
        self.moveMultipleValues = []

    def PreStartOne(self, axis, pos):
        self.moveMultipleValues.append((axis,pos))
        return True

    def StartOne(self, axis, pos):
        pass

    def StartAll(self):
        if len(self.moveMultipleValues) == 3:
            #check that we are trying to ramp a vector (b, theta and phi)
            axes = [x[0] for x in self.moveMultipleValues]
            values = [x[1] for x in self.moveMultipleValues]
            check = [x for x in axes if x in [1,2,3]]
            if len(check)!=3:
                msg = 'Passed axes do not correspond to b, theta and phi'
                self._log.error(msg)
                raise Exception(msg)
            self.dev.command_inout(self.CmdRampVector,values)
        elif len(self.moveMultipleValues) == 1:
            axis, pos = self.moveMultipleValues[0]
            self.dev.write_attribute(self.attrs[axis-1],pos)
        else:
            msg = 'This controller allows only to move 1 or 3 (b, theta and phi) axes at a time, not %s' % str(len(self.moveMultipleValues))
            self._log.error(msg)
            raise Exception(msg)
        self.last_update = 0 #force an state update immediately after starting a motion

    def AbortAll(self):
        #@todo: it looks like AbortAll mechanism is not working and hence this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def AbortOne(self, axis):
        #@todo: it looks like AbortAll mechanism is not working and hence this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def StopAll(self):
        #@todo: it looks like AbortAll mechanism is not working and hence this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def StopOne(self, axis):
        #@todo: it looks like AbortAll mechanism is not working and hence this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def GetCtrlPar(self, parameter):
        """ Get controller parameters.
        @param axis to get the parameter
        """
        if not (parameter.capitalize() in [key.capitalize() for key in self.ctrl_attributes.keys()]):
            raise Exception('Invalid parameter %s' % str(parameter))
        try:
            return self.dev.read_attribute(parameter).value
        except:
            raise Exception('Error getting parameter %s' % parameter)

    def SetCtrlPar(self, parameter, value):
        """ Set controller parameters.
        @param parameter to be set
        @param value to set
        """
        if not (parameter.capitalize() in [key.capitalize() for key in self.ctrl_attributes.keys()]):
            raise Exception('Invalid parameter %s' % str(parameter))
        try:
            self.dev.write_attribute(parameter,value)
        except Exception, e:
            raise Exception('Error setting parameter %s' % parameter)
