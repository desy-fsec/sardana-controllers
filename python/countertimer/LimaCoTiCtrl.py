#!/usr/bin/env python

import os
import PyTango
from sardana import State
from sardana.pool.controller import CounterTimerController, Type, \
    Description, Access, DataAccess, Memorize, NotMemorized, \
    Memorized, DefaultValue
from sardana.pool import AcqSynch
import time

# TODO: WIP version.

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
        'SavingFolderName': {
            Type: str,
            Description: 'The folder name to save the images SCANDIR + '
                         'SavingFolderName',
            Access: DataAccess.ReadWrite,
            Memorize: Memorized},
        }

    axis_attributes = {}

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
            self._limaccd = PyTango.DeviceProxy(self.LimaCCDDeviceName)
            self._limaccd.reset()
        except PyTango.DevFailed as e:
            raise RuntimeError('__init__(): Could not create a device proxy '
                               'from following device name: %s.\nException: '
                               '%s ' % (self.LimaCCDDeviceName, e))
        self._data_buff = {}
        self._hw_state = None
        self._last_image_read = -1
        self._repetitions = 0
        self._state = None
        self._status = None
        self._new_data = False
        self._int_time = 0
        self._latency_time = 0
        self._expected_saving_images = 0
        self._software_trigger = self.SoftwareSync
        self._hardware_trigger = self.HardwareSync
        self._saving_format = ''
        self._filename = ''
        self._det_name = ''
        self._saving_folder_name = ''
        self._synchronization = AcqSynch.SoftwareTrigger
        self._abort_flg = False 

    def _clean_acquisition(self):
        if self._last_image_read != -1:
            self._last_image_read = -1
            self._repetitions = 0
            self._new_data = False
            if self._expected_saving_images == 0:
                self._filename = ''

    def _prepare_saving(self):
        if len(self._filename) > 0:
            path, fname = os.path.split(self._filename)
            path = os.path.join(path, self._saving_folder_name)
            prefix, _ = os.path.splitext(fname)
            path = os.path.join(path, prefix)
            if not os.path.exists(path):
                os.makedirs(path)
            prefix += '_%s_' % self._det_name
            suffix = self._saving_format.lower()
            frame_per_file = 1
            if self._saving_format.lower() == 'hdf5':
                suffix = 'h5'
            self._limaccd.write_attribute('saving_frame_per_file',
                                          frame_per_file)
            self._limaccd.write_attribute('saving_format', self._saving_format)
            self._limaccd.write_attribute('saving_directory', path)
            self._limaccd.write_attribute('saving_mode', 'Auto_Frame')
            self._limaccd.write_attribute('saving_prefix', prefix)
            self._limaccd.write_attribute('saving_suffix', '.' + suffix)
        else:
            self._limaccd.write_attribute('saving_mode', 'Manual')

    def AddDevice(self, axis):
        if axis != 1:
            raise ValueError('This controller only have the axis 1')
        self._data_buff[1] = []

    def DeleteDevice(self, axis):
        self._data_buff.pop(axis)

    def StateAll(self):
        self._hw_state = self._limaccd.read_attribute('acq_status').value
        if self._hw_state == 'Running':
            self._state = State.Moving
            self._status = 'The LimaCCD is acquiring'

        elif self._hw_state == 'Ready':
            if self._last_image_read != (self._repetitions - 1) and \
                    self._synchronization == AcqSynch.HardwareTrigger and \
                    not self._abort_flg:
                self._log.warning('The LimaCCDs finished but the ctrl did not '
                                  'read all the data yet. Last image read %r'
                                  % self._last_image_read)
                self._state = State.Moving
                self._status = 'The LimaCCD is acquiring'
            else:
                
                self._state = State.On
                self._status = 'The LimaCCD is ready to acquire'

        else:
            self._state = State.Fault
            self._status = 'The LimaCCD state is: %s' % self._hw_state

    def StateOne(self, axis):
        return self._state, self._status

    def LoadOne(self, axis, value, repetitions):
        self._clean_acquisition()
        if axis != 1:
            raise RuntimeError('The master channel should be the axis 1')

        self._int_time = value
        if self._synchronization == AcqSynch.SoftwareTrigger:
            self._repetitions = 1
            acq_trigger_mode = self._software_trigger
        elif self._synchronization == AcqSynch.HardwareTrigger:
            self._repetitions = repetitions
            acq_trigger_mode = self._hardware_trigger
        else:
            # TODO: Implement the hardware gate
            raise ValueError('LimaCoTiCtrl allows only Software or Hardware '
                             'triggering')
     
        self._limaccd.write_attribute('acq_expo_time', self._int_time)
        self._limaccd.write_attribute('acq_nb_frames', self._repetitions)
        self._limaccd.write_attribute('latency_time', self._latency_time)
        self._limaccd.write_attribute('acq_trigger_mode', acq_trigger_mode)
        self._prepare_saving()

    def PreStartAll(self):
        self._limaccd.prepareAcq()
        return True

    def StartAll(self):
        self._abort_flg = False 
        self._limaccd.startAcq()
        if self._expected_saving_images > 0:
            if self._synchronization == AcqSynch.SoftwareTrigger:
                self._expected_saving_images -= 1
            else:
                self._expected_saving_images = 0

    def ReadAll(self):
        new_image_ready = 0
        self._new_data = True
        axis = 1
        if self._synchronization == AcqSynch.SoftwareTrigger:
            if self._hw_state != 'Ready':
                self._new_data = False
                return
            self._data_buff[axis] = [self._int_time]
        elif self._synchronization == AcqSynch.HardwareTrigger:
            attr = 'last_image_ready'
            self._data_buff[axis] = []
            new_image_ready = self._limaccd.read_attribute(attr).value
            if new_image_ready == self._last_image_read:
                self._new_data = False
                return
            self._last_image_read += 1
            new_data = (new_image_ready - self._last_image_read) + 1
            if new_image_ready == 0:
                new_data = 1
            self._data_buff[axis] = [self._int_time] * new_data
        self._last_image_read = new_image_ready
        self._log.debug('Leaving ReadAll %r' % len(self._data_buff[1]))

    def ReadOne(self, axis):
        self._log.debug('Entering in  ReadOn')
        if self._synchronization == AcqSynch.SoftwareTrigger:
            if not self._new_data:
                raise Exception('Acquisition did not finish correctly. LimaCCD '
                                'State %r' % self._hw_state)  
            return self._data_buff[axis][0]
        elif self._synchronization == AcqSynch.HardwareTrigger:
            return self._data_buff[axis]

    def AbortOne(self, axis):
        self.StateAll()
        self._expected_saving_images = 0
        if self._hw_state != 'Ready':
            self._limaccd.abortAcq()
            self._clean_acquisition()
            self._abort_flg = True
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
        elif param == 'expectedsavingimages': 
            self._expected_saving_images = value
        elif param == 'savingfoldername':
            self._saving_folder_name = value
        else:
            super(LimaCoTiCtrl, self).SetCtrlPar(parameter, value)

    def GetCtrlPar(self, parameter):
        param = parameter.lower()
        if param == 'filename':
            value = self._filename
        elif param == 'lastimagename':
            path = self._limaccd.read_attribute('saving_directory').value
            prefix = self._limaccd.read_attribute('saving_prefix').value
            suffix = self._limaccd.read_attribute('saving_suffix').value
            nr = self._limaccd.read_attribute('saving_next_number').value - 1
            attr = 'saving_index_format'
            index_format = self._limaccd.read_attribute(attr).value
            nr_formated = index_format % nr
            value = '%s/%s%s%s' % (path, prefix, nr_formated, suffix)
        elif param == 'detectorname':
            value = self._det_name
        elif param == 'savingformat':
            value = self._saving_format
        elif param == 'expectedsavingimages':            
            value = self._expected_saving_images
        elif param == 'savingfoldername':
            value = self._saving_folder_name
        else:
            value = super(LimaCoTiCtrl, self).GetCtrlPar(parameter)
        return value
