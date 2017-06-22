
import PyTango
from sardana import State
from sardana.pool.controller import Type, Access, Description, MaxDimSize, \
    Memorize, NotMemorized, Memorized, CounterTimerController, DataAccess

HW_TRIG = 'gate'
SW_TRIG = 'soft'


class LimaRoICounterCtrl(CounterTimerController):
    """
    This class is the Tango Sardana CounterTimer controller for getting the
    Lima RoIs as counters
    """

    gender = "LimaCounterTimer"
    model = "Basic"
    organization = "CELLS - ALBA"
    image = "Lima_ctrl.png"
    logo = "ALBA_logo.png"

    class_prop = {
        'LimaROIDeviceName': {Type: str, Description: 'Name of the roicounter '
                                                      'lima device'},
        'LimaROIBufferSize': {Type: long, Description: 'Circular buffer size '
                                                       'in image'}
    }

    axis_attributes = {
        'RoIx1': {Type: long,
                  Description: 'Start pixel X',
                  Access: DataAccess.ReadWrite,
                  Memorize: Memorized
                  },
        'RoIx2': {Type: long,
                  Description: 'End pixel X',
                  Access: DataAccess.ReadWrite,
                  Memorize: Memorized
                  },
        'RoIy1': {Type: long,
                  Description: 'Start pixel Y',
                  Access: DataAccess.ReadWrite,
                  Memorize: Memorized
                  },
        'RoIy2': {Type: long,
                  Description: 'End pixel Y',
                  Access: DataAccess.ReadWrite,
                  Memorize: Memorized
                  },
        # attributes added for continuous acquisition mode
        'NrOfTriggers': {Type: long,
                         Description: 'Nr of triggers',
                         Access: DataAccess.ReadWrite,
                         Memorize: NotMemorized},
        'SamplingFrequency': {Type: float,
                              Description: 'Sampling frequency',
                              Access: DataAccess.ReadWrite,
                              Memorize: NotMemorized},
        'AcquisitionTime': {Type: float,
                            Description: 'Acquisition time per trigger',
                            Access: DataAccess.ReadWrite,
                            Memorize: NotMemorized},
        'TriggerMode': {Type: str,
                        Description: 'Trigger mode: soft or gate',
                        Access: DataAccess.ReadWrite,
                        Memorize: NotMemorized},
        'Data': {Type: [float],
                 Description: 'Data buffer',
                 Access: DataAccess.ReadOnly,
                 MaxDimSize: (1000000,)},
    }

    # The command readCounters returns roi_id,frame number,sum,average,std,
    # min,max,...
    IDX_ROI_NR = 0
    IDX_IMAGE_NR = 1
    IDX_SUM = 2
    IDX_AVERAGE = 3
    IDX_STD_DESVIATION = 4
    IDX_MIN_PIXEL = 5
    IDX_MAX_PIXEL = 6

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst),
                        repr(props))

        try:
            self._limaroi = PyTango.DeviceProxy(self.LimaROIDeviceName)
        except PyTango.DevFailed as e:
            raise RuntimeError('__init__(): Could not create a device proxy '
                               'from following device name: %s.\nException: '
                               '%s ' % (self.LimaROIDeviceName, e))
        self._limaroi.Stop()
        self._limaroi.Start()
        self._limaroi.write_attribute('BufferSize', self.LimaROIBufferSize)
        self._rois = {}
        self._data_buff = {}
        self._state = None
        self._status = None
        self._sampling_frequency = None
        self._trigger_mode = None
        self._no_of_triggers = None
        self._acquisition_time = None
        self._start_ct = False
        self._repetitions = 0
        self._last_image_read = -1
        self._last_image_ready = -1

    def _clean_acquisition(self):
        if self._last_image_read != -1:
            self._last_image_read = -1
            self._last_image_ready = -1
            self._repetitions = 0
            self._trigger_mode = SW_TRIG
            self._start_ct = False

    def AddDevice(self, axis):
        name = ["roi" + str(axis)]
        self._rois[axis] = {}
        self._rois[axis]['name'] = 'roi_%d' % axis
        roi_id = self._limaroi.addNames(name)[0]
        self._rois[axis]['id'] = roi_id
        roi = [roi_id, 0, 0, 1, 1]
        self._limaroi.setRois(roi)
        self._data_buff[axis] = []

    def DeleteDevice(self, axis):
        roi_name = self._rois[axis]['name']
        self._limaroi.removeRois(roi_name)
        self._data_buff.pop(axis)
        self._rois.pop(axis)

    def StateAll(self):
        attr = 'CounterStatus'
        self._last_image_ready = self._limaroi.read_attribute(attr).value

        if self._last_image_read < (self._repetitions - 1):
            self._state = State.Moving
            self._status = 'Taking data'
        else:
            self._state = State.On
            self._clean_acquisition()
            if self._last_image_ready == -2:
                self._status = "Not images in buffer"
            else:
                self._status = "RoI computed"

    def StateOne(self, axis):
        return self._state, self._status

    def LoadOne(self, axis, value, repetitions=None):
        if repetitions is None:
            self._repetitions = 1
            self._trigger_mode = SW_TRIG
        else:
            self._repetitions = repetitions
            self._trigger_mode = HW_TRIG

    def ReadAll(self):
        if self._last_image_ready > self._last_image_read:
            for axis in self._data_buff.keys():
                self._data_buff[axis] = []
            self._last_image_read += 1
            rois_data = self._limaroi.readCounters(self._last_image_read)
            for base_idx in range(0, len(rois_data), 7):
                roi_nr_idx = base_idx + self.IDX_ROI_NR
                roi_nr = rois_data[roi_nr_idx]
                if roi_nr in self._data_buff:
                    sum_idx = base_idx + self.IDX_SUM
                    self._data_buff[roi_nr] += [rois_data[sum_idx]]
            self._last_image_read = self._last_image_ready

    def ReadOne(self, axis):
        if self._trigger_mode == SW_TRIG:
            if len(self._data_buff[axis]) == 0:
                raise Exception('Acquisition did not finish correctly.')
            value = self._data_buff[axis][0]
        else:
            value = self._data_buff[axis]
        return value

    def StartAllCT(self):
        state = self._limaroi.state()
        if state == PyTango.DevState.OFF:
            self._limaroi.start()

    def GetExtraAttributePar(self, axis, name):
        name = name.lower()
        result = None
        if 'roi' in name:
            roi = self._limaroi.getRois(self._rois[axis]['id'])
            if name == "roix1":
                result = roi[1]
            elif name == "roix2":
                result = roi[1] + roi[3]
            elif name == "roiy1":
                result = roi[2]
            elif name == "roiy2":
                result = roi[2] + roi[4]
        elif name == 'samplingfrequency':
            result = self._sampling_frequency
        elif name == 'triggermode':
            result = self._trigger_mode
        elif name == 'nroftriggers':
            result = self._no_of_triggers
        elif name == 'acquisitiontime':
            result = self._acquisition_time
        elif name.lower() == 'data':
            self.ReadAll()
            result = self.ReadOne(axis)
        return result

    def SetExtraAttributePar(self, axis, name, value):
        name = name.lower()
        if 'roi' in name:
            roi = self._limaroi.getRois(self._rois[axis]['id'])
            if name == "roix1":
                roi[1] = value
            elif name == "roix2":
                roi[3] = value - roi[1]
            elif name == "roiy1":
                roi[2] = value
            elif name == "roiy2":
                roi[4] = value - roi[2]
            self._limaroi.setRois(roi)
        elif name == 'samplingfrequency':
            self._sampling_frequency = value
        elif name == 'triggermode':
            self._trigger_mode = value
        elif name == 'nroftriggers':
            self._no_of_triggers = value
        elif name == 'acquisitiontime':
            self._acquisition_time = value

    def SendToCtrl(self, cmd):
        cmd = cmd.lower()
        words = cmd.split(' ')
        ret = 'Unknown command'
        if len(words) == 2:
            action = words[0]
            axis = int(words[1])
            if action == 'pre-start':
                self._log.debug('SendToCtrl(%s): pre-starting channel %d' %
                                (cmd, axis))
                if not self._start_ct:
                    self.LoadOne(axis, self._acquisition_time,
                                 self._no_of_triggers)

            elif action == 'start':
                self._log.debug('SendToCtrl(%s): starting channel %d' %
                                (cmd, axis))
                if not self._start_ct:
                    self.StartAll()
                    self._start_ct = True
                ret = 'Acquisition started'
            elif action == 'pre-stop':
                self._log.debug('SendToCtrl(%s): pre-stopping channel %d' %
                                (cmd, axis))
                ret = 'No implemented'
            elif action == 'stop':
                self._log.debug('SendToCtrl(%s): stopping channel %d' %
                                (cmd, axis))
                self._start_ct = False
                ret = 'No implemented'

        return ret
