#!/usr/bin/env python

##############################################################################
#
# This file is part of Sardana
#
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
#
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import threading

from sardana import DataAccess
from sardana.pool import PoolUtil
from sardana.pool.controller import (MotorController, Type, Description,
                                     Access, Memorize, Memorized, NotMemorized,
                                     DefaultValue)
from sardana.tango.core.util import State, from_tango_state_to_state

import PyTango
from IcePAPCtrl import IcepapController


class BL29MaresMagnet(IcepapController):
    """This controller will behave exactly the same as an IcepapController
    except that it will disengage/engage the vertical magnet brake when
    starting/stopping the movement"""

    ctrl_properties = dict(IcepapController.ctrl_properties)  # copy dictionary
    ctrl_properties.update({'BrakeAttribute': {
            Type: str,
            Description: 'The attribute from which to read/write brake status'
        }})

    axis_attributes = dict(IcepapController.axis_attributes)  # copy dictionary
    axis_attributes.update({
        'timeout': {
            Type: float,
            Description: 'Time in seconds to wait before assuming that magnet'
                         'brake was not engaged/disengaged',
            Access: DataAccess.ReadWrite,
            DefaultValue: False
        }})

    gender = 'Motor'
    model = 'BL29_MARES_MagnetBrake'
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
        self.timeout = 3  # default time to wait for brake to disengage

    def StartAll(self):
        """Disengage and check before moving motors"""
        try:
            self.disengaged.write(True)
            start = time.time()
            while not self.disengaged.read().value:
                if time.time() - start < self.timeout:
                    time.sleep(0.3)
                else:
                    msg = 'unable to check if motor was correctly disengaged'
                    self._log.error(msg)
                    raise Exception(msg)
        except Exception, e:
            msg = 'Unable to disengage magnet brake. Details:%s' % str(e)
            self._log.error(msg)
            raise Exception(msg)
        super(BL29MaresMagnet, self).StartAll()

    def StopOne(self, axis):
        """Engage brake after stopping motor"""
        super(BL29MaresMagnet, self).StopOne(axis)
        try:
            self.disengaged.write(False)
            if not self.disengaged.read().value:  # brake was not engaged
                msg = 'unable to check if motor was correctly engaged'
                self._log.error(msg)
                raise Exception(msg)
        except Exception, e:
            msg = 'Failed to check if magnet brake was engaged, please check!'
            self._log.error('%s: %s' % (msg, str(e)))
            raise Exception(msg)

    def AbortOne(self, axis):
        """Engage brake after stopping motor"""
        super(BL29MaresMagnet, self).AbortOne(axis)
        try:
            start = time.time()
            self.disengaged.write(False)
            while not self.disengaged.read().value:
                if time.time() - start < self.timeout:
                    time.sleep(0.3)
                else:
                    msg = 'unable to check if motor was correctly engaged'
                    self._log.error(msg)
                    raise Exception(msg)
        except Exception, e:
            msg = 'Failed to check if magnet brake was engaged, please check!'
            self._log.error('%s: %s' % (msg, str(e)))
            raise Exception(msg)

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
            return super(BL29MaresMagnet, self).GetAxisExtraPar(axis, name)

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
            super(BL29MaresMagnet, self).SetAxisExtraPar(axis, name, value)


class BL29XMCDVectorMagnet(MotorController):
    """..."""

    ctrl_properties = {
        'Device': {
            Type: str,
            Description: 'The device to connect to'
        },
        'AttrB': {
            Type: str,
            Description: 'Attribute for B vector modulus'
        },
        'AttrTheta': {
            Type: str,
            Description: 'Attribute for theta angle'
        },
        'AttrPhi': {
            Type: str,
            Description: 'Attribute for phi angle'
        },
        'AttrBx': {
            Type: str,
            Description: 'Attribute for field in x axis'
        },
        'AttrBy': {
            Type: str,
            Description: 'Attribute for field in y axis'
        },
        'AttrBz': {
            Type: str,
            Description: 'Attribute for field in z axis'
        },
        'CmdRampVector': {
            Type: str,
            Description: 'Command for ramping'
        },
    }

    ctrl_attributes = {
        'Mode': {
            Type: str,
            Description: 'Mode: single axis or vectorial',
            Memorize: NotMemorized
        },
        'StrictCheck': {
            Type: str,
            Description: 'StrictCheck: the device will be strict and complain'
                         ' if not all SMCs are up and running',
            Memorize: NotMemorized
        },
    }

    gender = 'Motor'
    model = 'BL29_XMCD_Vector_Magnet'
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
        self.attrs = [
            self.AttrB, self.AttrTheta, self.AttrPhi, self.AttrBx,
            self.AttrBy, self.AttrBz]
        self.dev = PoolUtil.get_device(inst, self.Device)
        self.state = from_tango_state_to_state(self.dev.state())
        self.last_update = 0
        self.last_stop = 0
        self.timeout = 0.5

    def AddDevice(self, axis):
        """ Nothing special to do.
        @param axis to be added
        """
        if (axis < 1) or (axis > self.MaxDevice):
            raise Exception('Invalid axis %s devices allowed' % str(axis))

    def DeleteDevice(self, axis):
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
            msg = 'Error reading position, axis %s not available' % str(axis)
            self._log.error(msg)
            raise Exception(msg)

    def PreStartAll(self):
        self.moveMultipleValues = []

    def PreStartOne(self, axis, pos):
        self.moveMultipleValues.append((axis, pos))
        return True

    def StartOne(self, axis, pos):
        pass

    def StartAll(self):
        if len(self.moveMultipleValues) == 3:
            # check that we are trying to ramp a vector (b, theta and phi)
            axes = [x[0] for x in self.moveMultipleValues]
            values = [x[1] for x in self.moveMultipleValues]
            check = [x for x in axes if x in [1, 2, 3]]
            if len(check) != 3:
                msg = 'Passed axes do not correspond to b, theta and phi'
                self._log.error(msg)
                raise Exception(msg)
            self.dev.command_inout(self.CmdRampVector, values)
        elif len(self.moveMultipleValues) == 1:
            axis, pos = self.moveMultipleValues[0]
            self.dev.write_attribute(self.attrs[axis-1], pos)
        else:
            msg = ('This controller allows only to move 1 or 3 (b, theta, phi)'
                   ' axes at a time, not %d' % len(self.moveMultipleValues))
            self._log.error(msg)
            raise Exception(msg)
        # force an state update immediately after starting a motion
        self.last_update = 0

    def AbortAll(self):
        # @todo: it looks like AbortAll mechanism is not working and hence
        # this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def AbortOne(self, axis):
        # @todo: it looks like AbortAll mechanism is not working and hence
        # this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def StopAll(self):
        # @todo: it looks like AbortAll mechanism is not working and hence
        # this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def StopOne(self, axis):
        # @todo: it looks like AbortAll mechanism is not working and hence
        # this workaround
        now = time.time()
        if (now - self.last_stop) > 0.5:
            self.dev.command_inout('Stop')
            self.last_stop = now

    def GetCtrlPar(self, parameter):
        """ Get controller parameters.
        @param axis to get the parameter
        """
        if not (parameter.capitalize() in
                [key.capitalize() for key in self.ctrl_attributes.keys()]):
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
        if not (parameter.capitalize() in
                [key.capitalize() for key in self.ctrl_attributes.keys()]):
            raise Exception('Invalid parameter %s' % str(parameter))
        try:
            self.dev.write_attribute(parameter, value)
        except Exception, e:
            msg = 'Error setting parameter %s' % parameter
            self._log.error('%s: %s' % (msg, str(e)))
            raise Exception(msg)


class BL29SmarActSDCController(MotorController):
    """Temporary solution for moving SmarAct SDC motors. It will simply
    send the order to move, but no checks will be done that it actually
    worked: this is because the encoder electronics are not working since
    it was installed, and hence it is impossible to readback motor actual
    position. The controller will save as memorized the last written
    position and will retrieve it on start up"""

    ctrl_properties = {
        'BaudRate': {
            Type: int,
            Description: 'Baudrate of serial line',
            DefaultValue: 115200
        },
        'LineFeed': {
            Type: int,
            Description: 'Line feed character',
            DefaultValue: 0xA
        },
        'Voltage': {
            Type: int,
            Description: 'Voltage',
            DefaultValue: 4090
        },
        'Frequency': {
            Type: int,
            Description: 'Frequency',
            DefaultValue: 200
        },
        'RC_OK': {
            Type: str,
            Description: 'Return code OK value',
            DefaultValue: ':E0,0'
        },
    }

    axis_attributes = {
        'serial_name': {
            Type: str,
            Description: 'Serial device server to access the tty port',
            Access: DataAccess.ReadWrite,
            Memorize: Memorized
        },
        'axis_position': {
            Type: float,
            Description: 'Theoretical axis position of the motor',
            Access: DataAccess.ReadWrite,
            Memorize: Memorized
        },
    }

    SERIAL_NAME, AXIS_POSITION, STEP_PER_UNIT = range(3)

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.axis_param = {}
        self.write_lock = threading.Lock()

    def AddDevice(self, axis):
        if axis in self.axis_param.keys():
            msg = 'Axis %d already in use' % axis
            self._log.error(msg)
            Exception(msg)
        self.axis_param[axis] = ['', float('NaN'), 1.0]  # Init axis values

    def DeleteDevice(self, axis):
        del self.axis_param[axis]

    def ReadOne(self, axis):
        try:
            dial_position = (
                self.axis_param[axis][self.AXIS_POSITION] /
                self.axis_param[axis][self.STEP_PER_UNIT])
            return dial_position
        except Exception, e:
            msg = 'Exception reading axis (%d): %s' % (axis, str(e))
            self._log.error(msg)
            raise

    def StateOne(self, axis):
        """ Get state from hardware for a single axis
        """
        return State.On, 'Do not trust this', MotorController.NoLimitSwitch

    def StartOne(self, axis, dial_pos):
        # check if axis is accessible
        try:
            serial = PyTango.DeviceProxy(
                self.axis_param[axis][self.SERIAL_NAME])
            serial.command_inout('DevSerFlush', 2)
            # read version just to check that we can communicate with the SDC
            serial.command_inout('DevSerWriteString', ':GIV')
            serial.command_inout('DevSerWriteChar', [self.LineFeed])
            version = serial.command_inout('DevSerReadLine')
            if len(version) == 0:
                raise Exception('message got from hardware is empty')
        except Exception, e:
            msg = 'Unable to communicate with SmarAct controller'
            self._log.error('%s: %s' % (msg, str(e)))
            raise Exception(msg)

        # move
        try:
            axis_now = self.GetAxisExtraPar(axis, 'axis_position')
            axis_target = dial_pos * self.axis_param[axis][self.STEP_PER_UNIT]
            axis_steps = axis_target - axis_now
            # send move command to SmarAct controller
            cmd = ':MST0,%d,%d,%d' % (axis_steps, self.Voltage, self.Frequency)
            serial.command_inout('DevSerWriteString', cmd)
            serial.command_inout('DevSerWriteChar', [self.LineFeed])
            rc = serial.command_inout('DevSerReadLine')
            if rc.strip() != self.RC_OK:
                msg = 'SmarAct return code (expected 0): %s' % rc
                self._log.error(msg)
                raise Exception(msg)
            # set and memorize position
            self.SetAxisExtraPar(axis, 'axis_position', axis_target)
        except Exception, e:
            msg = ('Exception moving axis (%d) to position (%f): %s' %
                   (axis, dial_pos, str(e)))
            self._log.error(msg)
            raise Exception(msg)

    def AbortOne(self, axis):
        pass

    def StopOne(self, axis):
        pass

    def GetAxisPar(self, axis, name):
        if name.lower() == 'step_per_unit':
            value = self.axis_param[axis][self.STEP_PER_UNIT]
        else:
            msg = 'Unknown parameter %s' % name
            self._log.error(msg)
            raise Exception(msg)
        return value

    def SetAxisPar(self, axis, name, value):
        if name.lower() == 'step_per_unit':
            if value == 0:
                raise Exception('step_unit_unit cannot be 0')
            self.axis_param[axis][self.STEP_PER_UNIT] = value
        else:
            msg = 'Unknown parameter %s' % name
            self._log.error(msg)
            raise Exception(msg)

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == 'serial_name':
            value = self.axis_param[axis][self.SERIAL_NAME]
        elif name.lower() == 'axis_position':
            value = self.axis_param[axis][self.AXIS_POSITION]
        else:
            msg = 'Unknown parameter %s' % name
            self._log.error(msg)
            raise Exception(msg)
        return value

    def SetAxisExtraPar(self, axis, name, value):
        if name.lower() == 'serial_name':
            self.axis_param[axis][self.SERIAL_NAME] = value
        elif name.lower() == 'axis_position':
            self.axis_param[axis][self.AXIS_POSITION] = value
            # dirty hack to memorize last written position.
            # write 'axis_position' attribute with new axis position (since
            # attr is memorized this will be saved in tango DB) Ideally it
            # would be enough to call SetAxisExtraPar() from anywhere in oder
            # to do this, but this does not actually write the dynamic
            # attribute: the only way of doing that is explicitly setting the
            # 'axis_position' by calling the controller write (i.e in spock:
            # 'motor_name.axis_position = value'): it looks like this is the
            # only way that sardana really calls the 'write_*' tango method
            # of the corresponding tango device.
            if self.write_lock.acquire(False):
                # we need this lock because when we call attr.write_attribute
                # then tango will call sardana's the
                # PoolDeviceClass.write_DynamicAttribute
                # (it seems that sardana sets this function as a callback to
                # tango) if we don't lock then we will an infinite recursive
                # loop
                axis_name = self.GetAxisName(axis)  # axis name is tango alias
                attr = PyTango.DeviceProxy(axis_name)
                attr.write_attribute('axis_position', value)
                self.write_lock.release()
        else:
            msg = 'Unknown parameter %s' % name
            self._log.error(msg)
            raise Exception(msg)
