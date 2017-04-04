#!/usr/bin/env python

#############################################################################
##
## file :    PyCATSMotorCtrl.py
##
## developers : ctbeamlines@cells.es
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
import time
from sardana.pool.controller import MotorController
from sardana import State, DataAccess
from sardana.pool.controller import OneDController, Description, Access, \
Type, Memorize, Memorized, MaxDimSize 

class PyCATSMotorCtrl(MotorController):
    """This class is the Sardana motor controller for the device server of
    CATS robotic arm. It is designed to work linked to the TangoDS.

    The axes order is:
    1: X
    2: Y
    3: Z
    """

    MaxDevice = 3
    DELTA_STATE = 1
    AXIS_ATTR = ['Xpos', 'Ypos', 'Zpos']
    class_prop = {'DeviceName':
                      {Type: 'PyTango.DevString',
                       Description: 'Device name of the PyCATS DS'}}


    ctrl_attributes = {
		'AutoPoweron': {
		Type: bool,
		Description: 'Active/Deactivate automatic robot power on',
		Access: DataAccess.ReadWrite,
		Memorize: Memorized}
		}



    CATS_ALLOWED_TOOLS = {'PLATE': 3}

    def __init__(self, inst, props, *args, **kwargs):

        try:
            MotorController.__init__(self, inst, props, *args, **kwargs)
            self.device = PyTango.DeviceProxy(self.DeviceName)
            self.positionMultiple = {}
            self.attributes = {}
            self.tool = None
            self.idle = None
            self.powered = None
            self.auto_poweron = False
            self.t0 = time.time()

        except Exception as e:
            self._log.error('Error when init: %s' % e)
            raise

    def AddDevice(self, axis):
        self._log.debug('AddDevice entering...')
        self.attributes[axis] = {'step_per_unit': 1.0,
                                 'base_rate': 0,
                                 'acceleration': 0,
                                 'velocity': 1}
    def DeleteDevice(self, axis):
        self.attributes[axis] = None

    def StateAll(self):
        """
        Get robot State
        """
        try:

            self.powered = self.device.read_attribute('Powered').value
            # Try to power on the robot if necessary
            if self.auto_poweron and not self.powered:
            self.device.poweron()
            time.sleep(2)
            # check if robot is idle
            self.idle = self.device.read_attribute('do_PRO5_idl').value
            # check if power is powered
            self.powered = self.device.read_attribute('Powered').value
            # check if the tool installed is allowed
            self.tool = self.device.read_attribute('Tool').value.upper()
        except Exception as e:
            msg = "Cannot access robot attributes to update controller status"
            self._log.error('StateAll error: %s\n%s' % (msg, str(e)))
            self.state = State.Fault
            self.status = msg
            raise RuntimeError("%s,%s" % (msg, str(e)))

    def StateOne(self, axis):

        if not self.powered:
            self.state = State.Fault
            self.status = 'Not Powered, is EH open? (Fault)'
       
        elif self.tool not in self.CATS_ALLOWED_TOOLS.keys():
            self.state = State.Fault
            self.status = 'Wrong Tool Installed, use %r' \
                          %self.CATS_ALLOWED_TOOLS.keys()

        elif time.time() - self.t0 < self.DELTA_STATE:
            pass

        elif self.idle:
            self.state = State.On
            self.status = 'ON'

        else:
            self.state = State.Moving
            self.status = 'Moving'

        return self.state, self.status

    def ReadAll(self):
        self.positionMultiple = {}
        for axis in self.attributes.keys():
            attr = self.AXIS_ATTR[axis-1]
            value = self.device.read_attribute(attr).value
            pos = value / self.attributes[axis]['step_per_unit']
            self.positionMultiple[axis] = pos

    def ReadOne(self, axis):
        return self.positionMultiple[axis]

    def StartOne(self, axis, position):


        # TODO: The controllers does not allow to move multiple axes
        # at the same time.
        # CATS axes z,x can be move together by using a single command adjust.
        #
        # TODO: Implement correct sign for axes 2 and 3 at the DS level.
        #
        # Fault State when CATS is not powered or the tool installed is not
        # allowed
        if self.state is State.Fault:
            return

        attr = self.AXIS_ATTR[axis-1]
        # get target dial position in steps
        position = position * self.attributes[axis]['step_per_unit']
        # get current dial position in steps
        pos = self.device.read_attribute(attr).value
        #calculate delta
        delta = (position - pos)*1000 # command must be send in microns

        self._log.debug('Axis: %s, current pos: %s, target pos: %s, delta: '
                        '%s'  %(attr, pos, position, delta))

        cats_plate_tool = self.CATS_ALLOWED_TOOLS[self.tool]

        if axis == 1 or axis == 3:
            # Move in plane
            # Compose the command for X or Z motor
            if axis == 1:
                command = 'adjust(%d,0,0,0,0,0,0,0,0,0,%d,0)' % (
                    cats_plate_tool, delta)
            else:

                # Change sign because the CATS movement in Z motor is inverted
                delta = -delta
                command = str('adjust(%d,0,0,0,0,0,0,0,0,0,0,%d)' % (
                    cats_plate_tool, delta))

            response = self.device.command_inout('send_op_cmd', command)
            self._log.debug('adjust response: %s' % response)
            if response != 'adjust':
            #TODO raise error
                pass

        elif axis == 2:
            #Move Focus (along beam)
            # Change sign because the CATS movement in Y motor is inverted
            delta = -delta
            command = 'focus(%d,0,0,0,0,0,0,0,0,0,0,0,%d)' %  (
                cats_plate_tool, delta)
            response = self.device.command_inout('send_op_cmd', command)
            self._log.debug('focus response: %s' % response)
            if response != 'focus':
            #TODO raise error
                pass
        self._log.debug('command sent: %s' % command)

        self.state = State.Moving
        self.t0 = time.time()

    def StartAll(self):
        pass

    def SetAxisExtraPar(self, axis, name, value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        name = name.lower()
        if name == "velocity":
            self.attributes[axis]["velocity"] = float(value)
        elif name == "acceleration":
            self.attributes[axis]["acceleration"] = float(value)
        elif name == "deceleration":
            self.attributes[axis]["deceleration"] = float(value)
        elif name == "step_per_unit":
            self.attributes[axis]["step_per_unit"] = float(value)
        elif name == "base_rate":
            self.attributes[axis]["base_rate"] = float(value)

    def GetAxisExtraPar(self, axis, name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        name = name.lower()
        if name == 'velocity':
            value = self.attributes[axis]['velocity'] / self.attributes[
                axis]['step_per_unit']

        elif name in ['acceleration', 'deceleration']:
            value = self.attributes[axis]['acceleration']

        elif name == "step_per_unit":
            value = self.attributes[axis]["step_per_unit"]

        elif name == "base_rate":
            value = self.attributes[axis]["base_rate"]

        return value

    def AbortOne(self, axis):
        self._log.debug("aborting movement")
        self.device.command_inout('abort')

    def SetCtrlPar(self, parameter, value):
        self._log.debug("Entering SetCtrlPar, parameter = %s, value = %s" %
                        (parameter, value))
        if parameter.lower() == 'autopoweron':
            self.auto_poweron = value
        else:
            MotorController.SetCtrlPar(self, parameter, value)

    def GetCtrlPar(self, parameter):
        self._log.debug("Entering GetCtrlPar, parameter = %s" % parameter )
        if parameter.lower()== 'autopoweron':
            self._log.debug("auto_poweron = %s" % self.auto_poweron)
            return self.auto_poweron
        else:
            return MotorController.GetCtrlPar(self, parameter)




