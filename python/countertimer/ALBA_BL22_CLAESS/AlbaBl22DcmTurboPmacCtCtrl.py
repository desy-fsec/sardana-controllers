#!/usr/bin/env python
import numpy
import PyTango
from sardana import State, DataAccess
from sardana.sardanavalue import SardanaValue
from sardana.pool import AcqSynch
from sardana.pool.controller import (CounterTimerController, Type, Access,
                                     Description)

from bl22dcmlib import enegies4encoders

PMAC_REGS = {'MotorDir': 4080, 'StartBuffer': 4081, 'RunProgram': 4082,
             'NrTriggers': 4083, 'Index': 4084, 'StartPos': 4085,
             'PulseWidth': 4086, 'AutoInc': 4087}


class AlbaBl22DcmTurboPmacCoTiCtrl(CounterTimerController):
    """
    This class is the Sardana CounterTimer controller for TurboPmac controller.
    It is used to """

    MaxDevice = 1
    class_prop = {
        'TurboPmacDSName': {'Description': 'TurboPmac controller Tango device',
                            'Type': 'PyTango.DevString'},
        'EnergyDSName': {'Description': 'Energy pseudomotor Tango device',
                         'Type': 'PyTango.DevString'},
        'BraggDSName': {'Description': 'Bragg motor Tango device',
                        'Type': 'PyTango.DevString'},
        'XtalIORDSName': {'Description': 'Crystal IORegister Tango device',
                          'Type': 'PyTango.DevString'},
        'VCMPitchDSName': {'Description': 'VCM pitch pseudomotor Tango device',
                           'Type': 'PyTango.DevString'},
        'ChunkSize': {'Description': 'Chunk size to read from the pmac',
                      'Type': 'PyTango.DevLong'}}

    axis_attributes = {'InternalTriggers':
                       {Type: bool,
                        Description: 'If you want to share the same formula '
                                     'for all the channels set it to true"',
                        Access: DataAccess.ReadWrite
                        }}
    maxLen = 100

    def __init__(self, inst, props, *args, **kwargs):
        #        self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.nrOfTriggers = 4000

        self.pmac = PyTango.DeviceProxy(self.TurboPmacDSName)
        self.energy = PyTango.DeviceProxy(self.EnergyDSName)
        self.bragg = PyTango.DeviceProxy(self.BraggDSName)
        self.vcm_pitch = PyTango.DeviceProxy(self.VCMPitchDSName)
        self.xtal = PyTango.DeviceProxy(self.XtalIORDSName)

        self.start_buffer = int(self.pmac.GetPVariable(
            PMAC_REGS['StartBuffer']))
        self._int_trigger = False
        self._latency_time = 0.005

    def AddDevice(self, axis):
        self._log.debug("AddDevice(%d): Entering...", axis)

    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)

    def StateAll(self):
        try:
            m = int(self.pmac.GetMVariable(3300))
        except PyTango.DevFailed, e:
            msg = "StateAll(): Could not verify state of the " \
                  "device: %s.\nException: %s" % (self.TurboPmacDeviceName, e)
            self._log.error(msg)
            self.state = State.Unknown
            self.status = msg
        # value 0 means that plc0 is enabled, and value 1 means that plc0
        # is disabled
        if bool(m):
            self.state = State.On
            self.status = "Plc0 is disabled"
        else:
            self.state = State.Moving
            self.status = "Plc0 is enabled"

    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Leaving...%s %s", axis, self.state,
                        self.status)
        return self.state, self.status

    def ReadOne(self, axis):
        if self._synchronization in [AcqSynch.SoftwareTrigger,
                                     AcqSynch.SoftwareGate]:
            energy = self.energy.read_attribute('position').value
            return_value = SardanaValue(energy)

        else:
            try:
                # Hardware synchronization
                register_ranges = []
                current_idx = int(self.pmac.GetPVariable(PMAC_REGS['Index']))
                new_data = current_idx - self.start_idx

                if new_data == 0 or ((new_data < self.ChunkSize) and
                                     current_idx < self.repetitions):
                    return []

                # composing ranges in case of multiple queries
                start_register = self.start_buffer + self.start_idx
                end_register = self.start_buffer + current_idx - 1
                while (end_register - start_register) > self.maxLen:
                    endOfRange = start_register + (self.maxLen - 1)
                    register_ranges.append([start_register, endOfRange])
                    start_register = endOfRange + 1
                else:
                    register_ranges.append([start_register, end_register])
                rawCounts = numpy.array([])
                for r in register_ranges:
                    rawCounts = numpy.append(rawCounts,
                                             self.pmac.GetPVariableRange(r))
                self.start_idx = current_idx

                rawCounts = rawCounts.astype(long)

                msg = '%r %r %r %r %r %r %r %r' % (rawCounts,
                                                   self.vcm_pitch_rad,
                                                   self.xtal_d,
                                                   self.xtal_offset,
                                                   self.bragg_spu,
                                                   self.bragg_offset,
                                                   self.bragg_pos,
                                                   self.bragg_enc)
                self._log.debug(msg)

                return_value = enegies4encoders(rawCounts,
                                                self.vcm_pitch_rad,
                                                self.xtal_d,
                                                self.xtal_offset,
                                                self.bragg_spu,
                                                self.bragg_offset,
                                                self.bragg_pos,
                                                self.bragg_enc).tolist()

            except Exception as e:
                self._log.error('PmacCT %r' % e)

        return return_value

    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        self.pmac.command_inout("DisablePLC", 0)

    def StartAllCT(self):
        """
        Starting the acquisition is done only if before was called
        PreStartOneCT for master channel.
        """
        self._log.debug("StartAllCT(): Entering...")

        if self._synchronization in [AcqSynch.SoftwareTrigger,
                                     AcqSynch.SoftwareGate]:
            pass
        elif not self._int_trigger:
            self.start_idx = 0
            self.bragg_spu = self.bragg.read_attribute('step_per_unit').value
            self.bragg_offset = self.bragg.read_attribute('offset').value
            self.bragg_pos = float(self.pmac.SendCtrlChar("P").split()[0])
            self.bragg_enc = float(self.pmac.GetMVariable(101))
            vcm_pitch = self.vcm_pitch.read_attribute('position').value
            self.vcm_pitch_rad = vcm_pitch/1000.0
            xtal_value = self.xtal.read_attribute('value').value
            if xtal_value == 311:
                d_attr = 'dSi311'
                offset_attr = 'angularOffsetSi311'
            else:
                d_attr = 'dSi111'
                offset_attr = 'angularOffsetSi111'
            self.xtal_d = self.energy.read_attribute(d_attr).value
            self.xtal_offset = self.energy.read_attribute(offset_attr).value

            self.pmac.SetPVariable([PMAC_REGS['RunProgram'], 3])
            self.pmac.DisablePLC(0)
            # configuring position capture control
            self.pmac.SetIVariable([7012, 2])
            # configuring position capture flag select
            self.pmac.SetIVariable([7013, 3])
            # after enabling position capture, M117 is set to 1, forcing
            # readout of M103, to reset it, so PLC0 won't copy outdated data
            self.pmac.GetMVariable(103)
            # enabling plc0 execution
            self.pmac.SetIVariable([5, 3])
            self.pmac.EnablePLC(0)

    def LoadOne(self, axis, value, repetitions):
        try:
            self.repetitions = repetitions
            self.pmac.SetPVariable([PMAC_REGS['NrTriggers'], repetitions])
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not configure device.\n"
                            "Exception: %s", axis, value, e)
            raise

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar(%d, %s): Entering...", axis, name)
        if name.lower() == 'internaltriggers':
            return self._int_trigger

    def SetAxisExtraPar(self, axis, name, value):
        if name.lower() == 'internaltriggers':
            self._int_trigger = value
