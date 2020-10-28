import PyTango
from sardana.pool.controller import CounterTimerController
# import time


from sardana import DataAccess
# from sardana import State, DataAccess
# from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class LimaRoICounterCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller " \
        + "for getting the Lima RoIs as counters"

    axis_attributes = {
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly},
        'RoIx1': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'RoIx2': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'RoIy1': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'RoIy2': {Type: 'PyTango.DevLong', Access: ReadWrite},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: 'PyTango.DevString',
            Description: 'Name of the roicounter lima device'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where LimaCCDs runs'},
    }

    gender = "CounterTimer"
    model = "LimaCounter"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        if self.TangoHost is not None:
            self.node = self.TangoHost
            self.port = 10000
            if self.TangoHost.find(':'):
                lst = self.TangoHost.split(':')
                self.node = lst[0]
                self.port = int(lst[1])
        self.proxy_name = self.RootDeviceName
        if self.TangoHost is not None:
            self.proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(self.proxy_name)
        self.proxy = PyTango.DeviceProxy(self.proxy_name)
        self.proxy.Stop()
        self.proxy.Start()
        self.roi_id = []
        self.roi_name = []

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)
        name = ["roi" + str(ind)]
        self.roi_name.append(name)
        self.roi_id.append(self.proxy.addNames(name)[0])
        roi = [self.roi_id[ind - 1], 0, 0, 1, 1]
        self.proxy.setRois(roi)

    def DeleteDevice(self, ind):
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy = None

    def StateOne(self, ind):
        try:
            counterstatus = self.proxy.CounterStatus
        except Exception:
            sta = PyTango.DevState.FAULT
            status = "roicounter Lima device not started"
            tup = (sta, status)
            return tup
        if counterstatus == -1:
            sta = PyTango.DevState.MOVING
            status = "Taking data"
        else:
            sta = PyTango.DevState.ON
            if counterstatus == -2:
                status = "Not images in buffer"
            else:
                status = "RoI computed"
        tup = (sta, status)
        return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        counts = self.proxy.command_inout("readCounters", 0)
        return counts[7*(ind - 1) + 2]

    def AbortOne(self, ind):
        pass

    def PreStartAll(self):
        self.wantedCT = []

    def PreStartOne(self, ind, value):
        return True

    def StartOne(self, ind, value):
        self.wantedCT.append(ind)

    def StartAll(self):
        pass

    def LoadOne(self, ind, value, repetitions, latency_time):
        pass

    def GetAxisExtraPar(self, ind, name):
        if name == "TangoDevice":
            return self.proxy_name
        elif name == "RoIx1":
            roi = self.proxy.getRois(self.roi_name[ind - 1])
            return roi[1]
        elif name == "RoIx2":
            roi = self.proxy.getRois(self.roi_name[ind - 1])
            return roi[3]
        elif name == "RoIy1":
            roi = self.proxy.getRois(self.roi_name[ind - 1])
            return roi[2]
        elif name == "RoIy2":
            roi = self.proxy.getRois(self.roi_name[ind - 1])
            return roi[4]

    def SetAxisExtraPar(self, ind, name, value):
        roi = self.proxy.getRois(self.roi_name[ind - 1])
        if name == "RoIx1":
            roi[1] = value
            self.proxy.setRois(roi)
        elif name == "RoIx2":
            roi[3] = value
            self.proxy.setRois(roi)
        elif name == "RoIy1":
            roi[2] = value
            self.proxy.setRois(roi)
        elif name == "RoIy2":
            roi[4] = value
            self.proxy.setRois(roi)

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> LimaCounterCtrl  dying ")


if __name__ == "__main__":
    obj = LimaRoICounterCtrl('test')
