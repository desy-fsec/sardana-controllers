#!/usr/bin/env python

import PyTango
import time
from sardana import State
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, MaxDimSize

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

    axis_attributes = {
        'ExposureTime': {
            Type: float,
            'R/W Type': 'READ_WRITE',
            'Description': 'Exposure time',
            'Defaultvalue': 1.0},
        'LatencyTime': {
            'Type': float,
            'R/W Type': 'READ_WRITE',
            'Description': 'Latency time',
            'Defaultvalue': 1.0},
        'NbFrames': {
            'Type': int,
            'R/W Type': 'READ_WRITE',
            'Description': 'Number of frames to be acquired',
            'Defaultvalue': 1},
        'TriggerMode': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'Mode in case of external trigger',
            'Defaultvalue': 'EXTERNAL_TRIGGER'},
        'FilePrefix': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'File prefix',
            'Defaultvalue': 'Img'},
        'FileFormat': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'File format',
            'Defaultvalue': 'EDF'},
        'FileDir': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'Directory path to save files',
            'Defaultvalue': '/tmp'},
        'NextNumber': {
            'Type': int,
            'R/W Type': 'READ_WRITE',
            'Description': 'File number for next image',
            'Defaultvalue': 1},
        'LastImageReady': {
            'Type': int,
            'R/W Type': 'READ',
            'Description': 'Image Id of last acquired image',
            },
        'Value': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'Image identifier'},
        }

    ctrl_properties = {
        'LimaDeviceName': {'type': str,
                           'description': 'Detector device name',
                           'defaultvalue': ''
                           }
        }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst),
                        repr(props))

        try:
            self.LimaDevice = PyTango.DeviceProxy(self.LimaDeviceName)
        except PyTango.DevFailed, e:
            self._log.error("__init__(): Could not create a device proxy from "
                            "following device name: %s.\nException: %s",
                            self.LimaDeviceName, e)
            raise

        self.t0 = time.time()

    def AddDevice(self, axis):
        self._log.debug("AddDevice(%d): Entering...", axis)
        pass

    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        pass

    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        if self.LimaDevice is None:
            return PyTango.DevState.FAULT
        # Avoids continuous state queries during acquisition
        t = time.time()
        acqt = self.GetAxisExtraPar(axis, 'ExposureTime')
        delta = t - self.t0
        if delta < acqt:
            self._log.debug("StateOne(%d): Non disturbing the device for %s s"
                            % (axis, delta))
            return State.Running, 'Running (expected)'
        try:
            limaState = self.LimaDevice.read_attribute('acq_status').value

            if limaState == 'Ready':
                return State.Standby, limaState
            elif limaState == 'Running':
                return State.Running, limaState
            elif limaState == 'Configuration':
                return State.Init, limaState
            else:
                return State.Fault, limaState
        except Exception, e:
            self._log.error("StateOne(%d): Could not verify state of the "
                            "device: %s.\nException: %s",
                            axis, self.LimaDeviceName, e)
            return (PyTango.DevState.UNKNOWN, "Lima Device is not responding.")

    def PreReadOne(self, axis):
        self._log.debug("PreReadOne(%d): Entering...", axis)
        pass

    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        try:
            return self.filename
        except Exception, e:
            self._log.error("StateOne(%d): Could not read image counter of the"
                            " device: %s.\nException: %s",
                            axis, self.LimaDeviceName, e)

    def _save_filename(self, axis):
        number = self.GetAxisExtraPar(axis, 'NextNumber')
        prefix = self.GetAxisExtraPar(axis, 'FilePrefix')
        file_dir = self.GetAxisExtraPar(axis, 'FileDir')
        file_format = self.GetAxisExtraPar(axis, 'FileFormat')
        self.filename = '%s/%s_%s.%s' % (file_dir, prefix, number, file_format)

    def ReadAll(self):
        self._log.debug("ReadAll: Entering...")
        pass

    def PreStartOne(self, axis, position=None):
        self._log.debug("PreStartOne(%d): Entering...", axis)
        try:
            self.LimaDevice.prepareAcq()
            return True
        except Exception, e:
            self._log.error("PreStartOne(%d): Could not prepare acquisition for"
                            " device: %s.\nException: %s",
                            axis, self.LimaDeviceName, e)
            return False

    def StartOne(self, axis, position=None):
        self._log.debug("StartOne(%d): Entering...", axis)
        pass

    def StartAll(self):
        self._log.debug("StartAll: Entering...")
        self.LimaDevice.startAcq()
        self.t0 = time.time()

    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(%d): Entering...", axis)
        if self.GetAxisExtraPar(axis,'NbFrames') == 0:
            raise RuntimeError('You must set the number of frames')
        self.LimaDevice.write_attribute('acq_expo_time', value)
        self._save_filename(axis)

    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        self.LimaDevice.stopAcq()

    def SetAxisExtraPar(self, axis, name, value):
        if name == 'ExposureTime':
            self.LimaDevice.write_attribute('acq_expo_time', value)
        elif name == 'LatencyTime':
            self.LimaDevice.write_attribute('latency_time', value)
        elif name == 'NbFrames':
            self.LimaDevice.write_attribute('acq_nb_frames', value)
        elif name == 'TriggerMode':
            TrigList = ['INTERNAL_TRIGGER',
                        'EXTERNAL_TRIGGER',
                        'EXTERNAL_TRIGGER_MULTI',
                        'EXTERNAL_GATE',
                        'EXTERNAL_START_STOP']
            if value in TrigList:
                self.LimaDevice.write_attribute('acq_trigger_mode', value)
            else:
                self._log.error('Attribute TriggerMode: ' +
                                'Not supported trigger mode (%s).' % value)
        elif name == 'FilePrefix':
            self.LimaDevice.write_attribute('saving_prefix', value)
        elif name == 'FileFormat':
            self.LimaDevice.write_attribute('saving_format', value)
        elif name == 'FileDir':
            self.LimaDevice.write_attribute('saving_directory', value)
        elif name == 'NextNumber':
            self.LimaDevice.write_attribute('saving_next_number', value)

    def GetAxisExtraPar(self, axis, name):
        if name == 'ExposureTime':
            value = self.LimaDevice.read_attribute('acq_expo_time').value
            self._log.debug('ExposureTime: %s' % value)
            return value
        elif name == 'LatencyTime':
            value = self.LimaDevice.read_attribute('latency_time').value
            self._log.debug('LatencyTime: %s' % value)
            return value
        elif name == 'NbFrames':
            value = self.LimaDevice.read_attribute('acq_nb_frames').value
            self._log.debug('NbFrames: %s' % value)
            return value
        elif name == 'TriggerMode':
            value = self.LimaDevice.read_attribute('acq_trigger_mode').value
            self._log.debug('TriggerMode: %s' % value)
            return value
        elif name == 'FilePrefix':
            value = self.LimaDevice.read_attribute('saving_prefix').value
            self._log.debug('FilePrefix: %s' % value)
            return value
        elif name == 'FileFormat':
            value = self.LimaDevice.read_attribute('saving_format').value
            self._log.debug('FileFormat: %s' % value)
            return value
        elif name == 'FileDir':
            value = self.LimaDevice.read_attribute('saving_directory').value
            self._log.debug('FileDir: %s' % value)
            return value
        elif name == 'NextNumber':
            value = self.LimaDevice.read_attribute('saving_next_number').value
            self._log.debug('NextNumber: %s' % value)
            return value
        elif name == 'LastImageReady':
            value = self.LimaDevice.read_attribute('last_image_ready').value
            self._log.debug('LastImageReady: %s' % value)
            return value
