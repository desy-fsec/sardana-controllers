#!/usr/bin/env python

from sardana.pool.controller import Type, Description
from LimaCoTiCtrl import LimaCoTiCtrl, HW_TRIG, SW_TRIG
import PyTango


class LimaXspress3CTCtrl(LimaCoTiCtrl):
    """
    TODO:
    """

    gender = "LimaCounterTimer"
    model = "Basic"
    organization = "CELLS - ALBA"
    image = "Lima_ctrl.png"
    logo = "ALBA_logo.png"

    MaxDevice = 11

    xspress_ctrl_properties = {
        'Xspress3DeviceName': {Type: str, Description: 'Detector device name'},
        }
    ctrl_properties = {}
    ctrl_properties.update(LimaCoTiCtrl.ctrl_properties)
    ctrl_properties.update(xspress_ctrl_properties)

    def __init__(self, inst, props, *args, **kwargs):
        LimaCoTiCtrl.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst),
                        repr(props))

        try:
            self._xspress3 = PyTango.DeviceProxy(self.Xspress3DeviceName)
        except PyTango.DevFailed as e:
            raise RuntimeError('__init__(): Could not create a device proxy '
                               'from following device name: %s.\nException: '
                               '%s ' % (self.Xspress3DeviceName, e))

        self._nr_channels = self._xspress3.read_attribute('numChan').value
        self.MaxDevice = (self._nr_channels * 2) + 1
        self._last_dt_read = -1
        self._new_data_dt = False 

    def _get_values(self, image_nr):
        # TODO optimize reading
        for channel in range(self._nr_channels):
            data = self._xspress3.ReadScalers([image_nr, channel])
            dt = (channel + 1) * 2
            dtf = dt + 1
            # dt value
            if dt in self._data_buff:
                self._data_buff[dt] += [data[9]]
            # dtf value
            if dtf in self._data_buff:
                self._data_buff[dtf] += [data[10]]
       
    def _clean_acquisition(self):
        LimaCoTiCtrl._clean_acquisition(self)
        self._last_dt_read = self._last_image_read
        self._new_data_dt = False 

    def _clean_data(self):
        for channel in range(self._nr_channels):
            dt = (channel + 1) * 2
            dtf = dt + 1
            if dt in self._data_buff:
                self._data_buff[dt] = []
            if dtf in self._data_buff:
                self._data_buff[dtf] = []

    def AddDevice(self, axis):
        if axis == 1:
            LimaCoTiCtrl.AddDevice(self, axis)
        else:
            self._data_buff[axis] = []

    def ReadAll(self):
        LimaCoTiCtrl.ReadAll(self)
        if not self._new_data:
            return
        self._clean_data()
        if self._trigger_mode == SW_TRIG:
            self._get_values(0)
        else:
            self._last_dt_read += 1
            nr_images = self._last_image_read - self._last_dt_read + 1
            for i in range(nr_images):
                image_nr = self._last_dt_read + i
                self._get_values(image_nr)
            self._new_data_dt = True
            self._last_dt_read = self._last_image_read

    def ReadOne(self, axis):
        if axis == 1:
            return LimaCoTiCtrl.ReadOne(self, axis)
        else:
            if self._trigger_mode == SW_TRIG:
                return self._data_buff[axis][0]
            else:
                if not self._new_data_dt:
                    return []
                else:
                    return self._data_buff[axis]
