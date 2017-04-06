import PyTango
import taurus
from sardana import State
from sardana.pool.controller import (TriggerGateController, Type, Description)
from sardana.tango.core.util import from_tango_state_to_state

POSITIONDEVNAMES_DOC = ('Comma separated Ni660XCounter Tango device names ',
                       ' configured with CIAngEncoderChan as applicationType.',
                       ' They are used to generate (while changing position)',
                       ' base ticks for pulse train generation on another',
                       ' channel. The 1st name in the list will be used by the',
                       ' 1st axis, etc.')

GENERATORDEVNAMES_DOC = ('Comma separated Ni660XCounter Tango device names ',
                       ' configured with COPulseChanTicks as applicationType.',
                       ' They generate pulses based on base ticks coming from ',
                       ' another channel. The 1st name in the list will be',
                       ' used by the 1st axis, etc.')

def eval_state(state):
    """This function converts Ni660X device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return State.Moving
    elif state == PyTango.DevState.STANDBY:
        return State.On
    else:
        return from_tango_state_to_state(state)

ni6602 = {"ctr0": {"src": "PFI39", "gate": "PFI38", "out": "PFI36", "aux": "PFI37"},
          "ctr1": {"src": "PFI35", "gate": "PFI34", "out": "PFI32", "aux": "PFI33"},
          "ctr2": {"src": "PFI31", "gate": "PFI30", "out": "PFI28", "aux": "PFI29"},
          "ctr3": {"src": "PFI27", "gate": "PFI26", "out": "PFI24", "aux": "PFI25"},
          "ctr4": {"src": "PFI23", "gate": "PFI22", "out": "PFI20", "aux": "PFI21"},
          "ctr5": {"src": "PFI19", "gate": "PFI18", "out": "PFI16", "aux": "PFI17"},
          "ctr6": {"src": "PFI15", "gate": "PFI14", "out": "PFI12", "aux": "PFI13"},
          "ctr7": {"src": "PFI11", "gate": "PFI10", "out": "PFI8",  "aux": "PFI9"}}

class Ni660XPositionTriggerGateController(TriggerGateController):

    MaxDevice = 32

    ctrl_properties = {
        'positionDevNames': {
            Type: str,
            Description: POSITIONDEVNAMES_DOC
        },
        'generatorDevNames': {
            Type: str,
            Description: GENERATORDEVNAMES_DOC
        }
    }
    # relation one to one between the Ni660XCounter Tango device attributes
    # and the Sardana TriggerGate element attributes
    attribute_relations = {
        'offset': 'InitialDelayTicks',
        'active_interval': 'HighTicks',
        'passive_interval': 'LowTicks',
        'repetitions': 'SampPerChan'
    }
    # relation between state and status  
    state_to_status = {
        State.On: 'Device finished generation of pulses',
        State.Standby: 'Device is standby',
        State.Moving: 'Device is generating pulses'
    }


    def __init__(self, inst, props, *args, **kwargs):
        """Construct the TriggerGateController and prepare the controller
        properties.
        """
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self.position_names = self.positionDevNames.split(",")
        self.generator_names = self.generatorDevNames.split(",")
        if len(self.position_names) != len(self.generator_names):
            msg = 'Number of position and generator channels do not match'
            raise Exception(msg)
        self.attributes = {}
        self._ch_pos_attr = ['outputevenbehaviour', 'outputeventterminal',
                             'initialpos', 'zindexval', 'units', 'decoding',
                             'pulsesperrevolution']
        self._ch_gen_attr = ['repetitions', 'offset', 'active_period',
                             'passive_period']

    def AddDevice(self, axis):
        """Add axis to the controller, basically creates a taurus device of
        the corresponding channel.
        """
        position_name = self.position_names[axis - 1]
        self.attributes[axis] = tg = {}
        try:
            ch_position = tg['ch_position'] = taurus.Device(position_name)
            prop_dict = ch_position.get_property(['deviceName', 'counterName'])
            attr = ch_position.getAttribute('OutputEventTerminal')
            counter_name = ni6602.get(prop_dict.get('counterName')[0])
            device_name = prop_dict.get('deviceName')[0]
            chn_str = "/%s/%s" % (device_name, counter_name.get("out"))
            attr.write(chn_str)
        except Exception, e:
            msg = 'Could not create taurus device: %s, details: %s' %\
                  (position_name, e)
            self._log.debug(msg)
        generator_name = self.generator_names[axis - 1]
        try:
            ch_generator =tg['ch_generator'] = taurus.Device(generator_name)
            prop_dict = ch_generator.get_property('counterName')
            attr = ch_generator.getAttribute('SourceTerminal')
            attr.write(chn_str)

        except Exception, e:
            msg = 'Could not create taurus device: %s, details: %s' %\
                  (generator_name, e)
            self._log.debug(msg)
        tg['resolution'] = .25

    def DeleteDevice(self, axis):
        """Remove axis from the controller, basically forgets about the taurus
        device of the corresponding channel."""
        self.attributes.pop(axis)

    def PreStartOne(self, axis):
        """Prepare axis for generation.
        """
        tg = self.attributes[axis]
        self._log.debug('PreStartOne(%d): entering...' % axis)
        ch_generator = tg['ch_generator']
        state = ch_generator.getAttribute('State')
        sta = from_tango_state_to_state(state.read().value)
        if sta is State.On:
            ch_generator.stop()
        ch_position =tg['ch_position']
        state = ch_position.getAttribute('State')
        sta = from_tango_state_to_state(state.read().value)
        if sta is State.On:
            ch_position.stop()
        #configure the position source counter channel
        output_behaviour = ch_position.getAttribute('OutputEventBehaviour')
        output_behaviour.write('Pulse')
        zindex = ch_position.getAttribute('ZindexVal')
        zindex.write(4294967294)
        initialpos = ch_position.getAttribute('InitialPos')
        initialpos.write(4294967294)
        units = ch_position.getAttribute('Units')
        units.write('Ticks')
        decoding = ch_position.getAttribute('Decoding')
        decoding.write('X1')
        pulsesperrevolution = ch_position.getAttribute('PulsesPerRevolution')
        pulsesperrevolution.write(1)
        # configure the trigger counter channel
        sample_mode = ch_generator.getAttribute('SampleMode')
        sample_mode.write('Finite')
        sample_timing_type = ch_generator.getAttribute('SampleTimingType')
        sample_timing_type.write('Implicit')
        self._log.debug('PreStartOne(%d): entering...' % axis)
        return True

    def StartOne(self, axis):
        """Start generation - start the specified channel.
        """
        self._log.debug('StartOne(%d): entering...' % axis)
        tg = self.attributes[axis]
        ch_generator = tg['ch_generator']
        ch_position = tg['ch_position']
        self._Started = True
        ch_position.Start()
        ch_generator.Start()
        self._log.debug('StartOne(%d): leaving...' % axis)

    def AbortOne(self, axis):
        """Stop generation - stop the specified channel
        """
        self._log.debug('StopOne(%d): entering...' % axis)
        tg = self.attributes[axis]
        ch_generator = tg['ch_generator']
        ch_position = tg['ch_position']
        ch_generator.Stop()
        ch_position.Stop()
        self._log.debug('StopOne(%d): leaving...' % axis)

    def StateOne(self, axis):
        """Get state from the channel and translate it to the Sardana state
        """
        self._log.debug('StateOne(%d): entering...' % axis)
        tg = self.attributes[axis]
        ch_generator = tg['ch_generator']
        ch_position = tg['ch_position']
        state = ch_generator.getAttribute('State')
        sta = eval_state(state.read().value)
        status = self.state_to_status[sta]

        sta_pos = ch_position.getAttribute('State')
        if sta != State.Running and sta_pos == State.Running:
            ch_position.stop()
        self._log.debug('StateOne(%d): returning (%s, %s)'\
                             % (axis, sta, status))
        return sta, status

    def SetAxisPar(self, axis, name, value):
        """Set axis parameter.
        """
        tg = self.attributes[axis]
        ch_generator = tg['ch_generator']
        ch_position = tg['ch_position']
        name = name.lower()
        # TODO: write of some attrs require that the device is STANDBY
        # For the moment Sardana leaves the TriggerGate elements in the 
        # state that they finished the last generation. In case of 
        # Ni660XCounter, write of some attributes require the channel 
        # to be in STANDBY state. Due to that we stop the channel.
        state = ch_position.getAttribute('State')
        sta = from_tango_state_to_state(state.read().value)
        if sta is not State.Standby:
            ch_position.stop()
        state = ch_generator.getAttribute('State')
        sta = from_tango_state_to_state(state.read().value)
        if sta is not State.Standby:
            ch_generator.stop()

        if name in self._ch_gen_attr:
            attr_name = self.attribute_relations[name]
            attr = ch_generator.getAttribute(attr_name)
            if name == 'offset':
                offset = self._fromUserToHardware(axis, value)
                if offset < 4:
                    offset = 4
                value = offset
            elif name == 'repetitions':
                value = long(value)
            attr.write(value)
        elif name in self._ch_pos_attr:
            if name == 'initialpos':
                attr = int(value)
            attr = ch_position.getAttribute(name)
            attr.write(value)
        else:
            tg[name] = value

    def GetAxisPar(self, axis, name):
        tg = self.attributes[axis]
        ch_generator = tg['ch_generator']
        ch_position = tg['ch_position']
        name = name.lower()
        value = None
        if name in self._ch_gen_attr:
            attr_name = name
            if self.attribute_relations.has_key(name):
                attr_name = self.attribute_relations.get(name)
            attr = ch_generator.getAttribute(attr_name)
            value = attr.read().value
            if name == 'offset':
                value = self._fromHardwareToUser(axis, value)
        elif name in self._ch_pos_attr:
            attr = ch_position.getAttribute(name)
            value = attr.read().value
        else:
            value = self.attributes[axis][name]

        return value

    def _fromUserToHardware(self, axis, user):
        resolution = self.attributes[axis]['resolution']
        # this application can work only with X1 decoding, it means that 
        # we are loosing resolution by factor of 4
        resolution = resolution * 4
        hardware = user / resolution
        return hardware

    def _fromHardwareToUser(self, axis, hardware):
        resolution = self.attributes[axis]['resolution']
        # this application can work only with X1 decoding, it means that 
        # we are loosing resolution by factor of 4 
        resolution = resolution * 4
        user = hardware * resolution
        return user