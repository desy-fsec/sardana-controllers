import PyTango
'''

this controller should be able to handle 'ct' and 'ascan', 'dscan', etc.
'ct' has no hooks. therefore the controller itself has to arm or disarm
the detector, if necessary.

NbTriggers = 1

initial state
  device: ON/idle
  filewriter: ON/ready

device.arm()
  device: ON/ready
  filewriter: MOVING/acquire

device.trigger()
  device: ON/ready
  filewriter: MOVING/acquire

Even for ascans NbTriggers == 1. We create a file for every stop
because we don't know how many stops a scan will have.
'''
# from sardana import State, DataAccess
from sardana import DataAccess
from sardana.pool.controller import TwoDController
# from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import Type, Access, Description
# from sardana.pool import PoolUtil

import time
import os


ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

TIME_SLEEP = 0.01


class EigerDectrisCtrl(TwoDController):
    "This class is the Tango Sardana Two D controller for the EigerDectris"

    axis_attributes = {
        'CountTime': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'CountTimeInte': {Type: 'PyTango.DevDouble', Access: ReadWrite},
        'NbTriggers': {Type: 'PyTango.DevLong', Access: ReadWrite},
        'TriggerMode': {Type: 'PyTango.DevString', Access: ReadWrite},
        'TangoDevice': {Type: 'PyTango.DevString', Access: ReadOnly}
    }

    ctrl_properties = {
        'RootDeviceName': {
            Type: str,
            Description: 'The root name of the EigerDectris Tango devices'},
        'TangoHost': {
            Type: str,
            Description: 'The tango host where searching the devices'},
    }

    MaxDevice = 97

    def __init__(self, inst, props, *args, **kwargs):
        self.TangoHost = None
        TwoDController.__init__(self, inst, props, *args, **kwargs)

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
        self.tango_device_fw = []  # file writer
        self.proxy = []
        self.proxy_fw = []
        self.device_available = []
        self.APIVersion = []
        for name in self.devices.value_string:
            self.tango_device.append(name)
            self.tango_device_fw.append(self.getFwName(name))

            self.proxy.append(None)
            self.proxy_fw.append(None)
            self.device_available.append(0)
            self.max_device = self.max_device + 1
            if len(self.APIVersion) == 0:
                #
                # temp '1.8.0'
                #
                temp = getDeviceProperty(
                    name, 'APIVersion', tangoHost=self.TangoHost)[0]
                self.APIVersion = [ll for ll in temp.split('.')]
        self.started = False
        self.dft_CountTime = 0
        self.CountTime = []
        self.dft_CountTimeInte = 0
        self.CountTimeInte = []
        self.dft_TriggerMode = ""
        self.TriggerMode = []
        self.dft_NbTriggers = 0
        self.NbTriggers = []

        self.isatty = os.isatty(1)

    def getFwName(self, name):
        '''
        get the filewriter name belonging to name, e.g.: p62/eiger/e4m
        so we look at the list of filewriters and check theis EigerDevice
        property to find the filewriter in charge of name
        '''
        devsFw = getDeviceNamesByClass(
            "EigerFilewriter", tangoHost=self.TangoHost)
        for devFw in devsFw:
            prop = getDeviceProperty(
                devFw, 'EigerDevice', tangoHost=self.TangoHost)
            if prop[0] == name:
                return devFw
        return None

    def AddDevice(self, ind):
        TwoDController.AddDevice(self, ind)
        if ind > self.max_device:
            print("EigerDectris.AddDevice: ind %d > max_device %d" %
                  (ind, self.max_device))
            return
        proxy_name = self.tango_device[ind - 1]
        proxy_name_fw = self.tango_device_fw[ind - 1]
        if self.TangoHost is None:
            proxy_name = self.tango_device[ind - 1]
            proxy_name_fw = self.tango_device_fw[ind - 1]
        else:
            proxy_name = str(self.node) + (":%s/" % self.port) + \
                str(self.tango_device[ind - 1])
            proxy_name_fw = str(self.node) + (":%s/" % self.port) + \
                str(self.tango_device_fw[ind - 1])
        self.proxy[ind - 1] = PyTango.DeviceProxy(proxy_name)
        self.proxy_fw[ind - 1] = PyTango.DeviceProxy(proxy_name_fw)
        self.device_available[ind - 1] = 1
        self.CountTime.append(self.dft_CountTime)
        self.CountTimeInte.append(self.dft_CountTimeInte)
        self.TriggerMode.append(self.dft_TriggerMode)
        self.NbTriggers.append(self.dft_NbTriggers)

    def DeleteDevice(self, ind):
        if self.isatty:
            print("EigerDectris.deleteDevice %s" %
                  self.tango_device[ind - 1])
        TwoDController.DeleteDevice(self, ind)
        self.proxy[ind - 1] = None
        self.proxy_fw[ind - 1] = None
        self.device_available[ind - 1] = 0

    def StateOne(self, ind):
        if self.device_available[ind - 1] == 1:
            sta = self.proxy[ind - 1].command_inout("State")
            if sta == PyTango.DevState.ON:
                tup = (sta, "Camera ready")
            elif sta == PyTango.DevState.MOVING:
                tup = (sta, "Camera taking images")
            elif sta == PyTango.DevState.FAULT:
                tup = (sta, "Camera in FAULT state")
            # +++
            elif sta == PyTango.DevState.OFF:
                tup = (sta, "Camera in OFF state")
            else:
                tup = (sta, "Camera in %s state" % repr(sta))
            # +++
            if self.isatty:
                print("EigerDectris.stateOne, %s, %s" %
                      (self.tango_device[ind - 1], repr(tup)))
            return tup
        else:
            if self.isatty:
                print("EigerDectris, %s is not available" %
                      (self.tango_device[ind - 1]))

    def PreReadAll(self):
        pass

    def PreReadOne(self, ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        if self.isatty:
            print("EigerDectris.ReadOne, %s, status %s " %
                  (self.tango_device[ind - 1],
                   repr(self.proxy[ind - 1].status())))
        #
        #
        #
        if self.proxy[ind - 1].status() == 'idle' and \
           self.proxy_fw[ind - 1].state() == PyTango.DevState.MOVING:
            if self.isatty:
                print("EigerDectris.ReadOne, disarm, %s" %
                      self.tango_device[ind - 1])
            self.proxy[ind - 1].command_inout("Disarm")
            startTime = time.time()
            while self.proxy_fw[ind - 1].state() != PyTango.DevState.ON:
                time.sleep(TIME_SLEEP)
                if (time.time() - startTime) > 2:
                    print("EigerDectris.ReadOne: "
                          "filewriter does not become ON")
                    return
            while self.proxy_fw[ind - 1].status() != 'ready':
                time.sleep(TIME_SLEEP)
                if (time.time() - startTime) > 2:
                    print("EigerDectris.ReadOne: "
                          "filewriter does not become ready")
                    return

        # The EigerDectris return an Image in type encoded
        tmp_value = [(-1,), (-1,)]
        if self.device_available[ind - 1] == 1:
            return tmp_value
        return

    def PreStartAll(self):
        pass

    def PreStartOne(self, ind, value):
        return True

    def StartOne(self, ind, position=None):
        if self.isatty:
            print("EigerDectris.StartOne, %s, state %s" %
                  (self.tango_device[ind - 1],
                   repr(self.proxy[ind - 1].state())))
        #
        # after the detector has been armed, the filewrite has to be MOVING
        #
        if self.proxy_fw[ind - 1].state() != PyTango.DevState.MOVING:
            if self.isatty:
                print("EigerDectris.StartOne, "
                      "filewriter not MOVING, sending arm()")
            if self.proxy[ind - 1].state() != PyTango.DevState.ON:
                print("EigerDectris.StartOne: "
                      "FW != MOVING -> detector state should be ON, return")
                return
            if self.proxy[ind - 1].status() != 'idle':
                print("EigerDectris.StartOne: "
                      "FW != MOVING -> detector status should be 'idle',"
                      " return")
                return
            if self.isatty:
                print("EigerDectris.StartOne, arm()")
            self.proxy[ind - 1].command_inout("Arm")
            startTime = time.time()
            while self.proxy[ind - 1].status() != 'ready':
                time.sleep(TIME_SLEEP)
                if (time.time() - startTime) > 2:
                    print("EigerDectris.StartOne: "
                          "detector does not become 'ready'")
                    return
            if self.isatty:
                print("EigerDectris.StartOne, status is 'ready', OK")
            startTime = time.time()
            while self.proxy_fw[ind - 1].state() != PyTango.DevState.MOVING:
                time.sleep(TIME_SLEEP)
                if (time.time() - startTime) > 2:
                    print("EigerDectris.StartOne: "
                          "filewrite does not become MOVING")
                    return
            if self.isatty:
                print("EigerDectris.StartOne, state_fw is MOVING, OK")

        if self.isatty:
            print("EigerDectris.StartOne, calling Trigger(), state %s" %
                  self.proxy[ind - 1].state())

        self.proxy[ind - 1].command_inout("Trigger")
        #
        # was necessary because Eiger1@haspp10lab
        #
        # while self.proxy[ind - 1].status() != 'acquire':
        #    time.sleep(TIME_SLEEP)
        #    if (time.time() - startTime) > 2:
        #        print("EigerDectris.StartOne: "
        #                 "detector does not become 'acquire'")
        #        return

        if self.isatty:
            print("EigerDectris.StartOne, after Trigger(), status %s" %
                  self.proxy[ind - 1].status())

    def AbortOne(self, ind):
        pass

    #
    # +++
    # 'repetitions' and 'latency_time' need the '= None' because
    # the interface changes from Python2.7 to Python3
    #
    def LoadOne(self, ind, value, repetitions=None, latency_time=None):
        if self.isatty:
            print("EigerDectris.loadOne, %s, countTime %g, state %s" %
                  (self.tango_device[ind - 1], value,
                   str(self.proxy[ind - 1].state())))
        self.proxy[ind - 1].write_attribute("CountTime", value)
        self.proxy[ind - 1].write_attribute("CountTimeInte", value)
        #
        # to set NbTriggers here interfers with actions we do in the hooks.
        #
        #
        # self.proxy[ind - 1].write_attribute("NbTriggers", 1)
        if self.isatty:
            print("EigerDectris.loadOne DONE, %s, state %s" %
                  (self.tango_device[ind - 1],
                   str(self.proxy[ind - 1].state())))

    def GetAxisExtraPar(self, ind, name):
        if self.device_available[ind - 1]:
            if name == "CountTime":
                return self.proxy[ind - 1].read_attribute("CountTime").value
            elif name == "CountTimeInte":
                return self.proxy[ind - 1].read_attribute(
                    "CountTimeInte").value
            elif name == "NbTriggers":
                return self.proxy[ind - 1].read_attribute("NbTriggers").value
            elif name == "TriggerMode":
                return self.proxy[ind - 1].read_attribute("TriggerMode").value
            elif name == "TangoDevice":
                tango_device = self.node + ":" + str(self.port) + "/" + \
                    self.proxy[ind - 1].name()
                return tango_device
            elif name == "SettleTime":
                return self.SettleTime[ind - 1]

    def SetAxisExtraPar(self, ind, name, value):
        if self.device_available[ind - 1]:
            if name == "CountTime":
                self.proxy[ind - 1].write_attribute("CountTime", value)
            elif name == "CountTimeInte":
                self.proxy[ind - 1].write_attribute("CountTimeInte", value)
            elif name == "NbTriggers":
                self.proxy[ind - 1].write_attribute("NbTriggers", value)
            elif name == "TriggerMode":
                self.proxy[ind - 1].write_attribute("TriggerMode", value)

    def SendToCtrl(self, in_data):
        #        print "Received value =", in_data
        return "Nothing sent"

    def __del__(self):
        print("PYTHON -> EigerDectrisCtrl dying")


#
db = None


def findDB(tangoHost=None):
    '''
    handle these cases:
      - tangoHost == None: use TANGO_HOST DB
      - tangoHost == "haspp99:10000" return db link
      - tangoHost == "haspp99" insert 100000 and return db link
    '''
    if tangoHost is None:
        global db
        if db is None:
            db = PyTango.Database()
        return db

    #
    # unexpeccted: tango://haspe212oh.desy.de:10000/motor/dummy_mot_ctrl/1
    #
    if tangoHost.find('tango://') == 0:
        PyTango.Except.throw_exception(
            "n.n.", "bad TANGO_HOST syntax %s" % tangoHost,
            "EigerDectris.findDB")
    #
    # tangHost "haspp99:10000"
    #
    lst = tangoHost.split(':')
    if len(lst) == 2:
        return PyTango.Database(lst[0], lst[1])
    #
    # tangHost "haspp99"
    #
    elif len(lst) == 1:
        return PyTango.Database(lst[0], "10000")
    else:
        return None


def getDeviceNamesByClass(className, tangoHost=None):
    '''Return a list of all devices of a specified class,
        'DGG2' -> ['p09/dgg2/exp.01', 'p09/dgg2/exp.02']
    '''
    srvs = getServerNameByClass(className, tangoHost)
    argout = []

    db = findDB(tangoHost)
    if not db:
        return None

    for srv in srvs:
        lst = db.get_device_name(srv, className).value_string
        for i in range(0, len(lst)):
            argout.append(lst[i])
    return argout


def getServerNameByClass(argin, tangoHost=None):
    '''Return a list of servers containing the specified class '''

    db = findDB(tangoHost)

    srvs = db.get_server_list("*").value_string

    argout = []

    for srv in srvs:
        classList = db.get_server_class_list(srv).value_string
        for clss in classList:
            if clss == argin:
                argout.append(srv)
                break
    return argout


#
def getDeviceProperty(devName, propName, tangoHost=None):
    '''
    devName: p10/eigerfilewriter/lab.01, propName: EigerDevice
    return: ['p10/eigerdectris/lab.01']
    '''

    db = findDB(tangoHost)
    if not db:
        return None

    dct = db.get_device_property(devName, [propName])

    return list(dct[propName])


if __name__ == "__main__":
    obj = TwoDController('test')
