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
        if motor_vel == 0:
            par_vels.append(0)
            continue
        ti = abs(abs(lpos[i+1]) - abs(lpos[i])) / float(motor_vel)
        if ti == 0:
            par_vels.append(float('inf'))
        else:
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
        # TODO: Design implementation for the other benders
        'cabu_addr': {Type: int, Description: 'Motor axis number'},
        'cabd_addr': {Type: int, Description: 'Motor axis number'},

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
        'BenderOn': {Type: bool, Access: DataAccess.ReadWrite},
        'StatusDetails': {Type: str, Access: DataAccess.ReadOnly},
        'MasterPos': {Type: float, Access: DataAccess.ReadOnly},
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
        aliases['cabu'] = self.cabu_addr
        aliases['cabd'] = self.cabd_addr

        self._trajdic = None
        self._ipap.add_aliases(aliases)
        # TODO: Include on the trajectory tables the cslxr motor.
        # Exclude caz
        self._motors_names = ['cay', 'caxr', 'cdy', 'cdz', 'cdxr', 'cslxr']
        self._bender_names = ['cabu', 'cabd']
        self._all_motor_names = self._motors_names + self._bender_names
        self._bender_on = True
        self._master_name = 'caxr'
        self._tolerance = self.Tolerance
        self._velocity = None
        self._acctime = 0
        self._max_vel = None
        self._sync = []
        self._out_pos = []
        self._state = State.On
        self._status = 'State OK'

    @property
    def motor_names(self):
        if self._bender_on:
            return self._all_motor_names
        else:
            return self._motors_names

    def _load_trajectories(self, filename):
        with open(filename) as f:
            self._trajdic = pickle.load(f)
        par = list(self._trajdic['bragg'])

        self._max_vel = None
        max_vels = []
        for motor_name in self._all_motor_names:
            motor_table = list(self._trajdic[motor_name])
            self._ipap[motor_name].clear_parametric_table()
            self._ipap[motor_name].set_parametric_table(par, motor_table,
                                                        mode='SPLINE')
            motor_vel = self._ipap[motor_name].velocity
            max_vel = get_max_vel(par, motor_table, motor_vel)
            max_vels.append(max_vel)
            self._log.debug('{0} {1}'.format(motor_name, max_vel))
        self._max_vel = min(max_vels)

    def _set_vel(self, vel):
        for motor in self._all_motor_names:
            self._ipap[motor].parvel = vel

    def _set_acctime(self, acctime):
        for motor in self._all_motor_names:
            self._ipap[motor].paracct = acctime

    def _find_near_bragg(self, motor_name):
        is_cdz = False
        if motor_name == 'cdz':
            is_cdz = True
            motor_name = 'cdy'
        current_steps = self._ipap[motor_name].pos
        traj_pos = np.array(self._trajdic[motor_name])
        idx_min = (np.abs(traj_pos - current_steps)).argmin()
        par_name = 'bragg'
        if is_cdz:
            motor_name = 'cdz'
            current_steps = self._ipap[motor_name].pos

        bragg_pos = self._trajdic[par_name][idx_min]
        spu = self._trajdic['spu'][motor_name]
        offset = self._trajdic['offset'][motor_name]
        sign = self._trajdic['sign'][motor_name]
        motor_steps = self._trajdic[motor_name][idx_min]
        motor_pos = (motor_steps * sign / spu) + offset
        current_pos = (current_steps * sign / spu) + offset
        return bragg_pos, current_pos, motor_pos

    def _sync_check(self):
        sync = []

        for motor_name in self.motor_names:
            try:
                self._ipap[motor_name].parpos
            except Exception:
                near_bragg, current_pos, motor_pos = self._find_near_bragg(
                    motor_name)
                msg = '{0} ({1}) is near to ({2}) ' \
                      '{3}\n'.format(motor_name, current_pos, motor_pos,
                                     near_bragg)
                sync.append(msg)

        self._sync = sync

    def _out_pos_check(self):
        out_pos = []
        if self._state != State.Moving:
            master_pos = self._ipap[self._master_name].parpos
            out_pos = []
            msg = '{0} in {1} and should be in {2}\n'
            for motor_name in self.motor_names:
                motor_pos = self._ipap[motor_name].parpos
                diff = abs(abs(motor_pos) - abs(master_pos))
                is_close = diff <= self._tolerance
                if not is_close:
                    out_pos.append(msg.format(motor_name, motor_pos,
                                              master_pos))
        self._out_pos = out_pos

    def AddDevice(self, axis):
        """ Set default values for the axis and try to connect to it
        @param axis to be added
        """
        self._step_per_unit = 1
        self._load_trajectories(self.DataFile)

    def DeleteDevice(self, axis):
        # Todo analyze if is necesary
        pass
        # for motor_name in self._all_motor_names:
        #     self._ipap[motor_name].clear_parametric_table()

    def PreStateOne(self, axis):
        motors_states = self._ipap.get_states(self.motor_names)
        moving = []
        alarm = []

        for motor_state, motor_name in zip(motors_states, self.motor_names):
            moving_flags = [motor_state.is_moving(),
                            motor_state.is_settling()]
            if any(moving_flags):
                moving.append(motor_name)

            alarm_flags = [motor_state.is_limit_positive(),
                           motor_state.is_limit_negative(),
                           not motor_state.is_poweron()]
            if any(alarm_flags):
                alarm.append(motor_name)

        if len(moving) > 0:
            self._state = State.Moving
            self._status = 'The motors {0} are ' \
                           'moving.'.format(' '.join(moving))
        elif len(alarm) > 0:
            self._state = State.Alarm
            self._status = 'The motors {0} are in alarm ' \
                           'state'.format(' '.join(alarm))
        else:
            self._state = State.On
            self._status = 'All motors are ready'

        return True

    def StateOne(self, axis):
        """
        Connect to the hardware and check the state. If no connection
        available, return ALARM.
        @param axis to read the state
        @return the state value: {ALARM|ON|MOVING}
        """

        self._sync_check()
        if len(self._sync) == 0:
            self._out_pos_check()
        if len(self._sync) > 0 or len(self._out_pos) > 0:
            state = State.Alarm
            status = 'There are motors not synchronized, use ' \
                     'clearStatus for more details.'
            return state, status

        return self._state, self._status

    def ReadOne(self, axis):
        """ Read the position of the axis.
        @param axis to read the position
        @return the current axis position
        """

        state, status = self.StateOne(axis)
        if state == State.Alarm:
            raise RuntimeError(status)
        pos = self._ipap[self._master_name].parpos

        return pos

    def StartOne(self, axis, pos):
        """ Start movement of the axis.
        :param axis: int
        :param pos: float
        :return: None
        """
        state, status = self.StateOne(axis)
        if state != State.On:
            raise RuntimeError(status)
        self._ipap.pmove(pos, self.motor_names, group=True)

    def StopOne(self, axis):
        """
        Stop axis
        :param axis: int
        :return: None
        """
        self._ipap.stop(self.motor_names)

    def AbortOne(self, axis):
        """
        Abort movement
        :param axis: int
        :return: None
        """
        self._ipap.abort(self.motor_names)

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
            vel = self._ipap[self._master_name].parvel
            result = vel / self._step_per_unit
        elif attr_name == 'acceleration' or attr_name == 'deceleration':
            acctime = self._ipap[self._master_name].paracct
            result = acctime
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

    def getStatusDetails(self, axis):
        if len(self._sync) > 0:
            sync_err = ' '.join(self._sync)
            return 'There are motors not synchronized (use clearSync ' \
                   'macro):\n {0}'.format(sync_err)
        if len(self._out_pos) > 0:
            out_pos_err = ' '.join(self._out_pos)
            return 'There are motors out of position (use clearMoveTo ' \
                   'macro):\n {0}'.format(out_pos_err)

        return 'The motors are synchronized.'

    def getMasterPos(self, axis):
        bragg_pos, _, _ = self._find_near_bragg('caxr')
        return bragg_pos

    def setBenderOn(self, axis, value):
        self._bender_on = value

    def getBenderOn(self, axis):
        return self._bender_on

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
            for motor in self._motors_names:
                max_par_vel = self._ipap[motor].send_cmd('?parvel max')[0]
                res += '{0} {1};'.format(motor, max_par_vel)
        else:
            res = 'Wrong command'
        return res
