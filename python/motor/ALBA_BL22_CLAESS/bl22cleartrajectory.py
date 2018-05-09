###############################################################################
#
# file :    bl22cleartrajectory.py
#
# description : Motor controller to implement a first approach of the IcePAP
#               trajectories
#
# project :    miscellaneous/PoolControllers/MotorControllers
#
# developers history: rhoms
#
# copyleft :    Cells / Alba Synchrotron
#               Bellaterra
#               Spain
#
###############################################################################
#
# This file is part of Sardana.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
###############################################################################

import pickle
import numpy as np
from pyIcePAP import EthIcePAPController
from sardana.pool.controller import MotorController, Type, Description, \
    DefaultValue, Access, DataAccess
from sardana import State


def get_max_vel(lpar, lpos, motor_vel):
    """
    Get the maximum velocity of the parameter according to the motor velocity

    :param lpar: [float]
    :param lpos: [float]
    :param motor_vel: float
    :return: float
    """
    par_vels = []
    for i in range(len(lpar)-1):
        ti = abs(abs(lpos[i+1]) - abs(lpos[i])) / motor_vel
        vi = abs(abs(lpar[i+1]) - abs(lpar[i])) / ti
        par_vels.append(vi)
    return min(par_vels)


class BL22ClearTrajectory (MotorController):
    # TODO: Do the docstring
    """

    """
    gender = "Motor"
    model = "Icepap"
    organization = "ALBA"
    MaxDevice = 1

    # The properties used to connect to the IcePAP motor controller

    ctrl_properties = {
        'Host': {Type: str, Description: 'The host name'},
        'Port': {Type: int, Description: 'The port number',
                 DefaultValue: 5000},
        'Timeout': {Type: int, Description: 'Connection timeout',
                    DefaultValue: 3},
        'DataFile': {Type: str,
                     Description: 'Filename with the binary data'},
        'cay_addr': {Type: int, Description: 'Motor axis number'},
        'caxr_addr': {Type: int, Description: 'Motor axis number'},
        'caz_addr': {Type: int, Description: 'Motor axis number'},
        'cdy_addr': {Type: int, Description: 'Motor axis number'},
        'cdz_addr': {Type: int, Description: 'Motor axis number'},
        'cdxr_addr': {Type: int, Description: 'Motor axis number'},
        'cslxr_addr': {Type: int, Description: 'Motor axis number'},

        'Tolerance': {Type: float,
                      Description: 'Parameter error on the position of each '
                                   'motor.',
                      DefaultValue: 1.0e-5},

    }
    ctrl_attributes = {

    }
    axis_attributes = {
        # TODO add mode to select which motor we will move
        'MaxVelocity': {Type: float, Access: DataAccess.ReadOnly},
    }

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self._ipap = EthIcePAPController(self.Host, self.Port, self.Timeout)

        self._step_per_unit = None
        aliases = {}
        aliases['cay'] = self.cay_addr
        aliases['caxr'] = self.caxr_addr
        aliases['caz'] = self.caz_addr
        aliases['cdy'] = self.cdy_addr
        aliases['cdz'] = self.cdz_addr
        aliases['cdxr'] = self.cdxr_addr
        aliases['cslxr'] = self.cslxr_addr
        self._trajdic = None
        self._ipap.add_aliases(aliases)
        # TODO: Include on the trajectory tables the cslxr motor.
        # Exclude caz
        self._motor_list = ['cay', 'caxr', 'cdy', 'cdz', 'cdxr', 'cslxr']
        self._master_motor = 'caxr'
        self._tolerance = self.Tolerance
        self._velocity = None
        self._acctime = 0
        self._max_vel = None

    def _load_trajectories(self, filename):
        with open(filename) as f:
            self._trajdic = pickle.load(f)
        par = self._trajdic['parameter']
        self._max_vel = None
        max_vels = []
        for motor_name in self._motor_list:
            motor_table = self._trajdic[motor_name]
            self._ipap[motor_name].clear_parametric_table()
            self._ipap[motor_name].set_parametric_table(par, motor_table,
                                                        mode='LINEAR')
            motor_vel = self._ipap[motor_name].velocity
            max_vel = get_max_vel(par, motor_table, motor_vel)
            max_vels.append(max_vel)
            self._log.debug('{0} {1}'.format(motor_name, max_vel))

        self._max_vel = min(max_vels)

    def _set_vel(self, vel):
        for motor in self._motor_list:
            self._ipap[motor].parvel = vel

    def _set_acctime(self, acctime):
        for motor in self._motor_list:
            self._ipap[motor].paracct = acctime

    def _find_near_bragg(self, motor_name):
        current_pos = self._ipap[motor_name].pos
        traj_pos = np.array(self._trajdic[motor_name])
        idx_min = (np.abs(traj_pos - current_pos)).argmin()
        bragg_pos = self._trajdic['parameter'][idx_min]
        motor_pos = self._trajdic[motor_name][idx_min]
        return bragg_pos, current_pos, motor_pos

    def AddDevice(self, axis):
        """ Set default values for the axis and try to connect to it
        @param axis to be added
        """
        self._step_per_unit = 1
        self._load_trajectories(self.DataFile)

    def DeleteDevice(self, axis):
        # Todo analyze if is necesary
        for motor_name in self._motor_list:
            self._ipap[motor_name].clear_parametric_table()

    def StateOne(self, axis):
        """
        Connect to the hardware and check the state. If no connection
        available, return ALARM.
        @param axis to read the state
        @return the state value: {ALARM|ON|MOVING}
        """

        sync = []
        for motor in self._motor_list:
            try:
                self._ipap[motor].parpos
            except Exception:
                near_bragg, current_pos, motor_pos = self._find_near_bragg(
                    motor)
                msg = '{0} ({1}) is near to ({2}) ' \
                      '{3}\n'.format(motor, current_pos, motor_pos,
                                     near_bragg)
                sync.append(msg)

        if len(sync) > 0:
            state = State.Alarm
            status = 'There are motors not synchronized (use clearSync ' \
                     'macro):\n {0}'.format(' '.join(sync))
            return state, status

        motors_states = self._ipap.get_states(self._motor_list)
        moving = []
        alarm = []

        for state, motor in zip(motors_states, self._motor_list):
            moving_flags = [state.is_moving(), state.is_settling()]
            if any(moving_flags):
                moving.append(motor)
            alarm_flags = [state.is_limit_positive(),
                           state.is_limit_negative(),
                           not state.is_poweron()]
            if any(alarm_flags):
                alarm.append(motor)
        if len(alarm) > 0:
            state = State.Alarm
            status = 'The motors {0} are in alarm state'.format(' '.join(
                alarm))
        elif len(moving) > 0:
            state = State.Moving
            status = 'The motors {0} are moving.'.format(' '.join(moving))
        else:
            state = State.On
            status = 'All motors are ready'

        if state != State.Moving:
            master_pos = self._ipap[self._master_motor].parpos
            out_pos = []
            msg = '{0} in {1} and should be in {2}\n'
            for motor in self._motor_list:

                motor_pos = self._ipap[motor].parpos
                diff = abs(abs(motor_pos) - abs(master_pos))
                is_close = diff <= self._tolerance
                if not is_close:
                    out_pos.append(msg.format(motor, motor_pos, master_pos))

            if len(out_pos) > 0:
                state = State.Alarm
                status = 'There are motors with diffent position (use ' \
                         'clearMoveTo macro):\n {0}'.format(' '.join(out_pos))
        self._log.debug('State: %r Status: %r' % (state, status))
        return state, status

    def ReadOne(self, axis):
        """ Read the position of the axis.
        @param axis to read the position
        @return the current axis position
        """

        state, status = self.StateOne(axis)
        if state == State.Alarm:
            raise RuntimeError(status)

        for motor in self._motor_list:
            pos = self._ipap[motor].parpos
            self._log.debug('{0}: {1}'.format(motor, pos))
        return self._ipap[self._master_motor].parpos

    def StartOne(self, axis, pos):
        """ Start movement of the axis.
        :param axis: int
        :param pos: float
        :return: None
        """
        state, status = self.StateOne(axis)
        if state != State.On:
            raise RuntimeError(status)
        self._ipap.pmove(pos, self._motor_list, group=True)

    def StopOne(self, axis):
        """
        Stop axis
        :param axis: int
        :return: None
        """
        self._ipap.stop(self._motor_list)

    def AbortOne(self, axis):
        """
        Abort movement
        :param axis: int
        :return: None
        """
        self._ipap.abort(self._motor_list)

    def SetPar(self, axis, name, value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        attr_name = name.lower()

        if attr_name == 'step_per_unit':
            self._step_per_unit = float(value)
        elif attr_name == 'velocity':
            velocity = value * self._step_per_unit
            if self._max_vel is None:
                raise RuntimeError('You must load first the table')
            if velocity > self._max_vel:
                raise ValueError('The value must be lower/equal than/to '
                                 '{0}'.format(self._max_vel))
            self._velocity = velocity
            self._set_vel(self._velocity)
            self._set_acctime(self._acctime)
        elif attr_name == 'acceleration':
            self._acctime = value
            self._set_acctime(self._acctime)
        elif attr_name == 'base_rate':
            pass
        elif attr_name == 'deceleration':
            pass
        else:
            MotorController.SetPar(self, axis, name, value)

    def GetPar(self, axis, name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """

        attr_name = name.lower()
        if attr_name == 'step_per_unit':
            result = self._step_per_unit
        elif attr_name == 'velocity':
            vel = self._ipap[self._master_motor].parvel
            result = vel / self._step_per_unit
        elif attr_name == 'acceleration' or attr_name == 'deceleration':
            acctime = self._ipap[self._master_motor].paracct
            result = acctime / self._step_per_unit
        elif attr_name == 'base_rate':
            result = 0
        else:
            result = MotorController.GetPar(self, axis, name)
        return result

    def getMaxVelocity(self, axis):
        if self._max_vel is None:
            return -1
        else:
            return self._max_vel

    def SendToCtrl(self, cmd):
        """ Send the .
        @param cmd: command to send to the Icepap controller
        @return the result received
        """
        res = 'Done'

        args = cmd.split()
        cmd_type = args[0].upper()
        if cmd_type == 'MOVEP':
            pos = args[1]
            motors = map(int, args[2:])
            self._ipap.movep(pos, motors)
        elif cmd_type == 'LOAD':
            filename = args[1]
            if filename == 'NONE':
                filename = self.DataFile
            self._load_trajectories(filename)
        elif cmd_type == 'PMOVE':
            pos = args[1]
            motors = map(int, args[2:])
            self._ipap.pmove(pos, motors)
        elif cmd_type == 'MAX_VEL':
            res = ''
            for motor in self._motor_list:
                max_par_vel = self._ipap[motor].send_cmd('?parvel max')[0]
                res += '{0} {1};'.format(motor, max_par_vel)
        else:
            res = 'Wrong command'
        return res
