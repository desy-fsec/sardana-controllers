#!/usr/bin/env python
import datetime
import numpy
import PyTango, taurus
from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController, Memorize, NotMemorized
from sardana.pool.controller import Type, Access, Description, MaxDimSize
from sardana.tango.core.util import from_tango_state_to_state

ReadWrite = DataAccess.ReadWrite
ReadOnly = DataAccess.ReadOnly

def evalState(state):
    """This function converts Ni660X device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return State.Moving
    elif state == PyTango.DevState.STANDBY:
        return State.On
    else:
        return from_tango_state_to_state(state)


class Ni660XPositionCTCtrl(CounterTimerController):
    "This class is the Ni600X position capture Sardana CounterTimerController"

    MaxDevice = 32
    
    ctrl_properties = { "channelDevNames" : { Type : str, Description : "Comma separated Ni660xCounter device names"} }
    
    axis_attributes = {     "channelDevName" : { Type : str,      Access : ReadOnly },
                         "sampleClockSource" : { Type : str,      Access : ReadWrite, Memorize : NotMemorized },
                     "dataTransferMechanism" : { Type : str,      Access : ReadWrite, Memorize : NotMemorized },
                       "pulsesPerRevolution" : { Type : float,    Access : ReadWrite, Memorize : NotMemorized }, 
                           "initialPosition" : { Type : float,    Access : ReadWrite, Memorize : NotMemorized }, 
                             "zIndexEnabled" : { Type : bool,     Access : ReadWrite, Memorize : NotMemorized }, 
                                      "sign" : { Type : int,      Access : ReadWrite, Memorize : NotMemorized }, 
                              "nrOfTriggers" : { Type : long,     Access : ReadWrite, Memorize : NotMemorized },
                               "triggerMode" : { Type : str,      Access : ReadWrite, Memorize : NotMemorized }, #to be replaced by mnt grp conf
                         "samplingFrequency" : { Type : float,    Access : ReadWrite, Memorize : NotMemorized }, #to be removed, not generic
                           "acquisitionTime" : { Type : float,    Access : ReadWrite, Memorize : NotMemorized }, #to be removed, not generic
                                      "data" : { Type : (float,), Access : ReadOnly, MaxDimSize : (1000000,)}
                       }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.channelDevNamesList = self.channelDevNames.split(",")
        self.channels = {}
        self.attributes = {}

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("SetAxisExtraPar() entering...")
        name = name.lower()
        if name == "channeldevname":
            v = self.channelDevNamesList[axis-1]
        elif name == "sampleclocksource":
            v = self.channels[axis]["SampleClockSource"].value
        elif name == "datatransfermechanism":
            v = self.channels[axis]["DataTransferMechanism"].value
        elif name == "units":
            v = self.channels[axis]["Units"].value
        elif name == "pulsesperrevolution":
            v = self.channels[axis]["PulsesPerRevolution"].value
        #temporarily using internal algorithm
        #elif name == "initialposition":
        #    v = self.channels[axis]["InitialPos"].value
        elif name == "zindexenabled":
            v = self.channels[axis]["ZIndexEnabled"].value
        elif name == "data":
            s = datetime.datetime.now()
            self._log.debug("GetAxisExtraPar() data: start time = %s" % s.isoformat())
            rawData = self.channels[axis]["PositionBuffer"].value
            if self.attributes[axis]["sign"] == -1:
                rawDataNumpy = numpy.array(rawData)
                v = rawDataNumpy * -1
            else:
                v = rawData
            v = v + self.attributes[axis]["initialposition"]
            e = datetime.datetime.now()
            self._log.debug("GetAxisExtraPar() data: end time = %s" % e.isoformat())
            t = e - s
            self._log.debug("GetAxisExtraPar() data: total = %d" % t.seconds)
        elif name == "nroftriggers":
            v = self.channels[axis]["SampPerChan"].value
        elif name == "triggermode":
            raw = self.channels[axis]["SampleTimingType"]
            if raw == "SampleClk":
                v = "gate"
            else:
                v = "soft"
        elif name == "samplingfrequency":
            v = float("nan")
        elif name == "acquisitiontime":
            v = float("nan")
        else:
            v = self.attributes[axis][name]
            
        return v

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar() entering...")
        name = name.lower()  
        if name == "sampleclocksource":
            self.channels[axis]["SampleClockSource"] = value
        elif name == "datatransfermechanism":
            self.channels[axis]["DataTransferMechanism"] = value
        elif name == "units":
            self.channels[axis]["Units"] = value
        elif name == "pulsesperrevolution":
            self.channels[axis]["PulsesPerRevolution"] = value
        #temporarily using internal algorithm
        #elif name == "initialposition":
        #    self.channels[axis]["InitialPos"] = value
        elif name == "zindexenabled":
            self.channels[axis]["ZIndexEnabled"] = value
        elif name == "nroftriggers":
            #self.channels[idx]["SampPerChan"] = value # due to bug in taurus remporarily using PyTango
            self.channels[axis].getHWObj().write_attribute("SampPerChan", long(value))
        elif name == "triggermode":
            if value == "gate":
                self.channels[axis]["SampleTimingType"] = "SampClk"
            else:
                pass
        elif name == "samplingfrequency":
            pass
        elif name == "acquisitiontime":
            pass
        else:
            self.attributes[axis][name] = value

    def AddDevice(self, axis):
        self.channels[axis] = taurus.Device(self.channelDevNamesList[axis-1])        
        self.channels[axis].set_timeout_millis(120000) #readount ot 60000 buffer takes aprox 10 seconds
        self.attributes[axis] = {"sign":1, "initialposition":0}

    def DeleteDevice(self, axis):
        self.channels.pop(axis)
        self.attributes.pop(axis)
        
    def PreStateAll(self):
        pass

    def PreStateOne(self, axis):
        pass

    def StateAll(self):
        pass

    def StateOne(self, axis):
        if self.channels[axis] == None:
            self.sta = State.Init
            self.status = '''Channel configuration is not finished. "channelDevName" attribute is not specified.'''
        else:
            rawState = self.channels[axis].State()
            self.sta = evalState(rawState)
            self.status = ""
        return self.sta, self.status

    def PreReadAll(self):
        self.spectrum = None

    def PreReadOne(self,axis):
        pass

    def ReadAll(self):
        self._log.debug("ReadAll(): entering...")
        self._log.debug("ReadAll(): leaving...")

    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): entering..." % axis)
        return 0

    def PreStartAllCT(self):
        pass

    def PreStartOneCT(self, axis):
        return True

    def StartOneCT(self, axis):
        pass

    def StartAllCT(self):
        self._log.debug("StartAllCT(): entering...")
        self._log.debug("StartAllCT(): leaving...")

    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(): entering...")
        self._log.debug("LoadOne(): leaving...")

    def AbortOne(self, axis):
        pass
    
    def SendToCtrl(self, cmd):
        cmd = cmd.lower()
        words = cmd.split(" ")
        if len(words) == 2:
            action = words[0]
            axis = int(words[1])
            if action == "start":
                self._log.debug("SendToCtrl(%s): starting channel %d", cmd, axis)
                self.channels[axis].Start()
                return "Channel %d started" % axis
            elif action == "stop":
                self._log.debug("SendToCtrl(%s): stopping channel %d", cmd, axis)
                self.channels[axis].Stop()
                return "Channel %d stopped" % axis
            else: 
                return "Unknown command"
