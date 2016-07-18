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

from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, Access, Description, Memorize, NotMemorized, MaxDimSize, DefaultValue

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
            Access: DataAccess.ReadWrite,
            Description: 'Invert polarity mask (1-inverted)',
            DefaultValue: 0},
        'DriveMask': {
            Type: int,
            Access: DataAccess.ReadWrite,
            Description: 'Drive strength mask (1-terminated)',
            DefaultValue: 15},
        'CCMode': {
            Type: int,
            Access: DataAccess.ReadWrite,
            Description: 'Calibration Channel mode mask',
            DefaultValue: 2},
        'CCChan': {
            Type: (int,),
            Access: DataAccess.ReadWrite,
            Description: 'Calibration Channel configuration',
            Memorize: Memorize},
        'TFout': {
            Type: (int,),
            Access: DataAccess.ReadWrite,
            Description: 'Time Frame output configuration',
            Memorize: Memorize},
        'Offset': {
            Type: float,
            Access: DataAccess.ReadWrite,
            Description: 'Offset',
            DefaultValue: 0.0
                      },
        'BufferSize': {
            Type: int,
            Access: DataAccess.ReadWrite,
            Description: 'BufferSize',
            DefaultValue: 10000
                      },
        #'OutputMask': {
            #Type: int,
            #Access: DataAccess.ReadWrite,
            #Description: 'Mask for enabled output channels',
            #DefaultValue: 7
                      #},

        'Nframes': {
            Type: int,
            Access: DataAccess.ReadWrite,
            Description: 'Number of Frames',
            DefaultValue: 1
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
        #self._invertmask = 0
        #self._drivemask = 15
        #self._ccmode = 0
        self._ccchan = [2, -1, 0, 0, 0]
        self._tfout = [1, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        #self._buffer_size = 10000

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
	    #TODO use attribute
	    self._outputmask = 7
            newgroup = '%d %f %f 0 %d 0 0' % (self._nframes, self._offset, value, self._outputmask)
            self.groups = ['8', '1', '', '',newgroup]
            self.tfg.SetupPort([self._invertmask, self._drivemask])
            self.tfg.SetupCCMode(self._ccmode)
            self.tfg.SetupCCChan(self._ccchan)
            self.tfg.SetupTFout(self._tfout)
            self.tfg.Enable()
            self.tfg.Clear([0,0,0,self._buffersize, 1, 9])
            self.groups.append('-1 0 0 0 0 0 0')
            self.tfg.SetupGroups(self.groups)
        pass

    def PreStartOne(self, axis, position=None):

        #try:
            #if axis == 1:
                #self.tfg.SetupPort([self._invertmask, self._drivemask])
                #self.tfg.SetupCCMode(self._ccmode)
                #self.tfg.SetupCCChan(self._ccchan)
                #self.tfg.SetupTFout(self._tfout)
                #self.tfg.Enable()
                #self.tfg.Clear([0,0,0,self._buffer_size, 1, 9])
                #self.groups.append('-1 0 0 0 0 0 0')
                #self.tfg.SetupGroups(self.groups)
        #except Exception, e:
            #self._log.error(e)

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

	# To convert nanoseconds to seconds
        self.values[0] = time/1e9

        # Counts
        for i in range(Nch):
            val = (ans[(1+i)*2+1] << 32) + ans[(1+i)*2]
            self.values[i+1] = val
        self._log.debug(self.values)

    
    def SetCtrlPar(self, parameter, value):
        param = parameter.lower()
        if param == 'invertmask':
            self._invertmask = value
        elif param == 'drivemask':
            self._drivemask = value
        elif param == 'ccmode':
            self._ccmode = value
        elif param == 'ccchan':
            self._ccchan = value
	    print 'cccchan %s'%str(self._ccchan)
        elif param == 'tfout':
            self._tfout = value
        elif param == 'offset':
            self._offset = value
        elif param == 'buffersize':
            self._buffersize = value
        elif param == 'nframes':
            self._nframes = value
        else:
            super(TfgCTController, self).SetCtrlPar(parameter, value)




    def GetCtrlPar(self, parameter):
        param = parameter.lower()
        if param == 'invertmask':
            value = self._invertmask
        elif param == 'drivemask':
            value = self._drivemask
        elif param == 'ccmode':
            value = self._ccmode
        elif param == 'ccchan':
            value = self._ccchan
        elif param == 'tfout':
            value = self._tfout
        elif param == 'offset':
            value = self._offset
        elif param == 'buffersize':
            value = self._buffersize
        elif param == 'nframes':
            value = self._nframes
        else:
            value = super(TfgCTController, self).GetCtrlPar(parameter)
        return value 