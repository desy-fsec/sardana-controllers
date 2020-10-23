import PyTango
from sardana.pool.controller import CounterTimerController
import time

from sardana import DataAccess
# from sardana import State, DataAccess
# from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description
# from sardana.pool.controller import Type, Access, Description, DefaultValue
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

# TimeTriggerStepSize
# TriggerPulseLength


class pilcTimerCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller " + \
        "for the PiLCTriggerGenerator used as timer"

    axis_attributes = {'TangoDevice': {Type: str, Access: ReadOnly}, }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description:
            'The root name of the PiLCTriggerGenerator Tango device'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    gender = "CounterTimer"
    model = "PilcTriggerGenerator"
    organization = "DESY"
    state = ""
    status = ""

    ############
    # __del__ ##
    ############

    def __del__(self):
        print("PYTHON -> pilcTimerCtrl dying")

    #############
    # __init__ ##
    #############

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
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
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.max_device += 1

    #############
    # AbortOne ##
    #############

    def AbortOne(self, ind):
        if self.device_available[ind - 1] == 1:
            self.proxy[ind - 1].write_attribute('Arm', 0)

    ##############
    # AddDevice ##
    ##############

    def AddDevice(self, ind):
        CounterTimerController.AddDevice(self, ind)
        if ind > self.max_device:
            print("False index")
            return

        proxy_name = self.tango_device[ind - 1]

        if self.TangoHost is None:
            proxy_name = self.tango_device[ind - 1]
        else:
            proxy_name = (
                            str(self.node)
                            + (":%s/" % self.port)
                            + str(self.tango_device[ind - 1])
                            )

        self.proxy[ind - 1] = PyTango.DeviceProxy(proxy_name)
        self.device_available[ind - 1] = 1

    #################
    # DeleteDevice ##
    #################

    def DeleteDevice(self, ind):
        CounterTimerController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    #########################
    # GetExtraAttributePar ##
    #########################

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "TangoDevice":
                tango_device = (self.node
                                + ":"
                                + str(self.port)
                                + "/"
                                + self.proxy[ind - 1].name()
                                )
                return tango_device

    ############
    # LoadOne ##
    ############

    def LoadOne(self, ind, value, repetitions, latency_time):
        if self.device_available[ind - 1] == 1:
            self.proxy[ind - 1].write_attribute("TimeTriggerStepSize", value)

    ###############
    # PreReadAll ##
    ###############

    def PreReadAll(self):
        pass

    ###############
    # PreReadOne ##
    ###############

    def PreReadOne(self, ind):
        pass

    ################
    # PreStartAll ##
    ################

    def PreStartAll(self):
        self.wantedCT = []
        self.startTime = [0.0 for _ in range(len(self.proxy))]

    ################
    # PreStartOne ##
    ################

    def PreStartOne(self, ind, value):
        self.proxy[ind - 1].write_attribute('TriggerPulseLength', 0.00005)
        self.proxy[ind - 1].write_attribute('TriggerMode', 2)
        self.proxy[ind - 1].write_attribute('FileDir', '/tmp')
        self.proxy[ind - 1].write_attribute('FilePrefix', '.timer' + str(ind))
        self.proxy[ind - 1].write_attribute('NbTriggers', 1)

        return True

    ############
    # ReadAll ##
    ############

    def ReadAll(self):
        pass

    ############
    # ReadOne ##
    ############

    def ReadOne(self, ind):
        if self.device_available[ind - 1] == 1:
            # Elapsed time can not be read from the device
            # so it is calculated by software.

            setTime = (
                        self.proxy[ind - 1].
                        read_attribute("TimeTriggerStepSize").
                        value
                        )

            exposureTime = (
                            time.time()
                            - self.startTime[ind - 1]
                            )

            if exposureTime > setTime:
                exposureTime = setTime

            return exposureTime

    ###############
    # SendToCtrl ##
    ###############

    def SendToCtrl(self, in_data):
        return "Nothing sent"

    #########################
    # SetExtraAttributePar ##
    #########################

    def SetExtraAttributePar(self, ind, name, value):
        pass

    #############
    # StartAll ##
    #############

    def StartAll(self):
        for i in self.wantedCT:
            self.proxy[i].write_attribute('Arm', 1)
            self.startTime[i] = time.time()

    #############
    # StartOne ##
    #############

    def StartOne(self, ind, val):
        if self.device_available[ind - 1] == 1:
            self.wantedCT.append(ind - 1)

    #############
    # StateOne ##
    #############

    def StateOne(self, ind):
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            if sta == PyTango.DevState.ON:
                status_string = "Timer is in ON state"
            elif sta == PyTango.DevState.MOVING:
                status_string = "Timer is busy"

            return (sta, status_string)
