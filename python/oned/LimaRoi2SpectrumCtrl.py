import PyTango
from sardana.pool.controller import OneDController
# import time, os

from sardana import DataAccess
# from sardana import State, DataAccess
# from sardana.pool.controller import MotorController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class LimaRoi2SpectrumCtrl(OneDController):
    "This class is the One D controller for the Roi2Spectrum Lima device"

    axis_attributes = {'DataLength': {Type: int, Access: ReadWrite}, }

    ctrl_properties = {
        'Roi2SpectrumDeviceName': {
            Type: str,
            Description:
            'The name of the Roi2SpectrumDeviceServer device from Lima'}
    }

    gender = "OneD"
    model = "LimaRoi2Spectrum"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        OneDController.__init__(self, inst, props, *args, **kwargs)
        self.proxy = PyTango.DeviceProxy(self.Roi2SpectrumDeviceName)
        self.started = False

    def AddDevice(self, ind):
        OneDController.AddDevice(self, ind)

    def DeleteDevice(self, ind):
        OneDController.DeleteDevice(self, ind)
        self.proxy = None

    def StateOne(self, ind):
        sta = self.proxy.command_inout("State")
        status = self.proxy.command_inout("Status")
        tup = (sta, status)
        return tup

    def LoadOne(self, axis, value, repetitions, latency_time):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        im = []
        im.append(ind - 1)
        frame_id = self.proxy.CounterStatus
        # frame_id should be always 0 because we take only one image
        im.append(frame_id)
        raw_spectrum = self.proxy.command_inout("readImage", im)
        if frame_id != 0:  # more than one spectrum is read
            rois_names = self.proxy.getNames()
            cmd = []
            cmd.append(rois_names[ind - 1])
            roi_mode = self.proxy.getRoiModes(cmd)
            roi_values = self.proxy.getRois(cmd)
            if roi_mode[0] == "LINES_SUM":
                datalength = roi_values[3]
            elif roi_mode[0] == "COLUMN_SUM":
                datalength = roi_values[4]
            data = []
            for i in range(len(raw_spectrum) - datalength, len(raw_spectrum)):
                data.append(raw_spectrum[i])
        else:
            data = raw_spectrum
        return data

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, value):
        return True

    def StartOne(self, ind, value):
        pass

    def AbortOne(self, ind):
        pass

    def GetAxisExtraPar(self, ind, name):
        if name == "DataLength":
            rois_names = self.proxy.getNames()
            cmd = []
            cmd.append(rois_names[ind - 1])
            roi_mode = self.proxy.getRoiModes(cmd)
            roi_values = self.proxy.getRois(cmd)
            if roi_mode[0] == "LINES_SUM":
                datalength = roi_values[3]
            elif roi_mode[0] == "COLUMN_SUM":
                datalength = roi_values[4]
            else:
                datalength = -1
            return datalength

    def SetAxisExtraPar(self, ind, name, value):
        pass

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def __del__(self):
        print("LimaRoi2SpectrumCtrl/%s " % self.inst_name)


if __name__ == "__main__":
    obj = OneDController('test')
