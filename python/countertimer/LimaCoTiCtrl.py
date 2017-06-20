#!/usr/bin/env python

import os
import PyTango
from sardana import State
from sardana.pool.controller import CounterTimerController, Type, \
    Description, Access, DataAccess, Memorize, NotMemorized, MaxDimSize, \
    Memorized, DefaultValue


class LimaCoTiCtrl(CounterTimerController):
    """This class is a Tango Sardana Counter Timer Controller for any
    Lima Device. This controller is used as an alternative to current
    2D controller. It has a single (master) axis which it provides the
    image name as a value of an experimental channel in a measurement group.
    The returned value is a string, which has been defined bby overwriting
    the current axis attribute Value but as a string.
    This controller avoids passing the image which was known to slow the
    acquisition process ans can be used as a workaround before the full
    integration of the 2D Sardana controller."""

    gender = "LimaCounterTimerController"
    model = "Basic"
    organization = "CELLS - ALBA"
    image = "Lima_ctrl.png"
    logo = "ALBA_logo.png"

    MaxDevice = 1

    class_prop = {}
    ctrl_attributes = {
        'Filename': {
            Type: str,
            Description: 'Full file name: path/filname. The extension is '
                         'defined on SavingFormat attribute',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
        'LastImageName': {
            Type: str,
            Description: 'Last images saved full file name',
            Access: DataAccess.ReadOnly,
            Memorize: NotMemorized},
        'DetectorName': {
            Type: str,
            Description: 'The full name saved: filename_DetectorName.format',
            Access: DataAccess.ReadWrite,
            Memorize: Memorized},
        'SavingFormat': {
            Type: str,
            Description: 'Saving format',
            Access: DataAccess.ReadWrite,
            Memorize: Memorized},
        'ExpectedSavingImages': {
            Type: int,
            Description: 'Expected Images to Save using Lima',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized,
            DefaultValue: 0},
        }

    axis_attributes = {
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

    ctrl_properties = {
        'LimaCCDDeviceName': {Type: str, Description: 'Detector device name'},
        'SoftwareSync': {Type: str,
                         Description: 'acq_trigger_mode for software mode'},
        'HardwareSync': {Type: str,
                         Description: 'acq_trigger_mode for hardware mode'},
        }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst),
                        repr(props))

        try:
            self._limacdd = PyTango.DeviceProxy(self.LimaCCDDeviceName)
            self._limacdd.reset()
        except PyTango.DevFailed as e:
            raise RuntimeError('__init__(): Could not create a device proxy '
                               'from following device name: %s.\nException: '
                               '%s ' % (self.LimaCCDDeviceName, e))
        self._data_buff = {}
        self._hw_state = None
        self._last_image_read = -1
        self._repetitions = 0
        self._ext_trigger = False
        self._state = None
        self._status = None
        self._new_data = False
        self._int_time = 0
        self._latency_time = 0
        self._trigger_mode = None
        self._expectedsavingimages = 0
        self._software_trigger = self.SoftwareSync
        self._hardware_trigger = self.HardwareSync
        self._saving_format = ''
        self._filename = ''
        self._det_name = ''
        # Attributes for the continuous scan sadana 2.2.2
        self._sampling_frequency = 1
        self._no_of_triggers = 1
        self._acquisition_time = 1

    def _clean_acquisition(self):
        if self._last_image_read != -1:
            self._last_image_read = -1
            self._repetitions = 0
            self._trigger_mode = self._software_trigger
            self._new_data = False
            if self._expectedsavingimages == 0:
                self._filename = ''


    def _prepare_saving(self):
        if len(self._filename) > 0:
            path, fname = os.path.split(self._filename)
            prefix, _ = os.path.splitext(fname)
            prefix += '_%s_' % self._det_name
            suffix = self._saving_format.lower()
            frame_per_file = 1
            if self._saving_format == 'HDF5':
                suffix = 'h5'
                frame_per_file = self._repetitions

            self._limacdd.write_attribute('saving_frame_per_file',
                                          frame_per_file)
            self._limacdd.write_attribute('saving_format', self._saving_format)
            self._limacdd.write_attribute('saving_directory', path)
            self._limacdd.write_attribute('saving_mode', 'Auto_Frame')
            self._limacdd.write_attribute('saving_prefix', prefix)
            self._limacdd.write_attribute('saving_suffix', '.' + suffix)
        else:
            self._limacdd.write_attribute('saving_mode', 'Manual')

    def AddDevice(self, axis):
        if axis != 1:
            raise ValueError('This controller only have the axis 1')
        self._data_buff[1] = []

    def DeleteDevice(self, axis):
        self._data_buff.pop(axis)

    def StateAll(self):
        self._hw_state = self._limacdd.read_attribute('acq_status').value
        if self._hw_state == 'Running':
            self._state = State.Moving
            self._status = 'The LimaCCD is acquiring'

        elif self._hw_state == 'Ready':
            if self._last_image_read != (self._repetitions - 1) and \
                    self._ext_trigger:
                self._log.warning('The LimaCCDs finished but the ctrl did not '
                                  'read all the data yet. Last image read %r'
                                  % self._last_image_read)
                self._state = State.Moving
                self._status = 'The LimaCCD is acquiring'
            else:
                self._clean_acquisition()
                self._state = State.On
                self._status = 'The LimaCCD is ready to acquire'

        else:
            self._state = State.Fault
            self._status = 'The LimaCCD state is: %s' % self._hw_state

    def StateOne(self, axis):
        #self._log.debug('StateOne(%r): %r' %(axis,self._state))

        return self._state, self._status

    def LoadOne(self, axis, value, repetitions=None):
        if axis != 1:
            raise RuntimeError('The master channel should be the axis 1')

        self._int_time = value
        if repetitions is None:
            self._repetitions = 1
            self._trigger_mode = self._software_trigger
        else:
            self._repetitions = repetitions
            self._trigger_mode = self._hardware_trigger

        self._prepare_saving()
        self._limacdd.write_attribute('acq_expo_time', self._int_time)
        self._limacdd.write_attribute('acq_nb_frames', self._repetitions)
        self._limacdd.write_attribute('latency_time', self._latency_time)
        self._limacdd.write_attribute('acq_trigger_mode', self._trigger_mode)

    def PreStartAll(self):
        self._limacdd.prepareAcq()
        return True

    def StartAll(self):
      
        self._limacdd.startAcq()
        if self._expectedsavingimages > 0:
            if self._trigger_mode == self._software_trigger:              
                self._expectedsavingimages -= 1
            else:
                self._expectedsavingimages = 0
          

    def ReadAll(self):
        new_image_ready = 0
        self._new_data = True
        if self._trigger_mode == self._software_trigger:
            if self._hw_state != 'Ready':
                self._new_data = False
                return
            self._data_buff[1] = [self._int_time]
          
        else:
            attr = 'last_image_ready'
            new_image_ready = self._limacdd(attr).value
            if new_image_ready == self._last_image_read:
                self._new_data = False
                return
            self._last_image_read += 1
            new_data = (new_image_ready - self._last_image_read) + 1
            if new_image_ready == 0:
                new_data = 1
            self._data_buff[1] = [self._int_time] * new_data
        self._last_image_read = new_image_ready
        self._log.debug('Leaving ReadAll %r' %self._data_buff[1])

    def ReadOne(self, axis):
        self._log.debug('Entering in  ReadOn')
        self._log.debug(self._trigger_mode)
        self._log.debug(self._new_data)
        if self._trigger_mode == self._software_trigger:
            if not self._new_data:
                raise Exception('Acquisition did not finish correctly. LimaCCD '
                                'State %r' % self._hw_state)  
            return self._data_buff[axis][0]
        else:
            if not self._new_data:
                return []
            else:
                return self._data_buff[axis]


    def AbortOne(self, axis):
        self.StateAll()
        self._expectedsavingimages = 0
        if self._hw_state != 'Ready':
            self._limacdd.stopAcq()
            self._clean_acquisition()

################################################################################
#                Controller Extra Attribute Methods
################################################################################
    def SetCtrlPar(self, parameter, value):
        param = parameter.lower()
        if param == 'filename':
            self._filename = value
        elif param == 'detectorname':
            self._det_name = value
        elif param == 'savingformat':
            self._saving_format = value
        else:
            super(LimaCoTiCtrl, self).SetCtrlPar(parameter, value)

    def GetCtrlPar(self, parameter):
        param = parameter.lower()
        if param == 'filename':
            value = self._filename
        elif param == 'lastimagename':
            path = self._limacdd.read_attribute('saving_directory').value
            prefix = self._limacdd.read_attribute('saving_prefix').value
            suffix = self._limacdd.read_attribute('saving_suffix').value
            nr = self._limacdd.read_attribute('saving_next_number').value - 1
            index_format =  self._limacdd.read_attribute('saving_index_format').value            
            nr_formated = index_format % nr
            value = '%s/%s%s%s' % (path, prefix, nr_formated, suffix)
        elif param == 'detectorname':
            value = self._det_name
        elif param == 'savingformat':
            value = self._saving_format
        else:
            value = super(LimaCoTiCtrl, self).GetCtrlPar(parameter)
        return value

################################################################################
#                Code needed for sardana 2.2.2
################################################################################
    def SetAxisExtraPar(self, axis, name, value):
        name = name.lower()
        if name == 'samplingfrequency':
            self._sampling_frequency = value
        elif name == 'triggermode':
            if value == 'soft':
                self._trigger_mode = self._software_trigger
            elif value == 'gate':
                self._trigger_mode = self._hardware_trigger
        elif name == 'nroftriggers':
            self._no_of_triggers = value
        elif name == 'acquisitiontime':
            self._acquisition_time = value
        elif name == 'ExpectedSavingImages':            
            self._expectedsavingimages = value
            
    def GetAxisExtraPar(self, axis, name):
        name = name.lower()
        result = None
        if name == 'samplingfrequency':
            result = self._sampling_frequency
        elif name == 'triggermode':
            if self._trigger_mode == self._software_trigger:
                result = 'soft'
            else:
                result = 'gate'
        elif name == 'nroftriggers':
            result = self._no_of_triggers
        elif name == 'acquisitiontime':
            result = self._acquisition_time
        elif name.lower() == 'data':
            self.ReadAll()
            result = self.ReadOne(axis)
        elif name == 'expectedSavingImages':            
            result = self._expectedsavingimages
        return result

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
                if axis == 1:
                    self.LoadOne(1, self._acquisition_time,
                                 self._no_of_triggers)
                    self.PreStartAll()
                    ret = 'Prestart did it'
                else:
                    ret = 'Only axis 1 can prepare the DS'
            elif action == 'start':
                self._log.debug('SendToCtrl(%s): starting channel %d' %
                                (cmd, axis))
                if axis == 1:
                    self.StartAll()
                    ret = 'Acquisition started'
                else:
                    ret = 'Only axis 1 can start the DS'
            elif action == 'pre-stop':
                self._log.debug('SendToCtrl(%s): pre-stopping channel %d' %
                                (cmd, axis))
                ret = 'No implemented'
            elif action == 'stop':
                self._log.debug('SendToCtrl(%s): stopping channel %d' %
                                (cmd, axis))
                if axis == 1:
                    self.AbortOne(1)
                    ret = "Acquisition stopped"
                else:
                    ret = 'Only axis 1 can stop the DS'
        return ret
