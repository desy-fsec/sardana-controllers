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

from sardana import State
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type

import PyTango


class TfgCTController(CounterTimerController):
    "Tango Sardana Counter/Timer controller for the Time Frame Generator (TFG)"

    gender = "Counter/Timer controller"
    model = "Basic"
    organization = "CELLS - ALBA"
    image = "Lima_ctrl.png"
    logo = "ALBA_logo.png"

    ctrl_attributes = {
        'InvertMask': {
            Type: int,
            'R/W Type': 'READ_WRITE',
            'Description': 'Invert polarity mask (1-inverted)',
            'Defaultvalue': 0},
        'DriveMask': {
            Type: int,
            'R/W Type': 'READ_WRITE',
            'Description': 'Drive strength mask (1-terminated)',
            'Defaultvalue': 0},
        'CCMode': {
            Type: int,
            'R/W Type': 'READ_WRITE',
            'Description': 'Calibration Channel mode mask',
            'Defaultvalue': 2},
        'CCChan': {
            Type: (int,),
            'R/W Type': 'READ_WRITE',
            'Description': 'Calibration Channel configuration',
            'Defaultvalue': [2, -1, 0, 0, 0]},
        'TFout': {
            Type: (int,),
            'R/W Type': 'READ_WRITE',
            'Description': 'Time Frame output configuration',
            'Defaultvalue': [1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
        'Groups': {
            Type: (str,),
            'R/W Type': 'READ_WRITE',
            'Description': 'Time Frame groups',
            'Defaultvalue': ['8', '1', '', '',
                             '1 0 0.001 0 8 0 0',
                             '1 0.999 1 0 1 0 0',
                             '-1 0 0 0 0 0 0',
                             ]},
        }

    ctrl_properties = {
        'TFGDevice': {'type': str,
                      'description': 'TFG device name',
                      'defaultvalue': ''
                      }
        }

    MaxDevice = 8

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug('TFG device: %s' % self.TFGDevice)
        self.tfg = PyTango.DeviceProxy(self.TFGDevice)

    def StateOne(self, axis):
        tfgState = self.tfg.AcqStatus
        self._log.debug('SateOne [%s]' % tfgState)

        if tfgState == 'IDLE':
            return State.Standby, tfgState
        elif tfgState == 'RUNNING':
            return State.Running, tfgState
        elif tfgState == 'PAUSED':
            return State.Running, tfgState
        else:
            return State.Fault, tfgState

    def LoadOne(self, axis, value):
        pass

    def PreStartOne(self, axis, position=None):
        try: 
            self.tfg.SetupPort([self._invertmask, self._drivemask])
            self.tfg.SetupCCMode(self._ccmode)
            self.tfg.SetupCCChan(self._ccchan)
            self.tfg.SetupTFout(self._tfout)
            self.tfg.Enable()
            self.tfg.Clear([0,0,0,100,1,100])
            self.tfg.SetupGroups(self._groups)
        except Exception, e:
            self._log.error(e)

        return True

    def StartOne(self, axis, position=None):
        pass

    def StartAll(self):
        self._log.debug("Start Acq")
        self.tfg.Start()

    def AbortOne(self, axis):
        self.tfg.Stop()

