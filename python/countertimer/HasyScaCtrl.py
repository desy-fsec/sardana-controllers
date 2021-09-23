import PyTango
from sardana.pool.controller import CounterTimerController
import time
# import time, os


from sardana import DataAccess
# from sardana import State, DataAccess
# from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class HasyScaCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the HasySca"
#    axis_attributes = {'Offset': {Type: float, Access: ReadWrite}}

    ctrl_properties = {
        'mca': {Type: str, Description: 'The MCA name, tango device'},
        'roi1': {Type: str, Description: 'The lower ROI limit'},
        'roi2': {Type: str, Description: 'The upper ROI limit'},
    }

    gender = "CounterTimer"
    model = "HasySca"
    organization = "DESY"
    state = ""
    status = ""

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.max_device = 1
        self.tango_device = [None]
        self.proxy = [None]
        self.device_available = [0]
        self.started = False

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)
        if ind > self.max_device:
            print("HasyScaCtrl wrong index")
            return
        self.proxy[ind - 1] = PyTango.DeviceProxy(self.mca)
        self.device_available[ind - 1] = 1

    def DeleteDevice(self, ind):
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        if self.device_available[ind - 1] == 1:
            #
            # at this point the state of the mca-controller
            #     somehow stays MOVING
            #
            sta = self.proxy[ind - 1].State()
            sta = PyTango.DevState.ON
            tup = (sta, "Message from HasyScaCtrl")
            return tup

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        if self.device_available[ind - 1] == 0:
            return False
        if self.proxy[ind - 1].BankId != 0:
            self._log.error("HasyScaCtrl, BankId != 0 (%d) for %s"
                            % (self.proxy[ind - 1].BankId,
                               self.proxy[ind - 1].name()))
            return 0

        if self.proxy[ind - 1].StateBank0 != 0:
            self.proxy[ind - 1].Stop()
            self.proxy[ind - 1].Read()
        data = self.proxy[ind - 1].Data
        sum = 0
        for i in range(int(self.roi1), int(self.roi2)):
            sum += data[i]
        return sum

    def AbortOne(self, ind):
        return True

    def PreStartAll(self):
        self.wantedCT = []

    def PreStartOne(self, ind, value):
        return True

    def StartOne(self, ind, value):
        self.wantedCT.append(ind)

    def StartAll(self):
        self.started = True
        self.start_time = time.time()
        return True

    def LoadOne(self, ind, value, repetitions, latency_time):
        pass

    def GetAxisExtraPar(self, ind, name):
        if name == "Offset":
            if self.device_available[ind - 1]:
                return float(
                    self.proxy[ind - 1].read_attribute("Offset").value)

    def SetAxisExtraPar(self, ind, name, value):
        if name == "Offset":
            if self.device_available[ind - 1]:
                self.proxy[ind - 1].write_attribute("Offset", value)

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    def start_acquisition(self, value=None):
        return True

    def __del__(self):
        print("PYTHON -> HasyScaCtrl dying")


if __name__ == "__main__":
    obj = HasyScaCtrl('test')
