from sardana import State, DataAccess
from sardana.pool.controller import OneDController, Description, Access, \
    Type, Memorize, NotMemorized, MaxDimSize
from taurus import Device, Attribute
import PyTango
import Queue
import numpy as np
from math import sqrt, cos, sin, pi
import time

DEV_STATE_UNKNOWN = PyTango.DevState.UNKNOWN
DEV_STATE_FAULT = PyTango.DevState.FAULT
DEV_STATE_RUNNING = PyTango.DevState.RUNNING
DEV_STATE_ON = PyTango.DevState.ON
DEV_STATE_INIT = PyTango.DevState.INIT
CHANGE_EVENT = PyTango.EventType.CHANGE_EVENT

def debug(func):
    def new_fun(*args,**kwargs):
        klass = args[0]
        klass._log.debug('Entering to: %s(%s)' % (func.func_name, repr(args)))
        result = func(*args,**kwargs)
        klass._log.debug('Leaving the function: %s .....' % func.func_name)
        return result
    return new_fun

CHN_RAW = 1
CHN_NORM = 2
CHN_ENERGY_THEO = 3
CHN_ENERGY_EXP = 4


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
            raise 'Error with the event.'


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
    # TODO Implement the axis 3 and 4
    MaxDevice = 4

    class_prop = {
        'MythenDCS': {'Description': 'Device Server',
                      'Type': 'PyTango.DevString'},
        'ClearBragg': {'Description': 'Motor name',
                       'Type': 'PyTango.DevString'},
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

    axis_attributes ={
        "NrOfTriggers":
                    {Type : long,
                     Description : 'Nr of triggers',
                     Access : DataAccess.ReadWrite,
                     Memorize : NotMemorized
                    },

        "SamplingFrequency":
           {Type : float,
            Description : 'Sampling frequency',
            Access : DataAccess.ReadWrite,
            Memorize : NotMemorized},
        "AcquisitionTime":
           {Type : float,
            Description : 'Acquisition time per trigger',
            Access : DataAccess.ReadWrite,
            Memorize : NotMemorized
           },
        "TriggerMode":
           {Type : str,
            Description : 'Trigger mode: soft or gate',
            Access : DataAccess.ReadWrite,
            Memorize : NotMemorized
           },
        "Data":
           {Type: [[float]],
            Description : 'Data buffer',
            Access : DataAccess.ReadOnly,
            MaxDimSize : (1280, 1000000)
           }
    }

    def __init__(self, inst, props, *args, **kwargs):
        super(MythenController, self).__init__(inst, props, *args, **kwargs)
        self.flg_read_hw = False
        self.flg_postprocessing = False
        self.axes = {}
        self.mythen = Device(self.MythenDCS)
        self.raw_queue = Queue.Queue()
        self.ext_trigger = False
        self.nr_trigger = None
        self.raw_listener = ListenerChangeEvent(self.raw_queue, self.mythen,
                                                self._log)
        self.listener_id = self.mythen.subscribe_event('RawData',
                                                       CHANGE_EVENT,
                                                       self.raw_listener)

        for i in range(1, self.MaxDevice+1):
            self.axes[i] = {'Active': False, 'Data': None}
       
    @debug
    def AddDevice(self, axis):
        if axis > self.MaxDevice:
            raise ValueError('This controller can support: %s ' %
                             self.MaxDevice)
        self.axes[axis]['Active'] = True

    @debug
    def DeleteDevice(self, axis):
        self.axes[axis]['Active'] = False

    @debug
    def StateAll(self):
        mythen_state = self.mythen.state()
        self.status = self.mythen.status()

        if self.ext_trigger:
            frames_readies = self.mythen.read_attribute('FramesReadies').value
            if frames_readies < self.nr_trigger:
                self.state = State.Running
                return

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
        return self.state, self.status

    @debug
    def ReadOne(self, axis):
        # Read the raw data from the detector
        if not self.flg_read_hw:
            # TODO implement the calculation of the mean with more frames.
            self.axes[CHN_RAW]['Data'] = np.array(self.raw_queue.get())
            self.flg_read_hw = True
        if axis != CHN_RAW and not self.flg_postprocessing:
            self.postProcessing()
            self.flg_postprocessing = True
        return self.axes[axis]['Data']
    
    @debug
    def StartOne(self, axis, value):
        if axis == CHN_RAW:
            self.flg_read_hw = False
            self.flg_postprocessing = False
            # Clear the Queue before to start the new acquisition.
            with self.raw_queue.mutex:
                self.raw_queue.queue.clear()

            self.mythen.start()

    @debug
    def LoadOne(self, axis, value):
        self.state = self.mythen.state()
        live_mode = self.mythen.read_attribute('LiveMode').value
        if self.state == State.Running:
            self.mythen.stop()

        if live_mode:
            self._log.warning('The live move is active!!!. We will turn off '
                              'it.')
            self.mythen.write_attribute('LiveMode', False)

        if value > 0:
            self.mythen.write_attribute('Frames', 1)
            self.mythen.write_attribute('IntTime', value)
        else:
            raise Exception('The monitor mode does not implement yet.')

    @debug
    def AbortOne(self, axis):
        self.mythen.stop()
        for i in range(1, self.MaxDevice+1):
            self.axes[i]['Data'] = None


################################################################################
#                Axis Extra Attribute Methods
################################################################################
    @debug
    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar(%d, %s): Entering...", axis, name)
        name = name.lower()
        if name == "samplingfrequency":
            return float("nan")
        if name == "triggermode":
            trigger = self.mythen.read_attribute('TriggerMode').value
            if trigger:
                return "gate"
            else:
                return "soft"
        if name == "nroftriggers":
            nrOfTriggers = self.mythen.read_attribute('Frames').value
            return long(nrOfTriggers)
        if name == "acquisitiontime":
            acqTime = self.mythen.read_attribute('IntTime').value
            return acqTime
        if name.lower() == "data":
            rep = 0
            while True:
                self._log.debug('Waiting to extract data on mythen '
                                    'Repetition: %r' % rep)
                rep += 1
                time.sleep(0.01)
                frames = self.mythen.read_attribute('FramesReadies').value
                if frames >= self.nr_trigger:
                    break

            self.mythen.set_timeout_millis(30000)
            value = self.mythen.read_attribute('ImageData').value
            self.mythen.set_timeout_millis(3000)
            return value

    @debug
    def SetAxisExtraPar(self, axis, name, value):
        name = name.lower()
        #attributes used for continuous acquisition
        if name in ["samplingfrequency", "triggermode", "nroftriggers",
                      "acquisitiontime"]:
            # stopping Tango device, otherwise configuration won't be
            # possible
            if axis != 1:
                raise ValueError('The continuous scan is supported only by '
                                 'the first channel (raw data)')
            try:
                state = self.mythen.state()
                if state in [PyTango.DevState.RUNNING, PyTango.DevState.ON]:
                    self.mythen.stop()
            except PyTango.DevFailed, e:
                raise e
            if name == "samplingfrequency":
                pass
            elif name == "triggermode":
                if value == "soft":
                    self.ext_trigger = False
                if value == "gate":
                    self.ext_trigger = True

                self.mythen.write_attribute('TriggerMode', self.ext_trigger)
                self.mythen.write_attribute('ContinuousTrigger',
                                            self.ext_trigger)

            elif name == "nroftriggers":
                self.nr_trigger = value
                self.mythen.write_attribute('Frames', value)
            elif name == "acquisitiontime":
                self.mythen.write_attribute('IntTime', value)



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

    def SendToCtrl(self, cmd):
        cmd = cmd.lower()
        words = cmd.split(" ")
        ret = "Unknown command"
        if len(words) == 2:
            action = words[0]
            axis = int(words[1])
            if action == "pre-start":
                self._log.debug("SendToCtrl(%s): pre-starting channel %d", cmd, axis)
                ret = "Channel %d appended to contAcqChannels" % axis
            elif action == "start":
                self._log.debug("SendToCtrl(%s): starting channel %d", cmd, axis)
                self.mythen.start()
                ret = "Acquisition started"
            elif action == "pre-stop":
                self._log.debug("SendToCtrl(%s): pre-stopping channel %d", cmd, axis)
                ret = "Channel %d appended to contAcqChannels" % axis
            elif action == "stop":
                self.mythen.stop()
                ret = "Acquisition stopped"
        return ret

################################################################################
#                Controller Post Processing Methods
################################################################################

    @debug
    def postProcessing(self):
        self._calcNorm()
        #self._calcEscale()
        #self._calcTscale()

    @debug
    def _calcNorm(self):
        data = self.axes[CHN_RAW]['Data']
        # Set bad channels to 0
        data[np.where(data == -2)] = 0
        int_time = self.mythen.read_attribute('IntTime').value
        self.axes[CHN_NORM]['Data'] = data/int_time

    @debug
    def _calcEscale(self):
        """
        Method to calculate the experimental energy scale
        A: scale_a
        E(p) = A*p + B
        :return:
        """
        pixels = np.array(range(0, 1280))
        e_scale = (self.scale_a * pixels) + self.scale_b
        print 'escale= ', e_scale
        self.axes[CHN_ENERGY_EXP]['Data'] = e_scale


    # @debug
    # def _calcTscale(self):
    #     """
    #     Method to calculate the theoretical energy scale.
    #     th: Clear bragg angle
    #     p: pixel
    #     p0: central pixel
    #     n: crystal order
    #     a: Lattice constant by materials
    #     hkl: Miller values
    #     R: 0.5 m Rowland circle
    #     hc: 1.23984193e-3 eV/m
    #     C(hkl) = (hc/2a)*n*sqrt(h^2 + k^2 + l^2)
    #     A = (C(hkl)/4R) * cos(th)/sin^3(th)
    #     B = C(hkl)/sin(th)
    #     E(th, p) = A(p0-p) + B
    #     :return:
    #     """
    #     R = 0.5
    #     hc = 1.23984193e-3
    #     pixels = np.array(range(1, 1281))
    #     h, k, l, a = get_hkla(self.crystal)
    #     C = ((hc/(2*a)) * self.n * sqrt(h**2 + k**2 + l**2))/(2*pi)
    #     cbragg = Device(self.ClearBragg)
    #     th = cbragg.read_attribute('Position').value
    #     A = (C/(4*R)) * (cos(th)/(sin(th)**3))
    #     B = C/sin(th)
    #     t_scale = A*(self.p0 - pixels) + B
    #     self.axes[CHN_ENERGY_THEO]['Data'] = t_scale

