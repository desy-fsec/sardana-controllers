#!/usr/bin/env python

import PyTango

from sardana import State, DataAccess
from sardana.pool.controller import ZeroDController
from sardana.pool.controller import Type, Access, Description

class TiltZeroDController(ZeroDController):

    gender = "0D controller"
    model  = "MD900 Tiltmeter"
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    MaxDevice = 3

    # The serial port device to connect to
    ctrl_properties = {
        'SerialDevice': {
            Type : str,
            Description : 'The serial port device to connect to',
            Access : DataAccess.ReadOnly
        }
    }

    axis_attributes = {
        'step_per_unit' : {
                Type         : float,
                Description  : 'Factor to convert to user units',
                Access : DataAccess.ReadWrite,
        },
        'offset' : {
                Type         : float,
                Description  : 'Offset in user units',
                Access : DataAccess.ReadWrite,
        },
        'current_raw_value' : {
                Type         : float,
                Description  : 'Current raw value from the hardware',
                Access : DataAccess.ReadOnly,
        }
    }

    def __init__(self, inst, props, *args, **kwargs):
        ZeroDController.__init__(self, inst, props, *args, **kwargs)

        #Initialize values
        self.values = [0.0, 0.0, 0.0]
        self.steps_per_unit = [1.0, 1.0, 1.0]
        self.offsets = [0.0, 0.0, 0.0]

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
        self.values = answer.strip("$ \r\n").split(",")
        for i in range(self.MaxDevice):
            self.values[i] = float(self.values[i])

    def ReadOne(self,axis):
        return self.values[axis-1]/self.steps_per_unit[axis-1] + self.offsets[axis-1]

    def GetAxisExtraPar(self, axis, parameter):
        if parameter == 'step_per_unit':
            return self.steps_per_unit[axis-1]
        elif parameter == 'offset':
            return self.offsets[axis-1]
        elif parameter == 'current_raw_value':
            self.ReadAll()
            return self.values[axis-1]

    def SetAxisExtraPar(self, axis, parameter, value):
        if parameter == 'step_per_unit':
            self.steps_per_unit[axis-1] = value
        elif parameter == 'offset':
            self.offsets[axis-1] = value
