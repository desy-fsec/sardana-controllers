#############################################################################
##
## file :    LabeledIORegisterCtrl.py
##
## description : 
##
## project :    Sardana/Pool/ctrls/OIRegister
##
## developers history: ctbeamline
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
import copy

from sardana import State, DataAccess
from sardana.pool import PoolUtil

from sardana.pool.controller import IORegisterController
from sardana.pool.controller import Type, Access, Description

LABELS_DOC = ('String with dictionary ')

class LabeledIORController(IORegisterController):
    """
    Base class controller to include the attribute label on the
    IORegisterController.

    The inherited classes should implement the methods:
    * StateOne(self, axis)
    * SetValue(self)
    * GetValue(self)

    If the inherited class wants to have more axis_attributes, it must include
    in its definition the Label attribute and calls to the method
    Get/SetAxisExtraPar of the LabeledIORController to set it.

    """

    model = ""
    organization = "CELLS - ALBA"
    logo = "ALBA_logo.png"

    ctrl_properties = {'Labels': {Description: LABELS_DOC, Type: str}}

    axis_attributes ={
        'Label': {
            Type: str,
            Description: '',
            Access: DataAccess.ReadWrite}
        }
    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        self._labels = eval(self.Labels)

    def ReadOne(self, axis):
        return self.GetValue()

    def WriteOne(self, axis, value):
        if value not in self._labels.keys():
            raise ValueError('The value %s is not defined in Labels. %r' %
                             (value, self._labels.keys()))
        self.SetValue(value)

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar(%d, %s) entering..." % (axis, name))
        name = name.lower()
        if name == "label":
            value = self.GetValue()
            try:
                label = self._labels[value]
            except KeyError:
                raise RuntimeError('GetValue: %r is not defined in Labels.' %
                                   value)
            return label

        else:
            raise ValueError('Wrong parameter.')

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar(%d, %s, %s) entering..." %
                        (axis, name, value))
        name = name.lower()
        value = value.lower()
        if name == "label":
            try:
                labels = [label.lower() for label in self._labels.values()]
                idx = labels.index(value)
                self.SetValue(self._labels.keys()[idx])
            except ValueError:
                raise ValueError('The label %s is not defined in Labels %r' %
                                 (value, labels))
        else:
            raise ValueError('Wrong parameter.')

    def SetValue(self, value):
        raise NotImplementedError("SetValue must be defined in te controller")

    def GetValue(self):
        raise NotImplementedError("GetValue must be defined in te controller")


class TestLabelCtrl(LabeledIORController):

    def StateOne(self, axis):
        return State.On, 'On'

    def SetValue(self, value):
        self._value = value

    def GetValue(self):
        return self._value
