import time, logging
import PyTango, taurus

from sardana import pool, State
from sardana.pool.controller import CounterTimerController, Memorized

class Ni660XCoTiCtrl(CounterTimerController):

    MaxDevice = 32

    axis_attributes = {"channelDevName":{ "Type":"PyTango.DevString", "R/W Type": "PyTango.READ_WRITE", "memorized":Memorized}}
    
    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst), repr(props))
        self.attributes = {}
        self.channels = {}
        self.acqChannels = []
        self.values = {}
        self.state = State.Unknown
        self.status = ""

    def AddDevice(self, axis):
        self._log.debug("AddOne(%d): Entering...", axis)
        self.attributes[axis] = {"channeldevname":""}
        self.channels[axis] = None
        self._log.debug("AddOne(%d): Leaving...", axis)

    def PreStateOne(self, axis):
        pass

    def StateAll(self):
        self._log.debug("StateAll(): Entering...")
        #checking if acq was started
        channel = self.channels[1]
        if channel is None:
            self.state = State.Unknown
            self.status = "Unable to read state. Check if channelDevName attribute is set."
        else:
            self.state = channel.state()
            self.status = channel.status()
        
        #in case of finished gate reading channel values
        if len(self.acqChannels) > 0 and self.state == State.On:
            self._log.debug("Acquisition has finished. Collecting data...")
            for axis in self.acqChannels:
                channel = self.channels[axis]
                if channel is None:
                    raise Exception("Counter of axis %d does not have channelDevName set." % axis)
                self.values[axis] = channel.getAttribute("Value").read().value
                channel.stop()
            #stopping master channel
            self.channels[1].stop()
            self.acqChannels = []
        self._log.debug("StateAll(): Leaving...")

    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        self._log.debug("StateOne(%d): Leaving...", axis)
        return (self.state, self.status)
      
    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        channel = self.channels[axis]
        if axis == 1:
            value = channel.getAttribute("HighTime").read().value
        else:
            value = self.values.get(axis, 0)
        self._log.debug("ReadOne(%d): Returning %s...", axis, repr(value))
        return value
            
    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        self.channels[axis].stop()

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
            self.acqChannels.append(axis)
            self.values[axis] = 0
            channel.start()
        self._log.debug("StartOneCT(%d): Leaving..." % axis)

    def StartAllCT(self):
        self._log.debug("StartAllCT(): Entering...")
        channel = self.channels[1]
        if channel is None:
            raise Exception("Counter of axis %d does not have channelDevName set." % 1)
        channel.start()
        self._log.debug("StartAllCT(): Leaving...")

    def PreLoadOne(self, axis, value):
        self._log.debug("PreLoadOne(%d, %f): Entering...", axis, value)
        channel = self.channels[axis]
        if channel is None:
            raise Exception("Counter of axis %d does not have channelDevName set." % axis)
        #channel has to be stopped before applying new configuration
        channel.stop() 
        self._log.debug("PreLoadOne(%d, %f): Leaving...", axis, value)
        return True
        
    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(%d, %f): Entering...", axis, value)
        channel = self.channels[axis]
        if channel is None:
            raise Exception("Counter of axis %d does not have channelDevName set." % axis)
        channel.getAttribute("HighTime").write(value)
        self._log.debug("LoadOne(%d, %f): Leaving...", axis, value)

    def GetExtraAttributePar(self, axis, name):
        """Get extra attribute.

        :param axis: (int) axis nr to get an extra attribute
        :param name: (string) attribute name to retrieve

        :return: value of the attribute
        """
        return self.attributes[axis][name.lower()]

    def SetExtraAttributePar(self, axis, name, value):
        """Set extra attribute.

        :param axis: (int) axis nr to set an extra attribute
        :param name: (string) attribute name to retrieve
        :param value: an extra attribute value to be set

        """
        name = name.lower()
        self.attributes[axis][name] = value
        if name == "channeldevname":
            self.channels[axis] = taurus.Device(value)
