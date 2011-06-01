#!/usr/bin/env python

import PyTango
from pool import ZeroDController

class TiltZeroDController(ZeroDController):

    ## The serial port device to connect to
    class_prop = {'SerialDevice':{'Type':'PyTango.DevString','Description':'The serial port device to connect to'}}
    MaxDevice = 3

    gender = "0D controller"
    model  = "MD900 Tiltmeter"
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    def __init__(self,inst,props):
        ZeroDController.__init__(self,inst, props)

        #Initialize values
        self.values = [0, 0, 0]

        #connect to serial device
        self.dev = PyTango.DeviceProxy(self.SerialDevice)

        #following code commented: we assume the tiltmeter is already configured
        #disable command echo of the tiltmeter
        #self.dev.DevSerWriteString("*9900XY-SE")
        #self.dev.DevSerWriteChar([10])

        #set maximum data rate of the tiltmeter
        #self.dev.DevSerWriteString("*9900XYC0")
        #self.dev.DevSerWriteChar([10])

        #flush input until we get data
        #answer = self.dev.DevSerReadLine()
        #while not answer[0] == "$":
            #answer = self.dev.DevSerReadLine()

    def AddDevice(self,ind):
        pass

    def DeleteDevice(self,ind):
        pass

    def StateOne(self,ind):
        sta, status = PyTango.DevState.ON, "OK"
        return (sta,status)

    def ReadAll(self):
        #clean input before reading, to make sure we read the latest data
        self.dev.DevSerFlush(0)
        answer = self.dev.DevSerReadLine()
        while not answer[0] == "$":
            answer = self.dev.DevSerReadLine()
        print "answer", answer
        self.values = answer.strip("$ \r\n").split(",")
        for i in range(self.MaxDevice):
            self.values[i] = float(self.values[i])

    def ReadOne(self,ind):
        return self.values[ind-1]
