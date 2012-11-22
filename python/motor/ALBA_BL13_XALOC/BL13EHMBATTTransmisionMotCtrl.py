from sardana import pool
from sardana import State
from sardana.pool import PoolUtil
from sardana.pool.controller import MotorController
import time
import taurus
import PyTango

import transmission

class BL13EHMBATTTransmissionController(MotorController):
    """ This controller provides the transmission motor."""

    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.eps_dev = taurus.Device('bl13/ct/eps-plc-01')
        self.energy_mot = PoolUtil.get_motor(inst, 'E')
        # RIGHT NOW, ONLY WORKING WITH THE 7 ALUMINIUM FOILS
        self.foils = ['mbat16', 'mbat15', 'mbat14', 'mbat13', 'mbat12', 'mbat11', 'mbat26']
        self.last_state = None
        self.last_read = None

    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass
    
    def StateOne(self, axis):
        try:
            foil_qualities = [att_read.quality for att_read in self.eps_dev.read_attributes(self.foils)]
            if PyTango.AttrQuality.ATTR_CHANGING in foil_qualities:
                status = 'Device is MOVING.\nQualities: '+str(foil_qualities)
                self.last_state = State.Moving, status, 0
            self.last_state = State.On, 'Device is ON', 0
        except Exception,e:
            self._log.warning('Exception trying to read from EPS-PLC.\n'+str(e))

        return self.last_state

    def ReadOne(self, axis):
        try:
            energy = self.energy_mot.position
            foil_values = [att_read.value for att_read in self.eps_dev.read_attributes(self.foils)]
            calculated_transmission = transmission.GetMBATTransmission(foil_values, energy) * 100.0
            self.last_read = calculated_transmission
            return calculated_transmission
        except Exception,e:
            self._log.warning('Exception trying to read from EPS-PLC.\n'+str(e))

        return self.last_read

    def StartAll(self):
        # THIS IS NEEDED BY THE POOL
        pass

    def StartOne(self, axis, pos):
        energy = self.energy_mot.position

        target_transmission = pos / 100.0
        foil_values, calculated_transmission = transmission.GetMBATconfig(target_transmission, energy)
        foil_tango_values = map(int, foil_values)
        write_attributes_argument = zip(self.foils, foil_tango_values)

        try:
            self.eps_dev.write_attributes_asynch(write_attributes_argument)
        except Exception,e:
            self._log.warning('An exception ocurred while trying to change transmission.\n'+str(e))

    def AbortOne(self, axis):
        pass
