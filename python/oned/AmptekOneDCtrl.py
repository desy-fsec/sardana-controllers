import time
# import os

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import OneDController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class AmptekOneDCtrl(OneDController):
    """This class is the OneD controller for the Amptek detector.
    It works as slave of the AmptekPX5CoTiCtrl, which prepares and
    starts the acquisition."""

    axis_attributes = {
        'TangoDevice': {Type: str, Access: ReadOnly},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: 'PyTango.DevString',
            Description: 'The name of the Amptek Tango device'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    MaxDevice = 97

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        OneDController.__init__(self, inst, props, *args, **kwargs)
        if self.TangoHost is None:
            self.amptek_device_name = self.RootDeviceName
        else:
            self.amptek_device_name = self.TangoHost + ":10000/" + \
                self.RootDeviceName
        self.started = False
        self.max_device = 1
        self.device_available = []
        self.device_available.append(False)
        self.sta = State.On
        self.acqTime = 0
        self.acqStartTime = None

    def AddDevice(self, ind):
        OneDController.AddDevice(self, ind)
        if ind > self.max_device:
            print("AmptekOneDCtrl: False index %d max %d"
                  % (ind, self.max_device))
            return
        self.proxy = PyTango.DeviceProxy(self.amptek_device_name)
        self.device_available[ind - 1] = True

    def DeleteDevice(self, ind):
        OneDController.DeleteDevice(self, ind)
        self.proxy = None
        self.device_available[ind - 1] = 0

    def StateAll(self):
        if self.acqStartTime is not None:  # acquisition was started
            now = time.time()
            elapsedTime = now - self.acqStartTime
            # acquisition has probably not finished yet
            if elapsedTime < self.acqTime:
                self.sta = State.Moving
                self.status = "Acqusition time has not elapsed yet."
                return
            else:
                self.acqStartTime = None
        try:
            self.sta = self.proxy.State()
        except PyTango.DevFailed:
            self.proxy.ClearInputBuffer()
            self.sta = self.proxy.State()
        self.status = self.proxy.Status()

    def StateOne(self, ind):
        return self.sta, self.status

    def LoadOne(self, axis, value, repetitions, latency_time):
        self.acqTime = value

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        data = self.proxy.Spectrum
        return data

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, value):
        return True

    def StartOne(self, ind, value):
        self.acqStartTime = time.time()

    def AbortOne(self, ind):
        self.proxy.Disable()

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            if self.device_available[ind - 1]:
                tango_device = self.amptek_device_name
                return tango_device

    def SetAxisExtraPar(self, ind, name, value):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"
