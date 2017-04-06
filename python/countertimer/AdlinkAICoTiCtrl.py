#!/usr/bin/env python
import time
import Queue

import PyTango
from sardana import State, DataAccess
from sardana.sardanavalue import SardanaValue
from sardana.pool import AcqSynch
#from sardana.pool import AcqTriggerType, AcqMode
from sardana.pool.controller import (CounterTimerController, Type, Access,
                                     Description)
from sardana.tango.core.util import from_tango_state_to_state


def evalState(state):
    """This function converts Adlink device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return State.Moving
    elif state == PyTango.DevState.STANDBY:
        return State.On
    else:
        return from_tango_state_to_state(state)


class ListenerDataReady(object):

    def __init__(self, queue, log=None):
        self.queue = queue
        self.start_index = 0
        self.log = log

    def push_event(self, event):

        if self.log:
            self.log.debug('Listener DataReadyEvent received')

        if not event.err:
            new_index = event.ctr - 1
            attr_name = event.attr_name.split('/')[-1]
            device = event.device
            data = device.getdata(([self.start_index, new_index], [attr_name]))
            data = data.tolist()
            self.queue.put(data)
            self.log.debug(' - getting data from %s to %s - total received: '
                           '%s' % (self.start_index, new_index, len(data)))

            self.start_index = new_index + 1
        else:
            e = event.errors[0]
            msg = ('Event error (reason: %s; '
                   'description: %s)' % (e.reason, e.desc))
            self.log.debug(msg)
            raise Exception('ListenerDataReady event with error')


class AdlinkAICoTiCtrl(CounterTimerController):
    """
    This class is the Sardana CounterTimer controller for the Adlink adc
    based counters.

    The only way to use this controller is to define up to 5 channels and
    create a measurement group where the first channel is a master channel.
    The Adlink card works in a way where acquisition for all channels is
    started only once and in controller this is done when StartsAll()
    method was called for this controller, only when PreStartOne() was
    called for master channel.

    Configuration of Adlink card is done in LoadOne() method where size of
    acquisition buffer is calculated from acquisition time and SampleRate
    property.

    Value returned by a channggel is an average of buffer values. If you need
    also standard deviation of these values you can read it from extra
    attribute SD right after reading value of the channel.

    If you need SD value in measurement group you have two options:
       1- Add one tango attribute counter per each SD and place it in a
          measurement group after corresponding Adlink counter.
       2- Add an ExtraColumn with the attribute SD.
    """

    MaxDevice = 5

    class_prop = {'AdlinkAIDeviceName': {'Description': 'AdlinkAI Tango device',
                                         'Type': 'PyTango.DevString'},
                  'SampleRate': {'Description': 'SampleRate set for AIDevice',
                                 'Type': 'PyTango.DevLong'}}

    axis_attributes = {"SD":
                       {Type: float,
                        Description: 'Standard deviation',
                        Access: DataAccess.ReadWrite
                        },
                       "FORMULA":
                       {Type: str,
                        Description: 'The formula to get the real value.\n '
                                     'e.g. "(VALUE/10)*1e-06"',
                        Access: DataAccess.ReadWrite
                        },
                       "SHAREDFORMULA":
                       {Type: bool,
                        Description: 'If you want to share the same formula '
                                     'for all the channels set it to true"',
                        Access: DataAccess.ReadWrite
                        },
                       }


    def __init__(self, inst, props, *args, **kwargs):
        #        self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst),
                        repr(props))
        self.sd = {}
        self.formulas = {}
        self.sharedFormula = {}
        self.contAcqChannels = {}
        self.intTime = 0
        self.dataBuff = {}
        self.wrongVersion = False
        self._synchronization = None
        self._repetitions = 0
        self._latency_time = 1e-6 # 1 us

        try:
            self.AIDevice = PyTango.DeviceProxy(self.AdlinkAIDeviceName)
            cmdlist = [c.cmd_name for c in self.AIDevice.command_list_query()]
            if 'ClearBuffer' not in cmdlist:
                self._log.error(
                    "__init__(): Looks like ADlink device server version is "
                    "too old for this controller version. Please upgrade "
                    "Device server\n")
                self.wrongVersion = True
        except PyTango.DevFailed, e:
            self._log.error("__init__(): Could not create a device proxy from "
                            "following device name: %s.\nException: %s",
                            self.AdlinkAIDeviceName, e)
            raise

    def AddDevice(self, axis):
        self._log.debug("AddDevice(%d): Entering...", axis)
        self.sd[axis] = 0
        self.formulas[axis] = 'value'
        self.sharedFormula[axis] = False
        # buffer for the continuous scan
        self.dataBuff[axis] = {}
        if axis != 1:
            self.dataBuff[axis]['queue'] = Queue.Queue()
            self.dataBuff[axis]['value'] = []
            self.dataBuff[axis]['id'] = None
            self.dataBuff[axis]['cb'] = None
            self.dataBuff[axis]['counter'] = 0
        else:
            self.dataBuff[axis]['follow_chn'] = 1

    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        self.sd.pop(axis)
        self.formulas.pop(axis)
        self.sharedFormula.pop(axis)
        if self._synchronization == AcqSynch.HardwareTrigger:
            self.dataBuff[axis] = {}

        id = self.dataBuff[axis].get('id')

        if self._synchronization == AcqSynch.HardwareTrigger and id is not None:
            self.AIDevice.unsubscribe_event(id)
            self._log.debug('DeleteDevice(%d): Unsubcribe event id:%d', axis,
                            id)

    def getDeviceState(self):
        if self.wrongVersion:
            self._log.error(
                "__init__(): Looks like ADlink device server version is too "
                "old for this controller version. Please upgrade Device "
                "server\n")

        if self.AIDevice is None or self.wrongVersion:
            state = PyTango.DevState.FAULT
        else:
            state = self.AIDevice.state()
        return state

    def unsubscribeEvent(self, axis):
        id = self.dataBuff[axis].get('id')
        if id is None:
            return
        self.AIDevice.unsubscribe_event(id)
        self._log.debug('Unsubscribe event id: %d for axis: %d' %
                        (id, axis))
        self.dataBuff[axis]['id'] = None

    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        try:
            self.state = self.getDeviceState()
            if (self._synchronization == AcqSynch.HardwareTrigger and
                self.state == PyTango.DevState.ON and
                self.dataBuff[axis]['counter'] < self._repetitions):
                    self.state = PyTango.DevState.RUNNING
            state = evalState(self.state)
            status = "AI DeviceProxy present."
        except Exception, e:
            if self._synchronization == AcqSynch.HardwareTrigger:
                self.unsubscribeEvent(axis)
            state = State.Unknown
            status = "AI DeviceProxy is not responding."
        self._log.debug("StateOne(%d): state = %r status = %r" %
                        (axis, state, status))
        return state, status

    def PreReadOne(self, axis):
        self._log.debug("PreReadOne(%d): Entering...", axis)
        self.sd[axis] = 0

    def ReadAll(self):
        if self._synchronization == AcqSynch.HardwareTrigger:
            self._log.debug("ReadAll: Synchronization=HardwareTrigger")
            for axis in self.dataBuff.keys():
                if axis == 1:
                    continue
                queue = self.dataBuff[axis]['queue']
                value = self.dataBuff[axis]['value']
                while not queue.empty():
                    value += queue.get()

            follow_chn = self.dataBuff[1]['follow_chn']
            len_follow = len(self.dataBuff[follow_chn]['value'])
            self.dataBuff[1]['value'] = [self.intTime] * len_follow

    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        state = self.getDeviceState()
        if self._synchronization == AcqSynch.SoftwareTrigger:
            if state == PyTango.DevState.ON:
                if axis == 1:
                    return self.intTime
                self._log.debug("ReadOne(%d): Synchronization=SoftwareTrigger",
                                axis)
                mean = self.AIDevice["C0%s_MeanLast" % (axis - 2)].value
                std = self.AIDevice["C0%s_StdDevLast" % (axis - 2)].value
                self.sd[axis] = std
                value = mean
                mean = eval(self.formulas[axis])
                return_value = SardanaValue(mean)
                self._log.debug("ReadOne(%d): mean=%f, sd=%f",
                                axis, mean, std)
            else:
                self._log.error("ReadOne(%d): wrong state (%r) after"\
                    "acquisition" % (axis, state))
                raise Exception("Acquisition did not finish correctly.")

        elif self._synchronization == AcqSynch.HardwareTrigger:
            self._log.debug("ReadOne(%d): Synchronization=HardwareTrigger",
                            axis)
            return_value = self.dataBuff[axis]['value']
            if len(return_value) > 0:
                self.dataBuff[axis]['counter'] += len(return_value)
                self.dataBuff[axis]['value'] = []
            if self.dataBuff[axis]['counter'] == self._repetitions:
                self.unsubscribeEvent(axis)
        else:
            raise Exception("Unknown synchronization mode.")
        self._log.debug("ReadOne(%d): values=%r" % (axis, return_value))
        return return_value

    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        state = self.getDeviceState()
        if state != PyTango.DevState.STANDBY:
            self.AIDevice.stop()
        if self._synchronization == AcqSynch.HardwareTrigger:
            self.unsubscribeEvent(axis)

    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        for axis in self.dataBuff.keys():
            self.dataBuff[axis]['counter'] = 0
            self.dataBuff[axis]['value'] = []
            if axis != 1:
                self.dataBuff[axis]['queue'].__init__()
        self.axesToStart = []
        try:
            state = self.getDeviceState()
            if state != PyTango.DevState.STANDBY:
                self.AIDevice.stop()
        except Exception, e:
            self._log.error("PreStartAllCT(): Could not ask about state of "
                            "the device: %s and/or stop it.\nException: %s",
                            self.AdlinkAIDeviceName, e)
            raise

    def PreStartOneCT(self, axis):
        """
        Here we are counting which axes are going to be start, so later we
        can distinguish if we are starting only the master channel.
        """
        self._log.debug("PreStartOneCT(%d): Entering...", axis)
        if self._synchronization == AcqSynch.HardwareTrigger:
            if axis != 1:
                self.dataBuff[1]['follow_chn'] = axis
                attr_name = 'C0%s_MeanValues' % (axis - 2)
                cb = ListenerDataReady(self.dataBuff[axis]['queue'],
                                       log=self._log)

                event_type = PyTango.EventType.DATA_READY_EVENT
                dev = self.AIDevice
                try:
                    id = dev.subscribe_event(attr_name, event_type, cb)
                    self.dataBuff[axis]['id'] = id
                    self._log.debug('Subscribe event axis: %d' % axis)
                except Exception, e:
                    self._log.debug('Event subscription error: %s' % e)
                    raise
        return True

    def StartAllCT(self):
        """
        Starting the acquisition is done only if before was called
        PreStartOneCT for master channel.
        """
        self._log.debug("StartAllCT(): Entering...")
        # AdlinkAI Tango device has two aleatory bugs:
        # * Start command changes state to ON without passing throug RUNNING
        # * Start command changes state to RUNNING after a while
        # For these reasons we either wait or retry 3 times the Start command.
        for i in range(1, 4):
            self._log.debug(
                'StartAllCT: trying to start for the %d time' % i)
            state = self.AIDevice.state()
            self._log.debug('StartAllCT: AIDevice state before start is %s'
                        % repr(state))
            self.AIDevice.start()
            state = self.AIDevice.state()
            self._log.debug('StartAllCT: AIDevice state after start '
                            'is %s' % repr(state))
            if state == PyTango.DevState.RUNNING:
                break
            time.sleep(0.05)
            state = self.AIDevice.state()
            self._log.debug('StartAllCT: AIDevice state after wait '
                            'is %s' % repr(state))
            if state == PyTango.DevState.RUNNING:
                break
            self._log.debug('StartAllCT: stopping AIDevice')
            self.AIDevice.stop()
        else:
            raise Exception('Could not start acquisition')

    def PreLoadOne(self, axis, value):
        """
        Here we are keeping a reference to the master channel, so  later in
        StartAll() we can distinguish if we are starting only the master
        channel.
        """
        self._log.debug("PreLoadOne(%d, %f): Entering...", axis, value)
        return True

    def LoadOne(self, axis, value, repetitions):
        self._log.debug("LoadOne(%d, %f): Entering...", axis, value)
        self.intTime = value
        try:
            self.state = self.AIDevice.state()
            if self.state != PyTango.DevState.STANDBY:
                self._log.debug('LoadOne(%d): state = %s' %
                                (axis, repr(self.state)))
                # Randomly device may take more than 3 seconds to stop.
                # The probability raises when acquisitions are done frequently
                # step scan, frequent executions of ct, etc.
                # Temporarily set a higher timeout.
                self.AIDevice.set_timeout_millis(10000)
                self.AIDevice.stop()
                self.AIDevice.set_timeout_millis(3000)
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not ask about state of "
                            "the device: %s and/or stop it.\nException: %s",
                            axis, value, self.AdlinkAIDeviceName, e)
            raise
        self._repetitions = repetitions
        self.AIDevice["NumOfTriggers"] = repetitions
        sampRate = self.AIDevice['SampleRate'].value
        chnSampPerTrigger = int(self.intTime * sampRate)
        if self._synchronization == AcqSynch.SoftwareTrigger:
            self._log.debug("SetCtrlPar(): setting synchronization "
                            "to SoftwareTrigger")
            source = "SOFT"
        elif self._synchronization == AcqSynch.HardwareTrigger:
            self._log.debug("SetCtrlPar(): setting synchronization "
                            "to HardwareTrigger")
            source = "ExtD:+"
        else:
            raise Exception("Adlink daq2005 allows only Software or "
                            "Trigger triggering")

        self.AIDevice["TriggerInfinite"] = 0
        self.AIDevice["TriggerSources"] = source

        try:
            if self._synchronization == AcqSynch.SoftwareTrigger:
                self.AIDevice['NumOfTriggers'] = 1
            elif self._synchronization == AcqSynch.HardwareTrigger:
                if axis == 1:
                    self.AIDevice.ClearBuffer()
            else:
                raise Exception('Unknown synchronization mode.')
            self.AIDevice['TriggerInfinite'] = 0
            self.AIDevice['ChannelSamplesPerTrigger'] = chnSampPerTrigger
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not configure device: "
                            "%s.\nException: %s", self.AdlinkAIDeviceName, e)
            raise
        self._log.debug("LoadOne(%d, %f): Finished...", axis, value)

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar(%d, %s): Entering...", axis, name)
        if name.lower() == "sd":
            return self.sd[axis]
        if name.lower() == "formula":
            return self.formulas[axis]
        if name.lower() == "sharedformula":
            return self.sharedFormula[axis]

    def SetAxisExtraPar(self, axis, name, value):
        state = self.getDeviceState()
        if state != PyTango.DevState.STANDBY:
            self.AIDevice.stop()

        # self.set_extra_attribute_par(axis, name, value) #todo Ask to zibi
        # what is this!!
        if name.lower() == "formula":
            self.formulas[axis] = value

        if name.lower() == "sharedformula":
            self.sharedFormula[axis] = value
            if value:
                for i in self.formulas:
                    self.formulas[i] = self.formulas[axis]


