#!/usr/bin/env python

import datetime
import numpy
import PyTango, taurus
from sardana import State, DataAccess
from sardana.pool import AcqTriggerType, AcqMode
from sardana.pool.controller import CounterTimerController, Memorize, NotMemorized
from sardana.pool.controller import Type, Access, Description, MaxDimSize
from sardana.tango.core.util import from_tango_state_to_state

from BL29Energy import Energy
import Ni660XPositionCTCtrl


class BL29EnergyCTCtrl(Ni660XPositionCTCtrl.Ni660XPositionCTCtrl):
    "This class is the Ni600X position capture Sardana CounterTimerController"

    MaxDevice = 32
    
    ctrl_properties = { "channelDevNames" : { Type : str, Description : "Comma separated Ni660xCounter device names"}, 
                        'sm_pseudo' : { Type : str, Description : 'The name of the DiscretePseudoMotor to read/select which SM to use'},
                        'gr_pseudo' : { Type : str, Description : 'The name of the DiscretePseudoMotor to read/select which grating to use'}
                      }
    

    def __init__(self, inst, props, *args, **kwargs):
        #Ni660XPositionCTCtrl.__init__(self, inst, props, *args, **kwargs)
        super(BL29EnergyCTCtrl, self).__init__(inst, props, *args, **kwargs)
        self._log.debug("BL29EnergyCTCtrl.__init__(): entering...")
        self._log.debug(repr(self.axis_attributes))
        self.sm = PyTango.DeviceProxy(self.sm_pseudo)
        self.gr = PyTango.DeviceProxy(self.gr_pseudo)

    def PreReadAll(self):
        self.spectrum = None

    def PreReadOne(self,axis):
        pass

    def ReadOne(self, axis):
        self._log.debug('ReadOne(%d): entering...' % axis)
        try:
            data = self.channels[axis]["PositionBuffer"].value
            self._log.debug('ReadOne(%d): data: %s' % (axis, repr(data)))
        except Exception, e:
            self._log.error('ReadOne(%d): Exception while reading buffer: %s' %\
                            (axis, e))
        self._log.debug('ReadOne(%d) data read' % axis)
        try:
            index = self.dataBuff[axis]['index']
        except Exception, e:
            self._log.error('ReadOne(%d): reading index exception %s' % (axis, e))
        self._log.debug('ReadOne(%d) index = %d' % (axis, index))
        if data is None or len(data) == index:
            v = []
            self._log.debug('ReadOne(%d), data empty....' % axis)
        else:
            try:
                tmpIndex = len(data)
                data = data[index:]
                self.dataBuff[axis]['index'] = tmpIndex
                if self.attributes[axis]["sign"] == -1:
                    dataNumpy = numpy.array(data)
                    v = dataNumpy * -1
                else:
                    v = numpy.array(data)
                v = v + self.attributes[axis]["initialposition"]
                v = v.tolist()
                self._log.debug('Ending........, ReadOne')
            except Exception, e:
                self._log.debug('ReadOne(%d): Exception numpy array %s' % (axis, e))

        energies = []
        for encoder_value in v:
            energy_value = Energy.get_energy(self.sm_selected, self.gr_selected, encoder_value, gr_source_is_encoder=True)
            self._log.debug('!!!!!!!!!!!!!!!!!energy = %f; sm_selected = %d; gr_selected = %d, encoder_value = %f' % (energy_value, self.sm_selected, self.gr_selected, encoder_value))
            energies.append(energy_value)
        
        self._log.debug('Finish the calculation........')        
        return energies

    def PreStartAllCT(self):
        self.sm_selected = self.sm.read_attribute('Position').value
        self.gr_selected = self.gr.read_attribute('Position').value
