##############################################################################
#
# This file is part of Sardana
#
# http://www.sardana-controls.org/
#
# Copyright 2018 CELLS / ALBA Synchrotron, Cerdanyola del Valles, Spain
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

"""This module contains the definition of a generic operator over 2 values
pseudo counter controller for the Sardana Device Pool"""


from sardana import DataAccess
from sardana.pool.controller import (
    PseudoCounterController, Type, Access, Description, DefaultValue,
    Memorize, Memorized)


__all__ = ['Operator']
__docformat__ = 'restructuredtext'


class Operator(PseudoCounterController):
    """A simple pseudo counter which receives two counter values and returns
    the result of applying the specified operation (default is multiplying)"""

    gender = 'PseudoCounter'
    model = 'Operator'
    organization = 'Sardana team'

    counter_roles = ('value1', 'value2')
    pseudo_counter_roles = ('result',)

    axis_attributes = {
        'formula': {
            Type: str,
            Description: 'Formula to apply to the given values',
            Access: DataAccess.ReadWrite,
            DefaultValue: 'value1 * value2',
            Memorize: Memorized
        },
    }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        # initialize with default (if overwritten SetAxisExtraPar will set it)
        self.formula = self.axis_attributes['formula'][DefaultValue]
        # using lambda is faster than call eval
        self.function = eval('lambda value1, value2: %s' % self.formula)

    def Calc(self, axis, counter_values):
        value1, value2 = counter_values
        try:
            result = self.function(value1, value2)
        except Exception as e:
            msg = ('Error evaluating formula \"%s\" with values (%s)' %
                   (self.formula, str(counter_values)))
            self._log.error(msg)
            raise
        self._log.info('Returning %s: ' % str(result))
        return result

    def GetAxisExtraPar(self, axis, parameter):
        param = parameter.lower()
        if param == 'formula':
            value = self.formula
        else:
            value = PseudoCounterController.GetAxisExtraPar(axis, parameter)
        return value

    def SetAxisExtraPar(self, axis, parameter, value):
        param = parameter.lower()
        if param == 'formula':
            function = eval('lambda value1, value2: %s' % value)
            try:
                function(1.0, 1.0)
            except Exception as e:
                msg = 'Check formula! It fails with 1.0 as params: %s' % str(e)
                raise Exception(msg)
            self.formula = value
            self.function = function
        else:
            PseudoCounterController.SetAxisExtraPar(axis, parameter, value)
        return value
