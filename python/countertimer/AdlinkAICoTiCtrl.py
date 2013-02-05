#!/usr/bin/env python

import PyTango
from sardana import State, DataAccess
from sardana.pool.controller import CounterTimerController
from sardana.pool.controller import Type, Access, Description, Memorize, NotMemorized
from sardana.tango.core.util import from_tango_state_to_state

def evalState(state):
    """This function converts Adlink device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return State.Moving
    elif state == PyTango.DevState.STANDBY:
        return State.On
    else:
        return from_tango_state_to_state(state)

class AdlinkAICoTiCtrl(CounterTimerController):
    """This class is the Sardana CounterTimer controller for the Adlink adc based counters.
    The only way to use this controller is to define up to 5 channels 
    and create a measurement group where the first channel is a master channel. 
    The Adlink card works in a way where acquisition for all channels is started only once 
    and in controller this is done when StartsAll() method was called for this controller, 
    only when PreStartOne() was called for master channel. 
    
    Configuration of Adlink card is done in LoadOne() method where size of acquisition buffer 
    is calculated from acquisition time and SampleRate property. 
    
    Value returned by a channggel is an average of buffer values. If you need also 
    standard deviation of these values you can read it from extra attribute SD right after reading 
    value of the channel. 
    If you need SD value in measurement group you have two options:
        1- Add one tango attribute counter per each SD and place it in a measurement group after 
            corresponding Adlink counter.
        2- Add an ExtraColumn with the attribute SD."""
    
    MaxDevice = 5
    class_prop = {'AdlinkAIDeviceName':{'Description' : 'AdlinkAI Tango device', 'Type' : 'PyTango.DevString'},
                  'SampleRate':{'Description' : 'SampleRate set for AIDevice','Type' : 'PyTango.DevLong'}}
    
    axis_attributes ={"SD": 
                        {Type : float,
                         Description : 'Standard deviation',
                         Access : DataAccess.ReadWrite
                        },
                      "FORMULA":
                        {Type : str,
                         Description : 'The formula to get the real value.\ne.g. "(VALUE/10)*1e-06"',
                         Access : DataAccess.ReadWrite
                        },
                      "SHAREDFORMULA":
                        {Type : bool,
                         Description : 'If you want to share the same formula for all the channels set it to true"',
                         Access : DataAccess.ReadWrite
                        },
                       #attributes added for continuous acqusition mode
                      "NrOfTriggers":
                        {Type : long,
                         Description : 'Nr of triggers',
                         Access : DataAccess.ReadWrite,
                         Memorize : NotMemorized
                        },
                      "SamplingFrequency":
                       {Type : float,
                        Description : 'Sampling frequency',
                        Access : DataAccess.ReadWrite,
                        Memorize : NotMemorized
                       },
                      "AcquisitionTime":
                       {Type : float,
                        Description : 'Acquisition time per trigger',
                        Access : DataAccess.ReadWrite,
                        Memorize : NotMemorized
                       },
                      "TriggerMode":
                       {Type : str,
                        Description : 'Trigger mode: soft or gate',
                        Access : DataAccess.ReadWrite,
                        Memorize : NotMemorized
                       },
                       "Data":
                       {Type : [float],
                        Description : 'Data buffer',
                        Access : DataAccess.ReadOnly
                       }
                      }


    def __init__(self, inst, props, *args, **kwargs):
        #        self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst), repr(props))


        self.sd = {}
        self.formulas = {}
        self.sharedFormula = {}
        self.contAcqChannels = {}
        self.master = None
        self.integrationTime = 0
        
        try:
            self.AIDevice = PyTango.DeviceProxy(self.AdlinkAIDeviceName)
        except PyTango.DevFailed, e:
            self._log.error("__init__(): Could not create a device proxy from following device name: %s.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        self.sd[axis] = 0
        self.formulas[axis] = 'value'
        self.sharedFormula[axis] = False
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        self.sd.pop(axis)
        self.formulas.pop(axis)
        self.sharedFormula.pop(axis)
        
    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        if self.AIDevice is None:
            return State.Fault
        try:
            self.state = self.AIDevice.state()
            if self.master is not None: #step scan point in progress
                if self.state == PyTango.DevState.ON: #acquisition finished, resetting master
                    self.master = None
            return (evalState(self.state), "AI DeviceProxy present.") 
        except Exception, e:
            self._log.error("StateOne(%d): Could not verify state of the device: %s.\nException: %s", 
                            axis, self.AdlinkAIDeviceName, e)
            return (State.Unknown, "AI DeviceProxy is not responding.")
        
    def PreReadOne(self, axis):
        self._log.debug("PreReadOne(%d): Entering...", axis)
        self.sd[axis] = 0
        
    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        state = self.AIDevice.state() 
        mean = 0
        if axis == 1:
            return self.integrationTime

        if state == PyTango.DevState.ON: 
            mean = self.AIDevice["C0%s_MeanLast" % (axis - 2)].value
            std = self.AIDevice["C0%s_StdDevLast" % (axis - 2)].value
            
            self.sd[axis] = std

            value = mean
            mean = eval(self.formulas[axis])

            self._log.debug("ReadOne(%d): mean=%f, sd=%f", 
                            axis, mean, std)
        return mean
            
    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        state = self.AIDevice.state()
        if state == PyTango.DevState.RUNNING:
            self.AIDevice.stop()
    
    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        self.axesToStart = []
        try:
            state = self.AIDevice.state()
            if state == PyTango.DevState.RUNNING:
                self.AIDevice.stop()
        except Exception, e:
            self._log.error("PreStartAllCT(): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def PreStartOneCT(self, axis):
        """Here we are counting which axes are going to be start, so later we can distinguish 
        if we are starting only the master channel."""
        self._log.debug("PreStartOneCT(%d): Entering...", axis)
        #self.axesToStart.append(axis) #I think this is not needed because you can not start only one channel.
        return True

    def StartAllCT(self):
        """Starting the acquisition is done only if before was called PreStartOneCT for master channel."""
        self._log.debug("StartAllCT(): Entering...")
        #if not (len(self.axesToStart) == 1 and self.axesToStart[0] == self.master):
        #    return
        try:
            self.AIDevice.start()
        except Exception, e:
            self._log.error("StartAllCT(): Could not start acquisition on the device: %s.\nException: %s", 
                            self.AdlinkAIDeviceName, e)
            raise
        
    def PreLoadOne(self, axis, value):
        """Here we are keeping a reference to the master channel, so later in StartAll() 
        we can distinguish if we are starting only the master channel."""
        self._log.debug("PreLoadOne(%d, %f): Entering...", axis, value)
        self.master = None
        return True
        
    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(%d, %f): Entering...", axis, value)
        self.master = axis
        self.integrationTime = value
        try:
            self.state = self.AIDevice.state()
            if self.state == PyTango.DevState.RUNNING or self.state == PyTango.DevState.ON:
                self.AIDevice.stop()
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            axis, value, self.AdlinkAIDeviceName, e)
            raise
        bufferSize = int(self.integrationTime * self.SampleRate)
        try:
            self.AIDevice['NumOfTriggers'] = 1
            self.AIDevice['TriggerInfinite'] = 0    
            self.AIDevice['SampleRate'] = self.SampleRate
            self.AIDevice['ChannelSamplesPerTrigger'] = bufferSize
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not configure device: %s.\nException: %s", self.AdlinkAIDeviceName, e)
            raise

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar(%d, %s): Entering...", axis, name)
        if name.lower() == "sd":
            return self.sd[axis]
        if name.lower() == "formula":
            return self.formulas[axis]
        if name.lower() == "sharedformula":
            return self.sharedFormula[axis]
        #attributes used for continuous acquisition
        if name.lower() == "samplingfrequency":
            freq = self.AIDevice["SampleRate"].value
            return float(freq)
        if name.lower() == "triggermode":
            mode = self.AIDevice["TriggerSources"].value 
            if mode == "SOFT":
                return "soft"
            if mode == "ExtD:+":
                return "gate"
        if name.lower() == "nroftriggers":
            nrOfTriggers = self.AIDevice["NumOfTriggers"].value
            return long(nrOfTriggers)
        if name.lower() == "acquisitiontime":
            acqTime = self.AIDevice["BufferPeriod"].value
            return acqTime
        if name.lower() == "data":
            values = self.AIDevice["C0%d_MeanValues" % (axis - 2)].value
            return values
        #if name.lower() == "data":
            #data = []
            #values = self.AIDevice["C0%d_ChannelValues" % (axis -2)].value
            #samplesPerTrigger = self.AIDevice["ChannelSamplesPerTrigger"].value
            #nrOfTriggers = self.AIDevice["NumOfTriggers"].value
            #for triggerNr in range(nrOfTriggers):
                #start = triggerNr * samplesPerTrigger
                #end = start + samplesPerTrigger
                #data.append(values[start:end])
            #return data



    def SetAxisExtraPar(self,axis, name, value):
        #self.set_extra_attribute_par(axis, name, value) #todo Ask to zibi what is this!!
        if name.lower() == "formula":
            self.formulas[axis] = value

        if name.lower() == "sharedformula":
            self.sharedFormula[axis] = value
            if value:
                for i in self.formulas:
                    self.formulas[i] = self.formulas[axis]

        #attributes used for continuous acquisition
        if name.lower() == "samplingfrequency":
            maxFrequency = 500000
            if value == -1 or value > maxFrequency: 
                value = maxFrequency#-1 configures maximum frequency
            rate = long(value)
            self.AIDevice["samplerate"] = rate
        if name.lower() == "triggermode":
            if value == "soft":
                mode = "SOFT"
            if value == "gate":
                mode = "ExtD:+"
            self.AIDevice["TriggerSources"] = mode
        if name.lower() == "nroftriggers":
            self.AIDevice["NumOfTriggers"] = value
        if name.lower() == "acquisitiontime":
            self.AIDevice["BufferPeriod"] = value
    
    
    def SendToCtrl(self, cmd):
        cmd = cmd.lower()
        words = cmd.split(" ")
        ret = "Unknown command"
        if len(words) == 2:
            action = words[0]
            axis = int(words[1])
            if action == "pre-start":
                self._log.debug("SendToCtrl(%s): pre-starting channel %d", cmd, axis)
                self.contAcqChannels[axis] = None
                ret = "Channel %d appended to contAcqChannels" % axis
            elif action == "start":
                self._log.debug("SendToCtrl(%s): starting channel %d", cmd, axis)
                self.contAcqChannels.pop(axis)
                if len(self.contAcqChannels.keys()) == 0:
                    self.AIDevice.Start()
                    self._log.debug("SendToCtrl(%s): acquisition started", cmd)
                    ret = "Acquisition started"
                else:
                    ret = "Channel %d popped from contAcqChannels" % axis
            elif action == "pre-stop":
                self._log.debug("SendToCtrl(%s): pre-stopping channel %d", cmd, axis)
                self.contAcqChannels[axis] = None
                ret = "Channel %d appended to contAcqChannels" % axis
            elif action == "stop":
                self._log.debug("SendToCtrl(%s): stopping channel %d", cmd, axis)
                self.contAcqChannels.pop(axis)
                if len(self.contAcqChannels.keys()) == 0:
                    if self.AIDevice.State() != PyTango.DevState.STANDBY:
                        self.AIDevice.Stop()
                    self._log.debug("SendToCtrl(%s): acquisition stopped", cmd)
                    ret = "Acquisition stopped"
                else:
                    ret = "Channel %d popped from contAcqChannels" % axis
        return ret
