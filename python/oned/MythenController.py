from sardana import State, DataAccess
from sardana.pool.controller import OneDController, Description, Access, \
    Type, Memorize, NotMemorized
from taurus import Device, Attribute
import PyTango
import Queue
import numpy as np
from crystal import get_hkla
from math import sqrt, cos, sin, pi

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
        'ScaleA': {
            Type: float,
            Description: 'A constant of experimental energy scale',
            Access: DataAccess.ReadWrite,
            Memorize: Memorize},
        'ScaleB': {
            Type: float,
            Description: 'B constant of experimental energy scale',
            Access: DataAccess.ReadWrite,
            Memorize: Memorize},
        'Crystal': {
            Type: str,
            Description: 'crystal used e.g: Si111',
            Access: DataAccess.ReadWrite,
            Memorize: Memorize},
        'CrystalN': {
            Type: int,
            Description: 'order of the crystal used on the energy scale',
            Access: DataAccess.ReadWrite,
            Memorize: Memorize},
        'CentralPixel': {
            Type: int,
            Description: 'central pixel used on the theoretical energy scale',
            Access: DataAccess.ReadWrite,
            Memorize: Memorize},


        }
    
    def __init__(self, inst, props, *args, **kwargs):
        super(MythenController, self).__init__(inst, props, *args, **kwargs)
        self.flg_read_hw = False
        self.flg_postprocessing = False
        self.axes = {}
        self.mythen = Device(self.MythenDCS)
        self.raw_queue = Queue.Queue()
        self.raw_listener = ListenerChangeEvent(self.raw_queue, self.mythen,
                                                self._log)
        self.listener_id = self.mythen.subscribe_event('RawData',
                                                       CHANGE_EVENT,
                                                       self.raw_listener)

        for i in range(1, self.MaxDevice+1):
            self.axes[i] = {'Active': False, 'Data': None}
       
        #TODO: Analize if it has problem with the memorize values
        self.scale_a = -0.07
        self.scale_b = 6427.0
        self.crystal = 'Si111'
        self.crystaln = 3.0
        self.p0 = 700
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
#                Controller Extra Attribute Methods
################################################################################
    @debug
    def SetCtrlPar(self, parameter, value):
        param_list = self.mythen.get_attribute_list()
        param_list = map(str.lower, param_list)
        param = parameter.lower()
        if param == 'scalea':
            self.scale_a = value
        elif param == 'scaleb':
            self.scale_b = value
        elif param == 'crystaln':
            self.n = value
        elif param == 'crystal':
            self.crystal = value
        elif param == 'centralpixel':
            self.p0 = value
        elif param in param_list:
            self.mythen.write_attribute(parameter, value)
        else:
            super(MythenController, self).SetCtrlPar(parameter, value)

    @debug
    def GetCtrlPar(self, parameter):
        param_list = self.mythen.get_attribute_list()
        param_list = map(str.lower, param_list)
        param = parameter.lower()
        if param == 'scalea':
            value = self.scale_a
        elif param == 'scaleb':
            value = self.scale_b
        elif param == 'crystaln':
            value = self.n
        elif param == 'crystal':
            value = self.crystal
        elif param == 'centralpixel':
            value = self.p0
        elif param in param_list:
            value = self.mythen.read_attribute(parameter).value
        else:
            value = super(MythenController, self).GetCtrlPar(parameter)
        return value


################################################################################
#                Controller Post Processing Methods
################################################################################

    @debug
    def postProcessing(self):
        self._calcNorm()
        self._calcEscale()
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


    @debug
    def _calcTscale(self):
        """
        Method to calculate the theoretical energy scale.
        th: Clear bragg angle
        p: pixel
        p0: central pixel
        n: crystal order
        a: Lattice constant by materials
        hkl: Miller values
        R: 0.5 m Rowland circle
        hc: 1.23984193e-3 eV/m
        C(hkl) = (hc/2a)*n*sqrt(h^2 + k^2 + l^2)
        A = (C(hkl)/4R) * cos(th)/sin^3(th)
        B = C(hkl)/sin(th)
        E(th, p) = A(p0-p) + B
        :return:
        """
        R = 0.5
        hc = 1.23984193e-3
        pixels = np.array(range(1, 1281))
        h, k, l, a = get_hkla(self.crystal)
        C = ((hc/(2*a)) * self.n * sqrt(h**2 + k**2 + l**2))/(2*pi)
        print 'holaaaaaaaaaaaa' +'\n'*4
        cbragg = Device(self.ClearBragg)
        th = cbragg.read_attribute('Position').value
        print 'holaaaaaaaaaaaa!!!!!!!!!!!!!1' +'\n'*4
        A = (C/(4*R)) * (cos(th)/(sin(th)**3))
        B = C/sin(th)
        t_scale = A*(self.p0 - pixels) + B
        self.axes[CHN_ENERGY_THEO]['Data'] = t_scale

