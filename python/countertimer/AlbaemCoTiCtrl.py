import logging
import PyTango
from albaemlib import AlbaEm

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import CounterTimerController
from sardana.pool import AcqTriggerType
from sardana.pool.controller import MemorizedNoInit, NotMemorized, Memorized

class AlbaemCoTiCtrl(CounterTimerController):
    """This class is the Sardana CounterTimer controller for the Alba Electrometer adc based counters.
    The only way to use this controller is to define up to 5 channels 
    and create a measurement group where the first channel is a master channel. 
    The Adlink card works in a way where acquisition for all channels is started only once 
    and in controller this is done when StartsAll() method was called for this controller, 
    only when PreStartOne() was called for master channel. 
    
    Configuration of Albaem is done in LoadOne() method where size of acquisition buffer 
    is calculated from acquisition time and SampleRate property. 
    
    Value returned by a channel is an average of buffer values. 
    """
    MaxDevice = 5
    class_prop = {'Albaemname':{'Description' : 'Albaem DS name', 'Type' : 'PyTango.DevString'},
                  }
    
    ctrl_extra_attributes ={ "Range": 
                                {'Type':'PyTango.DevString',
                                 'Description':'Range for the channel',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                             "Filter": 
                                {'Type':'PyTango.DevString',
                                 'Description':'Filter for the channel',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                             "DInversion": 
                                {'Type':'PyTango.DevString',
                                 'Description':'Digital inversion for the channel',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                             "Offset": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Offset in % for the channel',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                             "SampleRate": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Albaem sample rate',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "AutoRange": 
                                {'Type':'PyTango.DevBoolean',
                                 'Description':'Enable/Disable electrometer autorange',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            #attributes added for continuous acqusition mode
                            "NrOfTriggers": 
                                {'Type':'PyTango.DevLong',
                                 'Description':'Nr of triggers',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "SamplingFrequency": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Sampling frequency',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "AcquisitionTime": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Acquisition time per trigger',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "TriggerMode": 
                                {'Type':'PyTango.DevString',
                                 'Description':'Trigger mode: soft or gate',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            "Data": 
                                {'Type':[float],
                                 'Description':'Trigger mode: soft or gate',
                                 'memorized': NotMemorized,
                                 'R/W Type':'PyTango.READ'
                                }
                            }

    def __init__(self, inst, props, *args, **kwargs):
        #self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self,inst,props, *args, **kwargs)
        #self._log.setLevel(logging.INFO)
        self._log.debug( "__init__(%s, %s): Entering...", repr(inst), repr(props))
        
        self.master = None
        self.integrationTime = 0.0
        self.avSamplesMax = 1000
        self.channels = []
        
        self.measures = ['0','0','0','0'] #@todo: this is not a good idea, better change it. Maybe avoid ReadAll?
        
        self.lastvalues = []
        self.contAcqChannels = {}
        self.acqchannels = []
        self.state = None
        self.ranges = ['','','','']
        self.filters = ['','','','']
        self.dinversions = ['','','','']
        self.offsets = ['','','',''] 
        self.sampleRate = 0.0
        try:
            self.AemDevice = PyTango.DeviceProxy(self.Albaemname)
            self.state = self.AemDevice.getEmState()
        
        except Exception, e:
            self._log.error("__init__(): Could not create a device from following device name: %s.\nException: %s", 
                            self.Albaemname, e)
            #raise #@warning: if you raise an exception, the pool doesn't start if the electrometer is switch off.
        
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        self.channels.append(axis)
        #self.AemDevice.enableChannel(axis) #@todo: Maybe this is better to be done in DS
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        self.channels.remove(axis)
        
    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        return (self.state, 'Device present')
    def StateAll(self):
        self._log.debug("StateAll(): Entering...")
        self.state = self.evalState(self.AemDevice.getEmState())
        return self.state
        
#    def PreReadOne(self, axis):
#        self._log.debug("PreReadOne(%d): Entering...", axis)
#        self.readchannels.append(axis)
        
    def ReadOne(self, axis):
        #@todo: Read directly the mean of the channels buffer, and avoid read all
        self._log.debug("ReadOne(%d): Entering...", axis)
        if axis == 1:
            return self.integrationTime
        
        return float(self.measures[axis-2])

#    def PreReadAll(self):
#        self.readchannels = []
#        self._log.debug("PreReadAll(): Entering...")

    def ReadAll(self):
        self._log.debug("ReadAll(): Entering...")
        if self.state == PyTango.DevState.ON:
            self.measures=self.AemDevice['LastValues'].value

    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
#        state = self.AemDevice['state']
#        if state == PyTango.DevState.RUNNING:
#            self.AemDevice.Stop()
        pass

    def AbortAll(self):
        #self._log.debug("AbortAll(): Entering...", axis)
        state = self.AemDevice.getEmState()
        if state == 'RUNNING':
            self.AemDevice.Stop()
    
    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        self.acqchannels = []

        try:
            state = self.AemDevice.getEmState()
            if state == 'RUNNING': #When live was easy: PyTango.DevState.RUNNING:
                self.AemDevice.Stop()
            elif state == 'IDLE': #PyTango.DevState.STANDBY:
                self.AemDevice.StartAdc()
        except Exception, e:
            self._log.error("PreStartAllCt(): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            self.Albaemname, e)
            raise
        
    def PreStartOneCT(self, axis):
        """Here we are counting which axes are going to be start, so later we can distinguish 
        if we are starting only the master channel."""
        self._log.debug("PreStartOneCT(%d): Entering...", axis)
        self.acqchannels.append(axis)
        return True
    def StartOneCT(self, axis):
        """Here we are counting which axes are going to be start, so later we can distinguish 
        if we are starting only the master channel."""
        self._log.debug("StartOneCT(%d): Entering...", axis)
        return True

    def StartAllCT(self):
        """Starting the acquisition is done only if before was called PreStartOneCT for master channel."""
        self._log.debug("StartAllCT(): Entering...")
        try:
            #if self.state == PyTango.DevState.ON:
            self.AemDevice.Start()
            
        except Exception, e:
            self._log.error("StartAllCT(): Could not start acquisition on the device: %s.\nException: %s", 
                            self.Albaemname, e)
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
        
        if self.integrationTime != value:
            self.integrationTime = value
        try:
            #@todo: This will be done too many times, only one is needed.
            if axis == 1:
                
                #@todo: This part is still not fully tested###########
                #self.sampleRate = self.AemDevice['SampleRate'].value
                #avSamples = value/self.sampleRate
                #
                #if avSamples > self.avSamplesMax:
                #    self.sampleRate = value/self.avSamplesMax
                #    self.AemDevice['SampleRate'] = self.sampleRate
                #    avSamples = value/self.sampleRate
                ######################################################
                avSamples = value #needed while tests are pending
                self.AemDevice['Avsamples'] = avSamples
                self.AemDevice['TriggerPeriod'] = value
                #added by zreszela 12.02.2013, trigger delay is set by conitnuous scan, in step scan it must be always 0
                self.AemDevice['TriggerDelay'] = 0
                
                
                #@warning: The next 1 + 1 is done like this to remember that it
                #                         shoud be Points + 1 because the first
                #                         trigger arrives at 0s
                #                         at some point this will be changed in
                #                         the albaem and we will remove the + 1
                ###############################################################
                self.AemDevice['BufferSize'] = 1 + 1
                
            else:
                pass
               
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not configure device: %s.\nException: %s", self.Albaemname, e)
            raise

    def evalState(self, state):
        """This function converts PyAlbaEm device states into counters state."""
        #self._log.debug('evalState: #%s# len:%s'%(state, len(state)))
        #@note: Thanks to the megaimportant requirement of changing the colors
        #       depending the ranges, I have to change completely this function
        #        ... again!

        if state == 'RUNNING':
            return PyTango.DevState.MOVING
        elif state == 'ON':
            return PyTango.DevState.ON
        elif state == 'IDLE':
            return PyTango.DevState.ON
        else:
            self._log.debug('Wrong state: %s',state)

    def GetExtraAttributePar(self, axis, name):
        self._log.debug("GetExtraAttributePar(%d, %s): Entering...", axis, name)
        if name.lower() == "range":
            self.ranges[axis-2] = self.AemDevice['Ranges'].value[axis-2]
            return self.ranges[axis-2] 
        if name.lower() == "filter":
            self.filters[axis-2] = self.AemDevice['Filters'].value[axis-2]
            return self.filters[axis-2]
        if name.lower() == "dinversion":
            attr = 'dInversion_ch'+str(axis-1)
            self.dinversions[axis-2] = self.AemDevice[attr].value
            return self.dinversions[axis-2] 
        if name.lower() == "offset":
            attr = 'offset_percentage_ch'+str(axis-1)
            self.offsets[axis-2] = self.AemDevice[attr].value
            return self.offsets[axis-2]
        if name.lower() == "samplerate":
            attr = 'SampleRate'
            self.sampleRate = self.AemDevice[attr].value
            return self.sampleRate
        if name.lower() == "autorange":
            attr = 'Autorange'
            autoRange = self.AemDevice[attr].value
            return autoRange
        #attributes used for continuous acquisition
        if name.lower() == "samplingfrequency":
            freq = 1 / self.AemDevice["samplerate"].value
            return freq
        if name.lower() == "triggermode":
            mode = self.AemDevice["TriggerMode"].value 
            if mode == "INT":
                return "soft"
            if mode == "EXT":
                return "gate"
        if name.lower() == "nroftriggers":
            nrOfTriggers = self.AemDevice["BufferSize"].value
            return nrOfTriggers
        if name.lower() == "acquisitiontime":
            acqTime = self.AemDevice["AvSamples"].value
            return acqTime
        if name.lower() == "data":
            data = self.AemDevice["BufferI%d" % (axis - 1)].value
            return data

    def SetExtraAttributePar(self,axis, name, value):
        if name.lower() == "range":
            self.ranges[axis-2] = value
            attr = 'range_ch'+ str(axis-1)
            self.AemDevice[attr]=str(value)
        if name.lower() == "filter":
            self.filters[axis-2] = value
            attr = 'filter_ch'+ str(axis-1)
            self.AemDevice[attr]=str(value)
        if name.lower() == "dinversion":
            self.dinversions[axis-2] = value
            attr = 'dInversion_ch'+ str(axis-1)
            self.AemDevice[attr]=str(value)
        if name.lower() == "offset":
            self.offsets[axis-2] = value
            attr = 'offset_ch'+ str(axis-1)
            self.AemDevice[attr]=str(value)
        if name.lower() == "samplerate":
            self.sampleRate = value
            attr = 'sampleRate'
            self.AemDevice[attr]= value
        if name.lower() == "autorange":
            attr = 'AutoRange'
            self.AemDevice[attr] = value
        #attributes used for continuous acquisition
        if name.lower() == "samplingfrequency":
            maxFrequency = 1000
            if value == -1 or value > maxFrequency: 
                value = maxFrequency#-1 configures maximum frequency            
            rate = 1 / value
            self.AemDevice["samplerate"] = rate
        if name.lower() == "triggermode":
            if value == "soft":
                mode = "INT"
            if value == "gate":
                mode = "EXT"
            self.AemDevice["TriggerMode"] = mode
        if name.lower() == "nroftriggers":
            self.AemDevice["BufferSize"] = value
        if name.lower() == "acquisitiontime":
            self.AemDevice["TriggerDelay"] = value
            self.AemDevice["AvSamples"] = value

    def SetCtrlPar(self, par, value):
        self._log.debug("SetCtrlPar(%s, %s) entering..." % (repr(par), repr(value)))
        if par == 'trigger_type':
            if value == AcqTriggerType["Software"]:
                self.AemDevice['TriggerMode'] = 'INT'
            elif value == AcqTriggerType["Gate"]:
                self.AemDevice['TriggerMode'] = 'EXT'
            else:
                raise Exception("Alba electrometer allows only Software or Gate triggering")
        else:
            super(AlbaemCoTiCtrl, self).SetCtrlPar(par, value)
            
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
                    self.AemDevice.Start()
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
                    self.AemDevice.Stop()
                    ret = "Acquisition stopped"
                else:
                    ret = "Channel %d popped from contAcqChannels" % axis
        return ret

if __name__ == "__main__":
    #import time
    #obj = AlbaemCoTiCtrl('test',{'Albaemname':'ELEM01R42-020-bl29.cells.es','SampleRate':1000})
    obj = AlbaemCoTiCtrl('test',{'Albaemname':'amilan/emet/01','SampleRate':1000})
    obj.AddDevice(1)
    obj.AddDevice(2)
    obj.AddDevice(3)
    obj.AddDevice(4)
    obj.AddDevice(5)
    obj.LoadOne(1,1)
    print obj.PreStartAllCT()
    #print obj.AemDevice.setFilters([['1', 'NO'],['2', 'NO'],['3', 'NO'],['4', 'NO']])
    #print obj.AemDevice.setRanges([['1', '1mA'],['2', '1mA'],['3', '1mA'],['4', '1mA']])
    print obj.StartOneCT(1)
    print obj.StartOneCT(2)
    print obj.StartOneCT(3)
    print obj.StartOneCT(4)
    print obj.StartOneCT(5)
    print obj.StartAllCT()
    ans = obj.StateOne(1)
    ans = obj.StateOne(2)
    ans = obj.StateOne(3)
    ans = obj.StateOne(4)
    ans = obj.StateOne(5)
    ans = obj.StateAll()
    print ans
    i = 0
    while ans == PyTango.DevState.MOVING:
        print "ans:", ans
        #time.sleep(0.3)
        ans = obj.StateOne(1)
        ans = obj.StateOne(2)
        ans = obj.StateOne(3)
        ans = obj.StateOne(4)
        ans = obj.StateOne(5)
        ans = obj.StateAll()
        print obj.ReadAll()
        print obj.ReadOne(1) 
        print obj.ReadOne(2) 
        print obj.ReadOne(3) 
        print obj.ReadOne(4) 
        print obj.ReadOne(5) 
        print "State is running: %s"%i 
        i = i + 1
    print "ans:", ans
    print obj.ReadAll()
    print obj.ReadOne(1) 
    print obj.ReadOne(2) 
    print obj.ReadOne(3) 
    print obj.ReadOne(4) 
    print obj.ReadOne(5) 
    obj.DeleteDevice(1)
    obj.DeleteDevice(2)
    obj.DeleteDevice(3)
    obj.DeleteDevice(4)
    obj.DeleteDevice(5)
    
