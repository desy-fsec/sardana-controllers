##############################################################################
#
# This file is part of Sardana
#
# http://www.sardana-controls.org
#
# Copyright 2016 CELLS / ALBA Synchrotron, Cerdanyola del Valles, Spain
# Author: Jairo Moldes
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


"""This module contains the definition of a grouped pseudomotor controllers"""


import json

from sardana import DataAccess, DataType
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description


__all__ = ['DiscretizedPseudoMotorController']


CALIBRATION = 'Calibration'
LABELS = 'Labels'


class DiscretizedPseudoMotorController(PseudoMotorController):
    """
    This class is meant to implement a basic logic which bind one or more
    physical motor positions to different values of a pseudo motor.

    In order to use more than one physical motor you must use a extremely dirty
    hack. Sardana does not allow a controller to dynamically define its
    "motor_roles" when creating the controller. In order to overcome this
    limitation you can first define a controller with only one physical motor
    and then manually do:
     1) modify the "motor_roles_ids" property of the tango device of the
        controller in order to include all the physical motor IDs
     2) modify the "elements" property of the tango device of the pseudo motor
        in order to include all the physical motor IDs
    After a Pool restart you controller will include all the physical motors.

    The controller needs two properties to be correctly defined:

    - Calibrations. This is a list of lists. Each list consists of as many
      elements as used physical motors and it represents a valid combination of
      physical motor positions. Each item in the list can be:
        a.- List of three elements [min, cal, max] which represents a valid
            range in which the corresponding physical motor is considered to be
            in a valid position.
        b.- None if the corresponding physical motor is ignored for the
            corresponding combination of motors.

    - Labels. This is a list of strings that define a user description of each
      of the corresponding list of the physical motor combinations defined in
      the calibrations property.

    Note that since there are no restrictions at all for the calibrations
    property it may be possible (specially if you use None for some of the
    physical motor calibrations) that the current physical motor positions may
    match more than one element in the calibrations property: in that case we
    consider the pseudo motor to be in the first combination of the list which
    matches the maximum number of non None motor positions.
    """

    CALIBRATION = 'calibration'
    LABELS = 'labels'
    USER_IDX_OFFSET = 'user_idx_offset'

    gender = 'DiscretizedPseudoMotorController'
    model = 'PseudoMotor'
    organization = 'Sardana team'
    image = ''

    pseudo_motor_roles = ('OutputMotor',)
    motor_roles = ('InputMotor',)

    axis_attributes = {
        CALIBRATION: {
            Type: DataType.String,
            Description:
                'List of lists of triples containing [min,cal,max] or None if'
                ' the corresponding motor is to be ignored',
            Access: DataAccess.ReadWrite,
        },
        LABELS: {
            Type: DataType.String,
            Description:
                'List of strings: each string is the description of the '
                'corresponding physical motor positions combination defined in'
                ' the CALIBRATION property.',
            Access: DataAccess.ReadWrite,
        },
        USER_IDX_OFFSET: {
            Type: DataType.Double,
            Description: 'Some users requested the pseudo motor values to'
                'start in 1 instead of 0: this offset allows to treat index 0'
                'as 0+user_idx_offset',
            Access: DataAccess.ReadWrite,
        }
    }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.calibrations = None
        self.labels = None
        self.user_idx_offset = 0

    def CalcPseudo(self, axis, physical_positions, current_pseudo_positions):
        self._log.debug('CalcPseudo: %s' % str(physical_positions))
        best_match = None
        max_motors_matched = 0
        for idx, ranges in enumerate(self.calibrations):
            motors_matched = 0
            for physical, range_ in zip(physical_positions, ranges):
                if range_ is None:
                    pass
                elif len(range_) != 3:
                    raise Exception('Incorrect calibration configuration')
                elif physical >= range_[0] and physical <= range_[2]:
                    motors_matched += 1
                else:
                    break
            else:
                if motors_matched > max_motors_matched:
                    best_match = idx
                    max_motors_matched = motors_matched
        return best_match + self.user_idx_offset

    def CalcAllPhysical(self, pseudo_positions, current_physical_positions):
        self._log.debug('CalcAllPhysical: %s' % str(pseudo_positions))
        idx = int(pseudo_positions[0]) - self.user_idx_offset
        if idx < 0 or idx > len(self.labels):
            msg = 'Motor position out of range'
            self._log.error(msg)
            raise Exception(msg)
        try:
            physical_positions = []
            ranges = self.calibrations[idx]
            for range_ in ranges:
                physical_positions.append(range_[1])
        except:
            msg = ('Unable to get calibration for axis %d and pseudo %d' %
                   (idx, pseudo_positions[0]))
            self._log.error(msg)
            raise Exception(msg)
        return physical_positions

    def GetAxisExtraPar(self, axis, name):
        name = name.lower()
        if name == self.CALIBRATION:
            return json.dumps(self.calibrations)
        elif name == self.LABELS:
            return json.dumps(self.labels)
        elif name == self.USER_IDX_OFFSET:
            return self.user_idx_offset
        else:
            pass

    def SetAxisExtraPar(self, axis, name, value):
        if type(value) is str and len(value) > 0:
            values = json.loads(value)
        else:
            values = []
        name = name.lower()
        if name == self.CALIBRATION:
            self.calibrations = values
        elif name == self.LABELS:
            self.labels = values
        elif name == self.USER_IDX_OFFSET:
            self.user_idx_offset = value
        else:
            pass
