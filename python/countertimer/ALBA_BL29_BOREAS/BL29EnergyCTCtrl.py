#!/usr/bin/env python
import datetime
import numpy
import PyTango, taurus
from sardana import State, DataAccess
from sardana.pool import AcqTriggerType, AcqMode
from sardana.pool.controller import CounterTimerController, Memorize, NotMemorized
from sardana.pool.controller import Type, Access, Description, MaxDimSize
from sardana.tango.core.util import from_tango_state_to_state

from BL29Energy import Energy
import Ni660XPositionCTCtrl

def evalState(state):
    """This function converts Ni660X device states into counters state."""
    if state == PyTango.DevState.RUNNING:
        return State.Moving
    elif state == PyTango.DevState.STANDBY:
        return State.On
    else:
        return from_tango_state_to_state(state)

class BL29EnergyCTCtrl(Ni660XPositionCTCtrl.Ni660XPositionCTCtrl):
    "This class is the Ni600X position capture Sardana CounterTimerController"

    MaxDevice = 32

    # in order to reduce readouts from the tango device we will use a delay counter
    # read from the tango device will be done every certain number of queries
    query_filter = 15
    
    ctrl_properties = { "channelDevNames" : { Type : str, Description : "Comma separated Ni660xCounter device names"}, 
                        'sm_pseudo' : { Type : str, Description : 'The name of the DiscretePseudoMotor to read/select which SM to use'},
                        'gr_pseudo' : { Type : str, Description : 'The name of the DiscretePseudoMotor to read/select which grating to use'}
                      }
    

    def __init__(self, inst, props, *args, **kwargs):
        #Ni660XPositionCTCtrl.__init__(self, inst, props, *args, **kwargs)
        super(BL29EnergyCTCtrl, self).__init__(inst, props, *args, **kwargs)
        self._log.debug("BL29EnergyCTCtrl.__init__(): entering...")
        self._log.debug(repr(self.axis_attributes))
        self.sm = PyTango.DeviceProxy(self.sm_pseudo)
        self.gr = PyTango.DeviceProxy(self.gr_pseudo)
        self.index = 0
        # in order to reduce readouts from the tango device we will use a delay counter
        # read from the tango device will be done every certain number of queries
        self.delay_counter = 0 
        # cache of nr of triggers - will be used to determine if index has reached it
        self.nr_of_triggers = 0
        self.acquireing = False

    def AddDevice(self, axis):
        self.channel = taurus.Device(self.channelDevNamesList[0])
        self.channel.set_timeout_millis(120000) #readount ot 60000 buffer takes aprox 10 seconds
        self.attributes = {"sign":1, "initialposition":0}


    def DeleteDevice(self, axis):
        self.channel = None
        self.attributes.pop(axis)

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar() entering...")
        name = name.lower()
        if name == "channeldevname":
            v = self.channelDevNamesList[0]
        elif name == "sampleclocksource":
            v = self.channel["SampleClockSource"].value
        elif name == "datatransfermechanism":
            v = self.channel["DataTransferMechanism"].value
        elif name == "units":
            v = self.channel["Units"].value
        elif name == "pulsesperrevolution":
            v = self.channel["PulsesPerRevolution"].value
        #temporarily using internal algorithm
        #elif name == "initialposition":
        #    v = self.channels[axis]["InitialPos"].value
        elif name == "zindexenabled":
            v = self.channel["ZIndexEnabled"].value
        elif name == "data":
            s = datetime.datetime.now()
            self._log.debug("GetAxisExtraPar() data: start time = %s" % s.isoformat())
            rawData = self.channel["PositionBuffer"].value
            if self.attributes["sign"] == -1:
                rawDataNumpy = numpy.array(rawData)
                v = rawDataNumpy * -1
            else:
                v = rawData
            v = v + self.attributes["initialposition"]
            e = datetime.datetime.now()
            self._log.debug("GetAxisExtraPar() data: end time = %s" % e.isoformat())
            t = e - s
            self._log.debug("GetAxisExtraPar() data: total = %d" % t.seconds)
        elif name == "nroftriggers":
            v = self.channel["SampPerChan"].value
        elif name == "triggermode":
            raw = self.channel["SampleTimingType"]
            if raw == "SampleClk":
                v = "gate"
            else:
                v = "soft"
        elif name == "samplingfrequency":
            v = float("nan")
        elif name == "acquisitiontime":
            v = float("nan")
        else:
            v = self.attributes[name]

        return v

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar() entering...")
        name = name.lower()
        if name == "sampleclocksource":
            self.channel["SampleClockSource"] = value
        elif name == "datatransfermechanism":
            self.channel["DataTransferMechanism"] = value
        elif name == "units":
            self.channel["Units"] = value
        elif name == "pulsesperrevolution":
            self.channel["PulsesPerRevolution"] = value
        #temporarily using internal algorithm
        #elif name == "initialposition":
        #    self.channels[axis]["InitialPos"] = value
        elif name == "zindexenabled":
            self.channel["ZIndexEnabled"] = value
        elif name == "nroftriggers":
            #self.channels[idx]["SampPerChan"] = value # due to bug in taurus remporarily using PyTango
            self.channel.getHWObj().write_attribute("SampPerChan", long(value))
            self.nr_of_triggers = long(value)
        elif name == "triggermode":
            if value == "gate":
                self.channel["SampleTimingType"] = "SampClk"
            else:
                pass
        elif name == "samplingfrequency":
            pass
        elif name == "acquisitiontime":
            pass
        else:
            self.attributes[name] = value 

    def StateAll(self):
        self._log.debug('StateAll(): entering...')
        if self.channel == None:
            self.sta = State.Init
            self.status = 'Channel configuration is not finished. "channelDevName" attribute is not specified.'
            return
        if self.acquireing:
            self._log.debug('StateAll(): index = %d' % self.index)
            if self.index == self.nr_of_triggers:
                self.sta = State.On
                self.status = 'Acquisition finished'
            else:
                self.sta = State.Moving
                self.status = 'Acquisition in progress'
            self._log.debug('StateAll(): status = %s' % self.status)
        else:
            rawState = self.channel.State()
            self.sta = evalState(rawState)
            self.status = "" 
    
    def StateOne(self, axis):
        return self.sta, self.status
    
    def PreStartAllCT(self):
        self.sm_selected = self.sm.read_attribute('Position').value
        self.gr_selected = self.gr.read_attribute('Position').value

    def StartOneCT(self, axis):
        self._log.debug("StartOneCT(%d): Entering" % axis)
        if self.channel.State() == PyTango.DevState.RUNNING:
            return
        self.channel.Start()
        self.index = 0
        # resetting delay counter
        self.delay_counter = 0
    
    def StartAllCT(self):
        self.acquireing = True

    def AbortOne(self, axis):
        self._log.debug('AbortOne(%d): Entering...' %  axis)
        if self.channel.State() != PyTango.DevState.RUNNING:
            self.channel.Stop()

    def AbortAll(self, axis):
        self.acquireing = False

    def PreReadAll(self):
        self.spectrum = None

    def PreReadOne(self,axis):
        pass

    def ReadAll(self):
        self._log.debug('ReadAll(): entering...' )
        data = None
        # incrementing delay counter
        self.delay_counter += 1
        # modulo calculation so that we reset every query_filter value to 0
        self.delay_counter %= self.query_filter
        # skipping readout
        if self.delay_counter != 0:
            self._log.debug('ReadAll(): Filtering out query...')
        else:
            # reading from the device
            try:
                data = self.channel["PositionBuffer"].value
                self._log.debug('ReadAll(): data: %s' % repr(data))
            except Exception, e:
                self._log.error('ReadAll(): Exception while reading buffer: %s' % e)
            self._log.debug('ReadAll() data read' )
        try:
            index = self.index
        except Exception, e:
            self._log.error('ReadAll(): reading index exception %s' % e)
        self._log.debug('ReadAll() index = %d' % index)
        if data is None or len(data) == index:
            v = []
            self._log.debug('ReadAll(), data empty....' )
        else:
            try:
                tmpIndex = len(data)
                data = data[index:]
                self.index = tmpIndex
                if self.attributes["sign"] == -1:
                    dataNumpy = numpy.array(data)
                    v = dataNumpy * -1
                else:
                    v = numpy.array(data)
                v = v + self.attributes["initialposition"]
                v = v.tolist()
                self._log.debug('Ending........, ReadAll')
            except Exception, e:
                self._log.debug('ReadAll(): Exception numpy array %s' % e)
        self.gr_pitch_angle = v
        self._log.debug('ReadAll(): leaving...')

    def ReadOne(self, axis):
        self._log.debug('ReadOne(%d): entering...' % axis)
        try:
            values = []
            if axis == 1:
                for encoder_value in self.gr_pitch_angle:
                    energy_value = Energy.get_energy(self.sm_selected, self.gr_selected, encoder_value, gr_source_is_encoder=True)
                    self._log.debug('ReadOne(): energy = %f; sm_selected = %d; gr_selected = %d, encoder_value = %f' % (energy_value, self.sm_selected, self.gr_selected, encoder_value))
                    values.append(energy_value)
            elif axis == 2:
                values = self.gr_pitch_angle
        except Exception, e:
            self._log.error('Exception: %s' % e)
        self._log.debug('ReadOne(%d): returning %s' % (axis, repr(values)))        
        return values

