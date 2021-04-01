import PyTango
import time
# import os

# from sardana import State
from sardana import DataAccess
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class TimePixCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the TimePix"

    axis_attributes = {
        'AcquisitionType': {
            Type: 'PyTango.DevLong',
            Access: ReadWrite,
            Description: '0-> StartAcquisition (hw trigger), '
            '1-> StartSingleAcquisition (sw trigger)'
        },
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the TimePix Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    MaxDevice = 97

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        TwoDController.__init__(self, inst, props, *args, **kwargs)
        print("PYTHON -> TwoDController ctor for instance", inst)
        if self.TangoHost is None:
            self.db = PyTango.Database()
        else:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find(':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int(lst[1])
            self.db = PyTango.Database(self.node, self.port)
        name_dev_ask = self.RootDeviceName + "*"
        self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.device_available = []
        self.start_time = []
        self.acq_type = []
        self.exp_time = 0
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.start_time.append(time.time())
            self.acq_type.append(0)
            self.max_device = self.max_device + 1
        self.started = False

    def AddDevice(self, ind):
        # print "PYTHON -> TimePixCtrl/", self.inst_name,": \
        #        In AddDevice method for index", ind
        TwoDController.AddDevice(self, ind)
        if ind > self.max_device:
            print("False index")
            return
        proxy_name = self.tango_device[ind - 1]
        if self.TangoHost is None:
            proxy_name = self.tango_device[ind - 1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(self.tango_device[ind - 1])
        self.proxy[ind - 1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind - 1] = 1

    def DeleteDevice(self, ind):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In DeleteDevice method for index", ind
        TwoDController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        #     ": In StateOne method for index", ind
        if self.device_available[ind - 1] == 1:
            if time.time() - self.start_time[ind - 1] > \
               self.exp_time and self.started is True:
                try:
                    sta_tmp = self.proxy[ind - 1].command_inout("State")
                    if sta_tmp == PyTango.DevState.MOVING:
                        self.proxy[ind - 1].command_inout("stop_acquisition")
                    self.started = False
                except Exception:
                    pass
                sta = PyTango.DevState.ON
                tup = (sta, "Camera ready")
            elif self.started is True:
                sta = PyTango.DevState.MOVING
                tup = (sta, "Camera taking images")
            else:
                sta = PyTango.DevState.ON
                tup = (sta, "Camera ready")

            return tup

    def PreReadAll(self):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In PreReadAll method"
        pass

    def PreReadOne(self, ind):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In PreReadOne method for index", ind
        try:
            sta_tmp = self.proxy[ind - 1].command_inout("State")
            if sta_tmp == PyTango.DevState.MOVING:
                self.proxy[ind - 1].command_inout("stop_acquisition")
        except Exception:
            pass

    def ReadAll(self):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        #     ": In ReadAll method"
        pass

    def ReadOne(self, ind):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In ReadOne method for index", ind
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value

    def PreStartAll(self):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In PreStartAll method"
        pass

    def StartOne(self, ind, position=None):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In StartOne method for index", ind
        self.proxy[ind - 1].command_inout("start_acquisition")

        self.started = True
        self.start_time[ind - 1] = time.time()

    def AbortOne(self, ind):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In AbortOne method for index", ind
        try:
            sta_tmp = self.proxy[ind - 1].command_inout("State")
            if sta_tmp == PyTango.DevState.MOVING:
                self.proxy[ind - 1].command_inout("stop_acquisition")
        except Exception:
            pass

    def LoadOne(self, ind, value, repetitions, latency_time):
        self.exp_time = value

    def GetAxisExtraPar(self, ind, name):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In GetExtraFeaturePar method for index", ind," name=", name
        pass

    def SetAxisExtraPar(self, ind, name, value):
        #        print "PYTHON -> TimePixCtrl/", self.inst_name, \
        # ": In SetExtraFeaturePar method for index", ind," name=", name, \
        # " value=", value
        pass

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> TimePixCtrl dying")


if __name__ == "__main__":
    obj = TwoDController('test')
