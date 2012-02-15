import logging
import numpy
import PyTango
from pool import CounterTimerController
import time
from AlbaEmLib import albaem
import subprocess


class AlbaemCoTiCtrl(CounterTimerController):
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
    #mode = 'SW' #@note: this will be better if it's an extraattribute.
    class_prop = {'Albaemname':{'Description' : 'Albaem DS name', 'Type' : 'PyTango.DevString'},
                  'SampleRate':{'Description' : 'SampleRate set for AIDevice','Type' : 'PyTango.DevLong'}}
    
    ctrl_extra_attributes ={ "Range": 
                                {'Type':'PyTango.DevString',
                                 'Description':'Range for the channel',
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                             "Filter": 
                                {'Type':'PyTango.DevString',
                                 'Description':'Filter for the channel',
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                             "Mode": 
                                {'Type':'PyTango.DevString',
                                 'Description':'TriggerMode',
                                 'R/W Type':'PyTango.READ_WRITE'
                                },
                            }

    def __init__(self, inst, props):
        #        self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self,inst,props)
        self._log.setLevel(logging.INFO)
        self._log.debug( "__init__(%s, %s): Entering...", repr(inst), repr(props))
        #self.sd = {}
        self.master = None
        self.integrationTime = 0.0
        self.channels = []
        #self.measures = [['1',0.0],['2',0.0],['3',0.0],['4',0.0]]
        self.measures = ['','','','']
        self.status = ''
        self.acqtimeini = 0
        self.acqstarted = False
        self.lastvalues = []
        self.acqchannels = []
        self.state = None
        self.ranges = ['','','','']
        self.filters = ['','','',''] 
        self.mode = 'HW'
        try:
            self.AemDevice = PyTango.DeviceProxy(self.Albaemname)
            if self.AemDevice.state() == PyTango.DevState.STANDBY:
                self.AemDevice.StartAdc()
                #self.AemDevice.disableAll() #@todo: Check if is this needed??
        except Exception, e:
            self._log.error("__init__(): Could not create a device from following device name: %s.\nException: %s", 
                            self.Albaemname, e)
            raise
        
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        self.channels.append(axis)
        self.AemDevice.StopAdc()
        self.AemDevice.enableChannel(axis)
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        self.channels.remove(axis)
        self.ranges.pop(axis)
        self.filters.pop(axis)
        
    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        return (self.state, 'Device present')
    def StateAll(self):
        self._log.debug("StateAll(): Entering...")
        if self.mode == 'SW':
            currentacqtime = time.time()-self.acqtimeini
            if (self.acqstarted and (currentacqtime < self.integrationTime)):
                self._log.debug('StateAll:%s s (%s)'%(currentacqtime, self.integrationTime))
                self.state = PyTango.DevState.MOVING
            else:
                self.acqstarted = False
                self.state = PyTango.DevState.ON
            return self.state
        elif self.mode == 'HW':
            self.state = self.evalState(self.AemDevice.state())
            return self.state
        
#    def PreReadOne(self, axis):
#        self._log.debug("PreReadOne(%d): Entering...", axis)
#        self.readchannels.append(axis)
        
    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        if axis == 1:
            return self.integrationTime
        return float(self.measures[axis-2])

#    def PreReadAll(self):
#        self.readchannels = []
#        self._log.debug("PreReadAll(): Entering...")

    def ReadAll(self):
        #self._log.debug("ReadAll(): Entering...")
        if self.state == PyTango.DevState.ON:
            self.measures=self.AemDevice['LastValues'].value

#    def AbortOne(self, axis):
#        self._log.debug("AbortOne(%d): Entering...", axis)
#        self.acqstarted = False
#        state = self.AemDevice['state']
#        if state == PyTango.DevState.RUNNING:
#            self.AemDevice.Stop()

    def AbortAll(self):
        #self._log.debug("AbortAll(): Entering...", axis)
        state = self.AemDevice.state()
        if state == PyTango.DevState.RUNNING:
            self.AemDevice.Stop()
        self.acqstarted = False
    
    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        self.acqchannels = []

        try:
            self.state = self.AemDevice.state()
            if self.state == PyTango.DevState.RUNNING:
                self.AemDevice.Stop()
            elif self.state == PyTango.DevState.STANDBY:
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
        if self.acqstarted == False:
            try:
                self.acqtimeini = time.time()
                self.acqstarted = True
            except Exception, e:
                self._log.error("StartAllCT(): Could not start acquisition on the device: %s.\nException: %s", self.Albaemname, e)
                raise
        #@todo: All the part above will be removed ... i think it's not needed anymore. (AM)
        try:
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
        self.acqstarted = False
        if self.integrationTime != value:
            self.integrationTime = value
        try:
            if self.mode == 'SW': ##Watch out!!! this is not called in the old pool versions
                self.AemDevice.setAvsamples(1000*value)
            elif self.mode == 'HW': #@todo: This mode should be implemented and managed in the DS
                self.AemDevice.setAvsamples(1000*value)
                self.AemDevice.setTrigperiode(1000*value)
                self.AemDevice.setPoints(1)
        except PyTango.DevFailed, e:
            if self.AemDevice.state() == PyTango.DevState.STANDBY:
                self.AemDevice.StartAdc() #@todo: check if it's really needed.
            self._log.error("LoadOne(%d, %f): Could not configure device: %s.\nException: %s", self.Albaemname, e)
            raise

    def evalState(self, state):
        """This function converts PyAlbaEm device states into counters state."""
        #self._log.debug('evalState: #%s# len:%s'%(state, len(state)))
        if state == PyTango.DevState.RUNNING:
            #self._log.debug('evalState: RUNNING')
            return PyTango.DevState.MOVING
        elif state == PyTango.DevState.STANDBY or state == PyTango.DevState.ON:
            return PyTango.DevState.ON
        else:
            raise Exception('Wrong state: %s'%state)

    def GetExtraAttributePar(self, axis, name):
        self._log.debug("GetExtraAttributePar(%d, %s): Entering...", axis, name)
        if name.lower() == "range":
            self.ranges[axis-2] = self.AemDevice['Ranges'].value[axis-2]
            return self.ranges[axis-2] 
        if name.lower() == "filter":
            self.filters[axis-2] = self.AemDevice['Filters'].value[axis-2]
            return self.filters[axis-2]
        if name.lower() == "mode":
            return self.mode 

    def SetExtraAttributePar(self,axis, name, value):
        if name.lower() == "range":
            self.ranges[axis-2] = value
            channel = 'range_ch'+ str(axis-1)
            self.AemDevice[channel]=str(value)
        if name.lower() == "filter":
            self.filters[axis-2] = value
            channel = 'filter_ch'+ str(axis-1)
            self.AemDevice[channel]=str(value)
        if name.lower() == "mode":
            self.mode = value
         
    
if __name__ == "__main__":
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
    
