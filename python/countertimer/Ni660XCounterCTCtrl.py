#!/usr/bin/env python

import datetime
import numpy
import PyTango, taurus
from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController, Memorize, Memorized, NotMemorized
from sardana.pool.controller import Type, Access, DataAccess, Description, MaxDimSize
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


class Ni660XCounterCTCtrl(CounterTimerController):
    """This class is the Ni600X counter Sardana CounterTimerController.
    It can work in step and continuous scan mode. """

    MaxDevice = 32
    
    ctrl_properties = { "channelDevNames" : { Type : str, Description : "Comma separated Ni660xCounter device names, first must be a timer channel"} }
    
    axis_attributes = {     "channelDevName" : { Type : str,      Access : ReadOnly },
                         "sampleClockSource" : { Type : str,      Access : ReadWrite, Memorize : NotMemorized },
                     "dataTransferMechanism" : { Type : str,      Access : ReadWrite, Memorize : NotMemorized },
                              "stepsPerUnit" : { Type : float,    Access : ReadWrite, Memorize : NotMemorized }, 
                              "nrOfTriggers" : { Type : long,     Access : ReadWrite, Memorize : NotMemorized },
                               "triggerMode" : { Type : str,      Access : ReadWrite, Memorize : NotMemorized }, #to be replaced by mnt grp conf
                         "samplingFrequency" : { Type : float,    Access : ReadWrite, Memorize : NotMemorized }, #to be removed, not generic
                           "acquisitionTime" : { Type : float,    Access : ReadWrite, Memorize : NotMemorized }, #to be removed, not generic
                                      "data" : { Type : (float,), Access : ReadOnly, MaxDimSize : (1000000,)}
                       }
    
    count = 0

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.channelDevNamesList = self.channelDevNames.split(",")
        self.channels = {}
        self.acqChannels = {}
        self.attributes = {}
        self.values = {}
        self.state = State.Unknown
        self.status = ""
        
    def AddDevice(self, axis):
        self.channels[axis] = taurus.Device(self.channelDevNamesList[axis-1])
        #self.channels[axis].set_timeout_millis(20000) #readout of 60000 buffer takes aprox 20ms, default timeout value should be enough
        self.attributes[axis] = {}

    def DeleteDevice(self, axis):
        self.channels.pop(axis)
        self.attributes.pop(axis)

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar() entering...")
        name = name.lower()
        
        if name == "channeldevname":
            v = self.channelDevNamesList[axis-1]
        if name == "sampleclocksource":
            v = self.channels[axis].getAttribute("SampleClockSource").read().value
        elif name == "datatransfermechanism":
            v = self.channels[axis].getAttribute("DataTransferMechanism").read().value
        elif name == "stepsperunit":
            v = self.channels[axis].getAttribute("PulsesPerRevolution").read().value
        elif name == "data":
            s = datetime.datetime.now()
            self._log.debug("GetAxisExtraPar() data: start time = %s" % s.isoformat())
            raw = self.channels[axis].getAttribute("CountBuffer").read().value
            numRaw = numpy.array(raw)
            v = list(numRaw[1:] - numRaw[:-1])
            v.insert(0,raw[0])
            e = datetime.datetime.now()
            self._log.debug("GetAxisExtraPar() data: end time = %s" % e.isoformat())
            t = e - s
            self._log.debug("GetAxisExtraPar() data: total = %d" % t.seconds)
        elif name == "nroftriggers":
            v = self.channels[axis].getAttribute("SampPerChan").read().value
        elif name == "triggermode":
            raw = self.channels[axis].getAttribute("SampleTimingType").read().value
            if raw == "SampleClk":
                v = "gate"
            else:
                v = "soft"
        elif name == "samplingfrequency":
            v = float("nan")
        elif name == "acquisitiontime":
            v = float("nan")        
            
        return v

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar() entering...")
        name = name.lower()
        if name == "sampleclocksource":
            self.channels[axis].getAttribute("SampleClockSource").write(value)
            #self.channels[axis].getHWObj().write_attribute("SampleClockSource", value)
        elif name == "datatransfermechanism":
            self.channels[axis].getAttribute("DataTransferMechanism").write(value)
        elif name == "stepsperunit":
            self.channels[axis].getAttribute("PulsesPerRevolution").write(value)
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
        
    def PreStateAll(self):
        pass

    def PreStateOne(self, axis):
        pass

    def StateAll(self):
        if len(self.acqChannels.keys()) > 0:
            channel = self.channels[1]
            if channel is None:
                self.state = State.Unknown
                self.status = "Unable to read state. Check if channelDevName attribute is set."
            else:
                self.state = channel.state()
                self.status = channel.status()
                self._log.debug("Channel 1 state is: %s" % repr(self.state))
        
            #in case of finished gate reading channel values
            if self.state == State.On:
                self._log.debug("Acquisition has finished. Collecting data...")
                for axis in self.acqChannels.keys():
                    channel = self.channels[axis]
                    if channel is None:
                        raise Exception("Counter of axis %d does not have channelDevName set." % axis)
                    self.values[axis] = channel.getAttribute("Count").read().value
                    channel.stop()
                #stopping master channel
                self.channels[1].stop()
                self.acqChannels = {}        
            
        self._log.debug("StateAll(): Leaving...")

    def StateOne(self, axis):
        #in case of continuous acquisition or step acquisition finished, asking directly devices
        if len(self.acqChannels.keys()) == 0:
            state = State.Init
            status = '''Channel configuration is not finished. "channelDevName" attribute is not specified.'''
            if self.channels[axis] != None:
                rawState = self.channels[axis].State()
                state = evalState(rawState)
                status = ""
            return state, status
        else:
            return self.state, self.status

    def PreReadAll(self):
        self.spectrum = None

    def PreReadOne(self,axis):
        pass

    def ReadAll(self):
        self._log.debug("ReadAll(): entering...")
        self._log.debug("ReadAll(): leaving...")

    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        channel = self.channels[axis]
        if axis == 1:
            value = channel.getAttribute("HighTime").read().value
        else:
            value = self.values.get(axis, 0)
        self._log.debug("ReadOne(%d): Returning %s...", axis, repr(value))
        return value

    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        self.values = {}
        self._log.debug("PreStartAllCT(): Leaving...")
        return True

    def PreStartOneCT(self, axis):
        self._log.debug("PreStartOneCT(%d): Entering..." % axis)
        if axis != 1:
            channel = self.channels[axis]
            if channel is None:
                raise Exception("Counter of axis %d does not have channelDevName set." % axis)
            channel.stop()            
        self._log.debug("PreStartOneCT(%d): Leaving..." % axis)
        return True

    def StartOneCT(self, axis):
        self._log.debug("StartOneCT(%d): Entering..." % axis)
        if axis != 1:
            channel = self.channels[axis]
            if channel is None:
                raise Exception("Counter of axis %d does not have channelDevName set." % axis)
            self.acqChannels[axis] = None
            self.values[axis] = 0
            channel.start()
        self._log.debug("StartOneCT(%d): Leaving..." % axis)

    def StartAllCT(self):
        self._log.debug("StartAllCT(): Entering...")
        channel = self.channels[1]
        if channel is None:
            raise Exception("Counter of axis %d does not have channelDevName set." % 1)
        channel.Start()
        self._log.debug("StartAllCT(): Leaving...")

    def PreLoadOne(self, axis, value):
        self._log.debug("PreLoadOne(%d, %f): Entering...", axis, value)
        channel = self.channels[axis]
        if channel is None:
            raise Exception("Counter of axis %d does not have channelDevName set." % axis)
        if channel.State() != PyTango.DevState.STANDBY: 
            channel.Stop() 
        self._log.debug("PreLoadOne(%d, %f): Leaving...", axis, value)
        return True
        
    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(%d, %f): Entering...", axis, value)
        channel = self.channels[axis]
        if channel is None:
            raise Exception("Counter of axis %d does not have channelDevName set." % axis)
        channel.getAttribute("HighTime").write(value)
        self._log.debug("LoadOne(%d, %f): Leaving...", axis, value)

    def AbortOne(self, axis):     
        channel = self.channels[axis]
        if channel.State() != PyTango.DevState.STANDBY:    
            channel.Stop()
    
    def SendToCtrl(self, cmd):
        cmd = cmd.lower()
        words = cmd.split(" ")
        ret = "Unknown command"
        if len(words) == 2:
            action = words[0]
            axis = int(words[1])
            if action == "pre-start":
                self._log.debug("SendToCtrl(%s): pre-starting channel %d", cmd, axis)                
                ret = "Nothing to do in pre-start"
            elif action == "start":
                self._log.debug("SendToCtrl(%s): starting channel %d", cmd, axis)
                self.channels[axis].Start()
                ret = "Channel %d started" % axis
            elif action == "pre-stop":
                self._log.debug("SendToCtrl(%s): pre-stopping channel %d", cmd, axis)
                ret = "Nothing to do in pre-stop"
            elif action == "stop":
                self._log.debug("SendToCtrl(%s): stopping channel %d", cmd, axis)
                self.channels[axis].Stop()
                ret = "Channel %d started" % axis
        return ret
                
