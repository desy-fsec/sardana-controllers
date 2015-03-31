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
###########################################################################


from sardana import State
from sardana.pool.controller import CounterTimerController, NotMemorized
from sardana.pool.controller import Type, Description, DefaultValue, MaxDimSize

import PyTango
import numpy

class AlbaemAdc18CoTiCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for tests"

    ctrl_properties = {
        'ElectroMeterDevice': {'type': str,
                           'description': 'Detector device name',
                           }
        }

    MaxDevice = 3

    ctrl_extra_attributes = {  "SamplingFrequency": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Albaem sample rate',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "NrOfTriggers": 
                                {'Type':'PyTango.DevLong',
                                 'Description':'Nr of triggers',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "AcquisitionTime": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Acquisition time per trigger',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "TriggerMode": 
                                {'Type':'PyTango.DevString',
                                 'Description':'Trigger mode: soft or gate',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "Data": 
                                {'Type':[float],
                                 'Description':'Trigger mode: soft or gate',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ'
                                }
                            }


    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug('Detector device: %s' % self.ElectroMeterDevice)
        self.det = PyTango.DeviceProxy(self.ElectroMeterDevice)	
	self.contAcqChannels = {}
	self.sampleRate = 0.0

    def StateOne(self, axis):
        self._log.debug('StateOne(%d): entering...' % axis)
        eMeterState = self.det.read_attribute('state').value
        self._log.debug('SateOne [%s]' % eMeterState)
        if eMeterState == PyTango.DevState.STANDBY:
            ret = State.On, eMeterState
        elif eMeterState == PyTango.DevState.RUNNING:
            ret = State.Moving, eMeterState  
        elif eMeterState == PyTango.DevState.ON:
            ret = State.On, eMeterState           
        else:
            ret = State.Unknown, eMeterState
        self._log.debug('StateOne(%d): returning %s' % (axis,repr(ret)))
        return ret

    def ReadOne(self, axis):
        self._log.debug('ReadOne')

	if axis==1:
		value = self.IntegTime
	else:
		buff= self.det.read_attribute('Buffer%d' % (axis-1)).value
                self._log.debug('Buffer Return: '+ repr(buff) + 'type: ' + repr(type(buff)))
                value = buff[0]
        self._log.debug('Value= %s type= %s' % (repr(value),type(value)))
        self._log.debug('ReadOne(%d): returning %f' % (axis,value))
        return float(value)

    def ReadAll(self):
        self._log.debug('ReadAll(): entering...')
        self._log.debug('ReadAll(): leaving...')

    def PreStartOne(self, axis, value=None):
        self._log.debug('PreStartOne(%d): entering...' % axis)
        eMeterState = self.det.read_attribute('state').value
        if eMeterState != PyTango.DevState.STANDBY:
	    self._log.debug('Stoping')	
            self.det.stop()
        self._log.debug('PreStartOne(%d): leaving...' % axis)   
        return True

    def StartOne(self, axis, value=None):
        self._log.debug('StartOne(%d): entering...' % axis)
        self._log.debug('StartOne(%d): leaving...' % axis)
        
    def StartAll(self):
        self._log.debug('StartAll(): entering...')
        self._log.debug("Start Acq")
        self.det.start()     
        self._log.debug('StartAll(): leaving...')

    def LoadOne(self, axis, value):
        self._log.debug('LoadOne(%d): entering...' % axis)
        self.IntegTime= value
        self.det.write_attribute('IntegTime', long(value))
        self.det.write_attribute('NrTriggers', 1)
        self._log.debug('LoadOne(%d): leaving...' % axis)
	
    def AbortOne(self, axis):
        self._log.debug("Stop Acq")
        try:
            self.det.stop()
        except:
            self._log.error('self.det.stop is not posible')
        self._log.debug('AbortOne(%d): leaving...' % axis)


    def SendToCtrl(self, cmd):
	cmd = cmd.lower()
        words = cmd.split(" ")
        ret = "Unknown command"
        if len(words) == 2:
            action = words[0]
            axis = int(words[1])
            if action == "pre-start":
                self._log.debug("SendToCtrl(%s): pre-starting channel %d", cmd, axis)
                self.contAcqChannels[axis] = None
                ret = "Channel %d appended to contAcqChannels" % axis
            elif action == "start":
                self._log.debug("SendToCtrl(%s): starting channel %d", cmd, axis)
                self.contAcqChannels.pop(axis)
                if len(self.contAcqChannels.keys()) == 0:
                    self.det.Start()
                    ret = "Acquisition started"
                else:
                    ret = "Channel %d popped from contAcqChannels" % axis
            elif action == "pre-stop":
                self._log.debug("SendToCtrl(%s): pre-stopping channel %d", cmd, axis)
                self.contAcqChannels[axis] = None
                ret = "Channel %d appended to contAcqChannels" % axis
            elif action == "stop":
                self._log.debug("SendToCtrl(%s): stopping channel %d", cmd, axis)
                self.contAcqChannels.pop(axis)
                if len(self.contAcqChannels.keys()) == 0:
                    self.det.Stop()
                    ret = "Acquisition stopped"
                else:
                    ret = "Channel %d popped from contAcqChannels" % axis
        return ret
	
	
    def GetExtraAttributePar(self, axis, name):
        self._log.debug("GetExtraAttributePar(%d, %s): Entering...", axis, name)
        #attributes used for continuous acquisition
        if name.lower() == "samplingfrequency":
            return 0.0
        if name.lower() == "triggermode":
            return "gate"
        if name.lower() == "nroftriggers":
            nrOfTriggers = self.det["NrTriggers"].value
            return nrOfTriggers
        if name.lower() == "acquisitiontime":
            return 0.0
        if name.lower() == "data":
            data = self.det["Buffer%d" % (axis - 1)].value
            return data

    def SetExtraAttributePar(self,axis, name, value):
        #attributes used for continuous acquisition
        if name.lower() == "samplingfrequency":
            pass
        if name.lower() == "triggermode":
            pass
        if name.lower() == "nroftriggers":
            self.det["NrTriggers"] = value
        if name.lower() == "acquisitiontime":
            pass #TODO:implement meeee!!!
    