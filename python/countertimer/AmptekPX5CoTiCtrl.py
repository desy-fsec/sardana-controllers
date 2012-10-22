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
import taurus

from sardana import State
from sardana.pool.controller import CounterTimerController
from sardana.pool import AcqTriggerType

        
class AmptekPX5CounterTimerController(CounterTimerController):
    "This class is the AmptekPX5 Sardana CounterTimerController"

    MaxDevice = 17

    class_prop = {'deviceName':{'Type':str,'Description':'AmptekPX5 Tango device name','DefaultValue':None},}

    axis_attributes = { "lowThreshold"   : { "Type" : long, "R/W Type": "READ_WRITE" },
                        "highThreshold" : { "Type" : long, "R/W Type": "READ_WRITE" }}

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.amptekPX5 = taurus.Device(self.deviceName)
        self.acqTime = 0
        self.sta = State.On
        self.acq = False

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("SetAxisExtraPar() entering...")
        if axis == 1:
            raise Exception("Axis parameters are not allowed for axis 1.")
        name = name.lower()
        scai = axis - 1
        if name == "lowthreshold":
            conf = ["SCAI=%d"%scai, "SCAL"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
        elif name == "highthreshold":
            conf = ["SCAI=%d"%scai, "SCAH"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
        v = long(ret[1].split("=")[1])
        return v

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar() entering...")
        if axis == 1:
            raise Exception("Axis parameters are not allowed for axis 1.")
        name = name.lower()
        scai = axis - 1
        if name == "lowthreshold":
            conf = ["SCAI=%d"%scai, "SCAH"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
            scah = long(ret[1].split("=")[1])
            conf = ["SCAI=%d"%scai, "SCAL=%d"%value, "SCAH=%d"%scah]
            for c in conf:
                self._log.debug("conf: %s" % repr(c))
                self.amptekPX5.SetTextConfiguration([c])
        elif name == "highthreshold":
            conf = ["SCAI=%d"%scai, "SCAL"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
            scal = long(ret[1].split("=")[1])
            conf = ["SCAI=%d"%scai, "SCAL=%d"%scal, "SCAH=%d"%value]
            for c in conf:
                self._log.debug("conf: %s" % repr(c))
                self.amptekPX5.SetTextConfiguration([c])

    def AddDevice(self,ind):
        pass

    def DeleteDevice(self,ind):
        pass

    def PreStateAll(self):
        pass

    def PreStateOne(self, ind):
        pass

    def StateAll(self):
        self._log.debug("StateAll(): entering...")
        sta = self.amptekPX5.State()
        self.status = self.amptekPX5.Status()
        self._log.info("AmptekPX5CounterTimerController StateOne - state = %s" % repr(sta))
        if self.sta == State.Moving and sta != State.Moving:
            self.acq = False
            self.sca_values = self.amptekPX5.LatchGetClearSCA()
        self.sta = sta

    def StateOne(self, ind):
        return self.sta, self.status

    def PreReadAll(self):
        pass

    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        self._log.debug("ReadOne(%d): entering..." % ind)
        if ind == 1:
            val = self.acqTime
        else:
            val = self.sca_values[ind-2]
        self._log.debug("ReadOne(%d): returning %d" % (ind,val))
        return val

    def PreStartAllCT(self):
        self.amptekPX5.ClearSpectrum()
        self.amptekPX5.LatchGetClearSCA()
        self.sca_values = [0] * 16

    def PreStartOneCT(self, ind):
        return True

    def StartOneCT(self, ind):
        pass

    def StartAllCT(self):
        self._log.debug("StartAllCT(): entering...")
        self.amptekPX5.Enable()
        self.acq = True

    def LoadOne(self, ind, value):
        self._log.debug("LoadOne(): entering...")
        self.acqTime = value
        self.amptekPX5.SetTextConfiguration(['PRET=%f'%value])

    def AbortOne(self, ind):
        self.amptekPX5.Disable()