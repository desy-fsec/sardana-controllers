import PyTango

# import time, os

from sardana import DataAccess
# from sardana import State, DataAccess
from sardana.pool.controller import ZeroDController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class HasyADCCtrl(ZeroDController):
    "This class is the Tango Sardana Zero D controller " \
        + "for a generic Hasylab ADC"

    axis_attributes = {
        'TangoDevice': {Type: str, Access: ReadOnly},
        'Conversion': {Type: float, Access: ReadWrite},
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the VFCADC Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    MaxDevice = 97

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        ZeroDController.__init__(self, inst, props, *args, **kwargs)
#        print "PYTHON -> ZeroDController ctor for instance", inst
        if self.TangoHost is None:
            self.db = PyTango.Database()
        else:
            #
            # TangoHost can be hasgksspp07eh3:10000
            #
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
        self.conversion = []
        self.device_available = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.conversion.append(1.)
            self.max_device = self.max_device + 1
        self.started = False

    def AddDevice(self, ind):
        #        print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        # In AddDevice method for index", ind
        ZeroDController.AddDevice(self, ind)
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
        #        print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        # In DeleteDevice method for index", ind
        ZeroDController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        #        print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        # In StateOne method for index", ind
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta, "ADC is in ON State")
            elif sta == PyTango.DevState.MOVING:
                tup = (sta, "ADC is busy")
            else:
                tup = (sta, "Unknown status")
            return tup

    def PreReadAll(self):
        #    print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        # In PreReadAll method"
        pass

    def PreReadOne(self, ind):
        #        print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        #     In PreReadOne method for index", ind
        pass

    def ReadAll(self):
        #        print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        #     In ReadAll method"
        pass

    def ReadOne(self, ind):
        #        print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        #     In ReadOne method for index", ind
        if self.device_available[ind - 1] == 1:
            return self.proxy[ind - 1].read_attribute("Value").value \
                * self.conversion[ind - 1]

    def PreStartAll(self):
        #        print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        #     In PreStartAll method"
        self.wanted = []

    def PreStartOne(self, ind, value):
        pass

    def StartOne(self, ind, value):
        # print "PYTHON -> HasyADCCtrl/", self.inst_name,": \
        #     In StartOne method for index", ind
        self.wanted.append(ind)

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device
            elif name == "Conversion":
                return self.conversion[ind - 1]

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "Conversion":
                self.conversion[ind - 1] = value

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> HasyADCCtrl being deleted")


if __name__ == "__main__":
    obj = ZeroDController('ADC')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
