##############################################################################
#
# This file is part of Sardana
#
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
#
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
# Author: Roberto Homs
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

"""This module contains the definition of a CLAESS pinhole pseudomotor. """


__all__ = ["BL22PinHolePseudoMotor"]

__docformat__ = 'restructuredtext'

from sardana.pool.controller import PseudoMotorController, Description, Type


class BL22PinHolePseudoMotor(PseudoMotorController):
    """"""

    gender = "Coupled"
    model = "TwoCoupled"
    organization = "Sardana Team"

    # theta = bragg
    pseudo_motor_roles = ["Pseudo"]
    motor_roles = ["master", "slave"]

    # Introduce properties here.
    ctrl_properties = {
        # 'tolerance': {Type: float,
        #               Description: 'Tolerance is the maximum difference '
        #                            'between motor positions. If it is -1, '
        #                            'we will not check it'},
    }

    # Introduce attributes here.
    axis_attributes = {}

    def __init__(self, inst, props, *args, **kwargs):

        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("Created a PinHole PseudoMotor")

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        # Validation of position can be included:
        master_current, slave_current = curr_physical_pos
        master_pos = pseudo_pos[0]
        delta_move = master_pos - master_current
        slave_pos = slave_current - delta_move

        return master_pos, slave_pos

    # Calculation of output PseudoMotor values.
    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):
        pos = physical_pos[0]
        return pos
