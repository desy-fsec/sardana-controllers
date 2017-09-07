import PyTango
import taurus
from sardana import State
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.controller import (TriggerGateController, Type, Description,
                                     DefaultValue, Access, DataAccess, Memorize, 
                                     Memorized, NotMemorized)

from sardana.tango.core.util import from_tango_state_to_state

ReadWrite = DataAccess.ReadWrite
ReadOnly = DataAccess.ReadOnly

CHANNELDEVNAMES_DOC = ('Comma separated Ni660XCounter Tango device names ',
                       ' configured with COPulseChanTime as applicationType.',
                       ' The 1st name in the list will be used by the 1st',
                       ' axis, etc.')
START_TRIGGER_SOURCE_DOC = ('Start trigger source, normally is the source '
                          'channel, the default value is /Dev1/PFI39 channel '
                            '0 source')
START_TRIGGER_TYPE_DOC = ('Trigger type, by default is DigEdge')

def eval_state(state):
    """This function converts Ni660X device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return State.Moving
    elif state == PyTango.DevState.STANDBY:
        return State.On
    else:
        return from_tango_state_to_state(state)

class Ni660XTriggerGateController(TriggerGateController):

    MaxDevice = 32
    min_time = 25e-7

    ctrl_properties = {
        'channelDevNames': {
            Type: str,
            Description: CHANNELDEVNAMES_DOC
        },
        'startTriggerSource':{
            Type: str,
            Description: START_TRIGGER_SOURCE_DOC,
            DefaultValue:"/Dev1/PFI39"
        },
        "startTriggerType" :{
            Type: str,
            Description: START_TRIGGER_TYPE_DOC,
            DefaultValue: "DigEdge"}
    }
    axis_attributes = {
        "slave": {
            Type: bool,
            Access: ReadWrite,
            Memorize: Memorized
        },
        "retriggerable": {
            Type: bool,
            Access: ReadWrite,            
            Memorize: Memorized
        },
        "extraInitialDelayTime": {
            Type: float,
            Access: ReadWrite,
            Memorize: Memorized,
            DefaultValue: 0
        },
    }

    # relation between state and status  
    state_to_status = {
        State.On: 'Device finished generation of pulses',
        State.Standby: 'Device is standby',
        State.Moving: 'Device is generating pulses'
    }

    def __init__(self, inst, props, *args, **kwargs):
        """
        Construct the TriggerGateController and prepare the controller
        properties.
        """
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self.channel_names = self.channelDevNames.split(",")
        self.channels = {}
        self.slave = False
        self.retriggerable = False
        self.extraInitialDelayTime = 0


    def AddDevice(self, axis):
        """
        Add axis to the controller, basically creates a taurus device of
        the corresponding channel.
        """
        channel_name = self.channel_names[axis - 1]
        try:
            self.channels[axis] = PyTango.DeviceProxy(channel_name)
        except Exception, e:
            msg = 'Could not create taurus device: %s, details: %s' %\
                  (channel_name, e)
            self._log.debug(msg)

    def DeleteDevice(self, axis):
        """
        Remove axis from the controller, basically forgets about the taurus
        device of the corresponding channel.
        """
        self.channels.pop(axis)

    def _getState(self, axis):
        channel = self.channels[axis]    
        state = channel.read_attribute('State').value
        if state == PyTango.DevState.RUNNING:
           return State.Moving
        elif state == PyTango.DevState.STANDBY:
           return State.On
        else:
           return from_tango_state_to_state(state)
 
    def SynchOne(self, axis, configuration):
        """
        Set axis configuration.
        """

        group = configuration[0]
        delay = group[SynchParam.Delay][SynchDomain.Time]
        active = group[SynchParam.Active][SynchDomain.Time]
        total = group[SynchParam.Total][SynchDomain.Time]
        passive = total - active
        repeats = group[SynchParam.Repeats]

        # TODO: write of some attrs require that the device is STANDBY
        # For the moment Sardana leaves the TriggerGate elements in the 
        # state that they finished the last generation. In case of 
        # Ni660XCounter, write of some attributes require the channel 
        # to be in STANDBY state. Due to that we stop the channel.
        
        channel = self.channels[axis]          
        if self._getState(axis) is State.On:
            channel.stop()
                  
        if passive < self.min_time:
            passive = self.min_time

        channel.write_attribute("HighTime", active)
        channel.write_attribute("LowTime", passive)
        channel.write_attribute("SampPerChan", long(repeats))
                     
        timing_type = 'Implicit'
        
        # Check if the axis trigger generator needs a master trigger to start        
        if self.slave:
            startTriggerSource = self.startTriggerSource
            startTriggerType = self.startTriggerType
            # If the trigger is manage by external trigger the delay time should be 0
            delay = 0        
            # The trigger should be retriggerable by external trigger?
            if self.retriggerable:
                channel.write_attribute('retriggerable',1)
                timing_type = 'OnDemand'                
        else:
            startTriggerSource = 'None'
            startTriggerType = 'None'            
                                
        channel.write_attribute("StartTriggerSource", startTriggerSource)
        channel.write_attribute("StartTriggerType", startTriggerType)
        delay = delay + self.extraInitialDelayTime
        self.extraInitialDelayTime = 0
        channel.write_attribute("InitialDelayTime", delay)
        channel.write_attribute('SampleTimingType',timing_type)
        
    def PreStartOne(self, axis, value=None):
        """
        Prepare axis for generation.
        """
        self._log.debug('PreStartOne(%d): entering...' % axis)
 
        self._log.debug('PreStartOne(%d): leaving...' % axis)
        return True

    def StartOne(self, axis):
        """
        Start generation - start the specified channel.
        """
        self._log.debug('StartOne(%d): entering...' % axis)
        channel = self.channels[axis]
        channel.Start()
        self._log.debug('StartOne(%d): leaving...' % axis)

    def StateOne(self, axis):
        """
        Get state from the channel and translate it to the Sardana state
        """
        self._log.debug('StateOne(%d): entering...' % axis)
        
        sta = self._getState(axis)
        status = self.state_to_status[sta]
        self._log.debug('StateOne(%d): returning (%s, %s)'\
                             % (axis, sta, status))
        return sta, status

    def AbortOne(self, axis):
        """
        Abort generation - stop the specified channel
        """
        self._log.debug('AbortOne(%d): entering...' % axis)
        channel = self.channels[axis]
        channel.Stop()
        self._log.debug('AbortOne(%d): leaving...' % axis)

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar(%d, %s) entering..." % (axis, name))
        name = name.lower()
        if name == "slave":
            v = self.slave
        elif name == 'retriggerable':
            self.rettrigerable =  self.channels[axis].read_attribute('retriggerable').value
            v = self.retriggerable
        elif name == 'extrainitialdelaytime':
            v = self.extraInitialDelayTime
        return v

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar(%d, %s, %s) entering..." %
                        (axis, name, value))
        name = name.lower()
        if name == "slave":
            self.slave = value
        elif name == 'retriggerable':
            if self._getState(axis) is State.On:
                self.channels[axis].stop()
            self.retriggerable = value
            self.channels[axis].write_attribute('retriggerable', value)
        elif name == 'extrainitialdelaytime':
            self.extraInitialDelayTime = value