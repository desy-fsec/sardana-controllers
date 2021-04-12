from sardana.pool import AcqSynch
from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController, Description, \
    Access, Type, Memorize, NotMemorized
from taurus import Device
import PyTango
import numpy as np

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


class MythenROICounterController(CounterTimerController):
    """
    """

    gender = ""
    model = "Basic"
    organization = "Sardana team"
    MaxDevice = 128

    class_prop = {
        'MythenDCS': {Description: 'Device Server',
                      Type: str},
    }

    axis_attributes = {
        'ROILow': {
            Type: int,
            Description: 'Set low value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'ROIHigh': {
            Type: int,
            Description: 'Set high value of the ROI.',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},

    }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.mythen = Device(self.MythenDCS)

        self._repetitions = 0
        self._last_frame_readed = {}
        self._flg_abort = False
        self._rois = []
        self._debug = False

    @debug
    def AddDevice(self, axis):
        self._rois.append(axis)
        self._last_frame_readed[axis] = 0

    @debug
    def DeleteDevice(self, axis):
        self._rois.remove(axis)

    @debug
    def StateAll(self):
        mythen_state = self.mythen.state()
        self.status = self.mythen.status()

        if mythen_state == DEV_STATE_RUNNING:
            self.state = State.Running
        elif mythen_state == DEV_STATE_ON:
            self.state = State.On
        elif mythen_state == DEV_STATE_INIT:
            self.state = State.Init
        else:
            self.state = State.Fault

    @debug
    def StateOne(self, axis):
        # self._log.debug('Status(%d): %s State %s' % (axis, self.status,
        #                                              self.state))
        return self.state, self.status

    @debug
    def ReadOne(self, axis):
        try:
            new_data = []
            frames_readies = self.mythen.FramesReadies

            if frames_readies > self._last_frame_readed[axis]:
                attr = 'ROI{0}Buffer'.format(axis)
                data = self.mythen.read_attribute(attr).value
                new_data = data[self._last_frame_readed[axis]:].tolist()
                if self._repetitions > 1:
                    self._last_frame_readed[axis] = len(data)

            if len(new_data) == 0:
                return None
            if self._synchronization in SOFTWARE:
                result = new_data[0]
            elif self._synchronization in HARDWARE:
                result = new_data
        except Exception as e:
            pass

        return result

    @debug
    def StartAll(self):
        pass

    def StartOne(self, axis, value=None):
        self._last_frame_readed[axis] = 0

    @debug
    def LoadOne(self, axis, value, repetitions):
        self._repetitions = repetitions

    @debug
    def AbortOne(self, axis):
        pass

    ###########################################################################
    #                Controller Extra Attribute Methods
    ###########################################################################
    @debug
    def getROILow(self, axis):
        attr = 'ROI{}Low'.format(int(axis))
        result = self.mythen.read_attribute(attr).value
        return result

    @debug
    def setROILow(self, axis, value):
        attr = 'ROI{}Low'.format(int(axis))
        self.mythen.write_attribute(attr, value)

    @debug
    def getROIHigh(self, axis):
        attr = 'ROI{}High'.format(int(axis))
        result = self.mythen.read_attribute(attr).value
        return result

    @debug
    def setROIHigh(self, axis, value):
        attr = 'ROI{}High'.format(int(axis))
        self.mythen.write_attribute(attr, value)

