from sardana.sardanavalue import SardanaValue
from sardana.pool import AcqSynch
from sardana import State, DataAccess
from sardana.pool.controller import OneDController, Description, Access, \
    Type, Memorize, NotMemorized, MaxDimSize
from taurus import Device, Attribute
import PyTango
import Queue
import numpy as np

import time

DEV_STATE_UNKNOWN = PyTango.DevState.UNKNOWN
DEV_STATE_FAULT = PyTango.DevState.FAULT
DEV_STATE_RUNNING = PyTango.DevState.RUNNING
DEV_STATE_ON = PyTango.DevState.ON
DEV_STATE_INIT = PyTango.DevState.INIT
CHANGE_EVENT = PyTango.EventType.CHANGE_EVENT
SOFTWARE = [AcqSynch.SoftwareTrigger, AcqSynch.SoftwareGate]
HARDWARE = [AcqSynch.HardwareTrigger, AcqSynch.HardwareGate]


def debug(func):
    def new_fun(*args, **kwargs):
        klass = args[0]
        if klass._debug:
            klass._log.debug('Entering to: %s(%s)' % (func.func_name,
                                                      repr(args)))
        result = func(*args,**kwargs)
        if klass._debug:
            klass._log.debug('Leaving the function: %s .....' % func.func_name)
        return result
    return new_fun

CHN_RAW = 1
# TODO include the other calculated channel and implement a ctrl for the ROIs.
# CHN_NORM = 2


class ListenerChangeEvent(object):
    def __init__(self, queue, mythen, log=None):
        self.queue = queue
        self.mythen = mythen
        self.log = log

    def push_event(self, event):
        if self.log:
            self.log.debug('Listener DataChangeEvent recevied')

        live_mode = self.mythen.read_attribute('LiveMode').value
        if live_mode:
            self.log.debug('Listener DataChangeEvent acquisition is not '
                           'running.')
            return

        if not event.err:
            new_data = event.attr_value.value
            # There are problem with the numpy array when we extract it from
            # the queue it has another values.
            self.queue.put(new_data.tolist())
            self.log.debug('New data')

        else:
            self.log.debug('Listener DataReadyEvent error in event')
            raise Exception('Error with the event.')


class MythenController(OneDController):
    """ 
    This class is the Sardana One Dimension Controller for the Dectris Mythen
    Detector. 

    The controller export four axes:
    1) Raw data: Array with the values of channels.
    2) Normalized Data: Array with value of each channel divided by the
    integration time.
    3) Theoretical Energy Scale: Array with the theoretical energy value for
    each channel.
    4) Experimental Energy Scale: Array with the experimental energy value
    for each channel.


    """

    gender = ""
    model = "Basic"
    organization = "Sardana team"
    # TODO Implement the axis 2 and 4
    MaxDevice = 1

    class_prop = {
        'MythenDCS': {Description: 'Device Server',
                      Type: str},
        'ClearBragg': {Description: 'Motor name',
                       Type: 'PyTango.DevString'},
        'LatencyTime': {Description: 'Latency time of the controller',
                        Type: float}
    }

    ctrl_attributes = {
        'Threshold': {
            Type: float,
            Description: 'Threshold in keV.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ReadoutBits': {
            Type: int,
            Description: 'The number of bits to be read out.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'Frames': {
            Type: int,
            Description: 'Number of frames per each acquisition.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'Tau': {
            Type: float,
            Description: 'Tau value in seconds.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'FlatFieldCorrection': {
            Type: bool,
            Description: 'Active/Deactivate flat field correction.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ROI1Low': {
            Type: int,
            Description: 'Set low value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ROI1High': {
            Type: int,
            Description: 'Set high value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ROI2Low': {
            Type: int,
            Description: 'Set low value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ROI2High': {
            Type: int,
            Description: 'Set high value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ROI3Low': {
            Type: int,
            Description: 'Set low value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ROI3High': {
            Type: int,
            Description: 'Set high value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'RateCorrection': {
            Type: bool,
            Description: 'Active/Deactivate rate correction.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'Settings': {
            Type: str,
            Description: 'Read settings.',
            Access: DataAccess.ReadOnly,
            Memorize: NotMemorized},
        'SettingsMode': {
            Type: str,
            Description: 'Read/Write settings mode.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},

        }

    axis_attributes = {}

    def __init__(self, inst, props, *args, **kwargs):
        OneDController.__init__(self, inst, props, *args, **kwargs)
        self.mythen = Device(self.MythenDCS)
        self.raw_queue = Queue.Queue()
        self.ext_trigger = False
        
        self.raw_listener = ListenerChangeEvent(self.raw_queue, self.mythen,
                                                self._log)
        self.listener_id = self.mythen.subscribe_event('RawData',
                                                       CHANGE_EVENT,
                                                       self.raw_listener)
        self._latency_time = self.LatencyTime
        self.repetitions = 0
        self.flg_abort = False
        self._debug = False

    @debug
    def AddDevice(self, axis):
        if axis > self.MaxDevice:
            raise ValueError('This controller can support: %s ' %
                             self.MaxDevice)

    @debug
    def DeleteDevice(self, axis):
        pass

    @debug
    def StateAll(self):
        mythen_state = self.mythen.state()
        self.status = self.mythen.status()

        if self._synchronization in HARDWARE:
            frames_readies = self.mythen.read_attribute('FramesReadies').value
            if frames_readies < self.repetitions and not self.flg_abort:
                self.state = State.Running
            else:
                self.state = State.On
            
        elif mythen_state == DEV_STATE_RUNNING:
            self.state = State.Running
        elif mythen_state == DEV_STATE_ON:
            self.state = State.On
        elif mythen_state == DEV_STATE_INIT:
            self.state = State.Init
        else:
            self.state = State.Fault

    @debug
    def StateOne(self, axis):
        # self._log.debug('Status({}): {} State {}'.format(axis, self.status,
        #                                                  self.state))
        return self.state, self.status

    @debug
    def ReadOne(self, axis):
        # Read the raw data from the detector
        # TODO implement the calculation of the mean with more frames.
        data = []
        result = []
        while not self.raw_queue.empty():
            data.append(self.raw_queue.get(timeout=1))
        new_data = len(data)
        
        if self._synchronization in SOFTWARE and new_data:
            result = data[0]
        elif self._synchronization in HARDWARE and new_data:
            result = data
        
        return result

    @debug
    def StartOne(self, axis, value):
        self.flg_abort = False 
        if axis == CHN_RAW:
            with self.raw_queue.mutex:
                self.raw_queue.queue.clear()

            self.mythen.start()



    @debug
    def LoadOne(self, axis, value, repetitions, latency):
        self.state = self.mythen.state()
        live_mode = self.mythen.read_attribute('LiveMode').value
        if self.state == State.Running:
            self.mythen.stop()

        if live_mode:
            self._log.warning('The live move is active!!!. We will turn off '
                              'it.')
            self.mythen.write_attribute('LiveMode', False)

        self.repetitions = repetitions    

        self.mythen.write_attribute('IntTime', value)
        if self._synchronization in SOFTWARE:
            self._log.debug("SetCtrlPar(): setting synchronization "
                            "to SoftwareTrigger")
            self.ext_trigger = False
            repetitions = 1

        elif self._synchronization in HARDWARE:
            self._log.debug("SetCtrlPar(): setting synchronization "
                            "to HardwareTrigger")

            self.ext_trigger = True
        else:
            raise Exception("Mythen allows only Software or Hardware "
                            "triggering")

        self.mythen.write_attribute('Frames', repetitions)
        self.mythen.write_attribute('TriggerMode', self.ext_trigger)
        self.mythen.write_attribute('ContinuousTrigger', self.ext_trigger)
        # Activate trigger to use rising edge
        self.mythen.write_attribute('InputHigh', False)

    @debug
    def AbortOne(self, axis):
        self.mythen.stop()
        self.flg_abort = True

################################################################################
#                Controller Extra Attribute Methods
################################################################################
    @debug
    def SetCtrlPar(self, parameter, value):
        param_list = self.mythen.get_attribute_list()
        param_list = map(str.lower, param_list)
        param = parameter.lower()
        if param in param_list:
            self.mythen.write_attribute(parameter, value)
        else:
            super(MythenController, self).SetCtrlPar(parameter, value)

    @debug
    def GetCtrlPar(self, parameter):
        param_list = self.mythen.get_attribute_list()
        param_list = map(str.lower, param_list)
        param = parameter.lower()
        if param in param_list:
            value = self.mythen.read_attribute(parameter).value
        else:
            value = super(MythenController, self).GetCtrlPar(parameter)
        return value



