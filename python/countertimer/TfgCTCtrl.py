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
            'Defaultvalue': 15},
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
        # 'Groups': {
        #     Type: (str,),
        #     'R/W Type': 'READ_WRITE',
        #     'Description': 'Time Frame groups',
        #     'Defaultvalue': ['8', '1', '', '',
        #                      '1 0 0.001 0 8 0 0',
        #                      '1 0.999 1 0 1 0 0',
        #                      '-1 0 0 0 0 0 0',
        #                      ]},
        'Offset': {
            Type: float,
            'R/W Type': 'READ_WRITE',
            'Description': 'Offset',
            'defaultvalue': 0.0
                      },
        'BufferSize': {
            Type: int,
            'R/W Type': 'READ_WRITE',
            'Description': 'BufferSize',
            'defaultvalue': 10000
                      },

        'Nframes': {
            Type: int,
            'R/W Type': 'READ_WRITE',
            'Description': 'Number of Frames',
            'defaultvalue': 1
                      },

        }

    ctrl_properties = {
        'TFGDevice': {'type': str,
                      'description': 'TFG device name',
                      'defaultvalue': ''
                      },

        }



    # Timer + Coutners
    MaxDevice = 9

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug('TFG device: %s' % self.TFGDevice)
        self.tfg = PyTango.DeviceProxy(self.TFGDevice)
        self.values = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.groups = ['8', '1', '', '']
#        self._invertmask = 0
#        self._drivemask = 15
#        self._ccmode = 0
#        self._ccchan = [2, -1, 0, 0, 0]
#        self._tfout = [1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
#        self._buffer_size = 10000

    def AddDevice(self, axis):
        self._log.debug("AddDevice(%d): Entering...", axis)
        pass

    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        pass

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

        if axis == 1:
            newgroup = '%d %f %f 0 7 0 0' % (self._nframes, self._offset, value)
            self.groups.append(newgroup)
        pass

    def PreStartOne(self, axis, position=None):
        try:
            if axis == 1:
                self.tfg.SetupPort([self._invertmask, self._drivemask])
                self.tfg.SetupCCMode(self._ccmode)
                self.tfg.SetupCCChan(self._ccchan)
                self.tfg.SetupTFout(self._tfout)
                self.tfg.Enable()
                self.tfg.Clear([0,0,0,self._buffer_size, 1, 9])
                self.groups.append('-1 0 0 0 0 0 0')
                self.tfg.SetupGroups(self.groups)
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

    def PreReadOne(self, axis):
        self._log.debug("PreReadOne(%d): Entering...", axis)
        pass


    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        self._log.debug(self.values)
        
        return self.values[axis-1]


    def ReadAll(self):
        self._log.debug("ReadAll: Entering...")

        # Read 8 Channels:
        Nch = 8

        ans = self.tfg.Read([0,0,0,1,1,Nch+1])
        self._log.debug(ans)
        #Integrated time in ns
        time = ((ans[1] << 32) + ans[0]) * 10
        self.values[0] = time

        # Counts
        for i in range(Nch):
            val = (ans[(1+i)*2+1] << 32) + ans[(1+i)*2]
            self.values[i+1] = val
        self._log.debug(self.values)
