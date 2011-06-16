import logging
import numpy
import PyTango
from pool import CounterTimerController
import time
from AlbaEmLib import albaem



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
    
    MaxDevice = 4
    DEBUG = True
    mode = 'SW' #For the time being must be like this
    class_prop = {'Albaemname':{'Description' : 'Albaem DNS name', 'Type' : 'PyTango.DevString'},
                  'SampleRate':{'Description' : 'SampleRate set for AIDevice','Type' : 'PyTango.DevLong'}}
    '''
    ctrl_extra_attributes ={ "SD": 
                                {'Type':'PyTango.DevDouble',
                                 'Description':'Standard deviation',
                                 'R/W Type':'PyTango.READ'
                                },
                             "FORMULA": {'Type':'PyTango.DevString',
                                         'Description':'The formula to get the real value.\ne.g. "(VALUE/10)*1e-06"',
                                         'R/W Type':'PyTango.READ_WRITE'
                                        },
                             "SHAREDFORMULA": {'Type':'PyTango.DevBoolean',
                                         'Description':'If you want to share the same formula for all the channels set it to true"',
                                         'R/W Type':'PyTango.READ_WRITE'
                                        }
                            }
    
    '''
    def __init__(self, inst, props):
        #        self._log.setLevel(logging.DEBUG)
        CounterTimerController.__init__(self,inst,props)
        self._log.setLevel(logging.INFO)
        self._log.debug( "__init__(%s, %s): Entering...", repr(inst), repr(props))
        #self.sd = {}
        self.master = None
        self.integrationTime = 0
        self.channels = []
        self.measures = []
        self.status = ''
        self.acqtimeini = 0
        self.acqstarted = False
        
        try:
            #self.AemDevice = PyTango.DeviceProxy(self.Albaemname)
            self.AemDevice = albaem(self.Albaemname)
            self.AemDevice.Start()
            #self.AemDevice.disableAll()
        except Exception, e:
            self._log.error("__init__(): Could not create a device from following device name: %s.\nException: %s", 
                            self.Albaemname, e)
            raise
        
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        self.channels.append(axis)
        self.AemDevice.Stop()
        self.AemDevice.enableChannel(axis)
        self.AemDevice.Start()
        #self.sd[axis] = 0
        #self.formulas[axis] = 'value'
        #self.sharedFormula[axis] = False
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        self.channels.remove(axis)
        #self.sd.pop(axis)
        #self.formulas.pop(axis)
        #self.sharedFormula.pop(axis)

    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        return (self.state, 'Device present')
    def StateAll(self):
        '''
        if self.AemDevice is None:
            return PyTango.DevState.FAULT
        try:
            self.state = self.AemDevice.state()
            if self.master is None:
                self.state = PyTango.DevState.ON
            else:
                if self.state == PyTango.DevState.ON:
                    self.master = None
            return (evalState(self.state), "AI DeviceProxy present.") 
        except Exception, e:
            self._log.error("StateOne(%d): Could not verify state of the device: %s.\nException: %s", 
                            axis, self.Albaemname, e)
            return (PyTango.DevState.UNKNOWN, "AI DeviceProxy is not responding.")
        '''
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
        else:
            self.state = self.evalState(self.AemDevice.state())
            return self.state
        
    def PreReadOne(self, axis):
        self._log.debug("PreReadOne(%d): Entering...", axis)
        #self.sd[axis] = 0
        
    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        if axis == 1:
            return self.integrationTime
        for measure in self.measures:
            auxAxis = axis-1
            if measure[0] == '%s'%auxAxis:
                return float(measure[1])

        '''
        state = self.AemDevice.getState() 
        mean = 0
        if axis == 1:
            return self.integrationTime

        if state == PyTango.DevState.ON: 
            mean = self.AemDevice["C0%s_MeanLast" % (axis - 2)].value
            std = self.AemDevice["C0%s_StdDevLast" % (axis - 2)].value
            
            self.sd[axis] = std

            value = mean
            mean = eval(self.formulas[axis])

            self._log.debug("ReadOne(%d): mean=%f, sd=%f", 
                            axis, mean, std)
        return mean
        '''

    def ReadAll(self):
        self._log.debug("ReadAll(): Entering...")
        self.measures, self.status = self.AemDevice.getMeasures(['1', '2', '3', '4'])
        

    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        self.acqstarted = False
        '''
        state = self.AemDevice.state()
        if state == PyTango.DevState.RUNNING:
            self.AemDevice.stop()
        '''

    def AbortAll(self):
        self._log.debug("AbortAll(): Entering...", axis)
        #self.AemDevice.Stop()
        self.acqstarted = False
    
    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        '''
        self.axesToStart = []
        try:
            state = self.AemDevice.state()
            if state == PyTango.DevState.RUNNING:
                self.AemDevice.stop()
        except Exception, e:
            self._log.error("PreStartAllCT(): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            self.Albaemname, e)
            raise
        '''
        
    def PreStartOneCT(self, axis):
        """Here we are counting which axes are going to be start, so later we can distinguish 
        if we are starting only the master channel."""
        self._log.debug("PreStartOneCT(%d): Entering...", axis)
        #self.axesToStart.append(axis) #I think this is not needed because you can not start only one channel.
        return True
    def StartOneCT(self, axis):
        """Here we are counting which axes are going to be start, so later we can distinguish 
        if we are starting only the master channel."""
        self._log.debug("StartOneCT(%d): Entering...", axis)
        #self.axesToStart.append(axis) #I think this is not needed because you can not start only one channel.
        return True

    def StartAllCT(self):
        """Starting the acquisition is done only if before was called PreStartOneCT for master channel."""
        self._log.debug("StartAllCT(): Entering...")
        #if not (len(self.axesToStart) == 1 and self.axesToStart[0] == self.master):
        #    return
        if self.acqstarted == False:
            try:
                self.AemDevice.Start()
                self.acqtimeini = time.time()
                self.acqstarted = True
            except Exception, e:
                self._log.error("StartAllCT(): Could not start acquisition on the device: %s.\nException: %s", self.Albaemname, e)
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
        self.acqstarted = False
        try:
            self._log.debug("LoadOne(%d, %f): Getting state...", axis, value)
            self.state = self.evalState(self.AemDevice.getState())#This might look tricky but is necessary
            self._log.debug("LoadOne(%d, %f): Got state...", axis, value)
            #self._log.debug('LoadOne: state: %s'%self.state)
            if self.state == PyTango.DevState.MOVING:# or self.state == PyTango.DevState.ON:
                self._log.debug('LoadOne: Device is RUNNING. Stopping...')
                self.AemDevice.Stop()
        except PyTango.DevFailed, e:
            self._log.error("LoadOne(%d, %f): Could not ask about state of the device: %s and/or stop it.\nException: %s", 
                            axis, value, self.Albaemname, e)
            raise
        #bufferSize = int(self.integrationTime * self.SampleRate)
        try:
            '''
            self.AemDevice['NumOfTriggers'] = 1
            self.AemDevice['TriggerInfinite'] = 0    
            self.AemDevice['SampleRate'] = self.SampleRate
            self.AemDevice['ChannelSamplesPerTrigger'] = bufferSize
            '''
            if self.mode == 'SW': ##Watch out!!! this is not called in the old pool versions
                self.AemDevice.setAvsamples(1000*value)
            else:
                self.AemDevice.setAvsamples(1000*value)
                self.AemDevice.setTrigperiode(1000*value)
                self.AemDevice.setPoints(1)
            avs = self.AemDevice.getAvsamples()
            avs = self.AemDevice.Start()
            #trp = self.AemDevice.getTrigperiode()
            #po = self.setPoints()
            #self._log.debug('Mode:%s, Avs:%s, Tp:%s, Po:%s'%(self.mode, avs, trp, po))
        except PyTango.DevFailed, e:
            self.AemDevice.Start() #keep it running baby
            self._log.error("LoadOne(%d, %f): Could not configure device: %s.\nException: %s", self.Albaemname, e)
            raise
    def evalState(self, state):
        """This function converts Adlink device states into counters state."""
        #self._log.debug('evalState: #%s# len:%s'%(state, len(state)))
        if state == 'RUNNING':
            #self._log.debug('evalState: RUNNING')
            return PyTango.DevState.MOVING
        elif state == 'IDLE':
            return PyTango.DevState.ON
        else:
            raise Exception('Wrong state')
    
    
if __name__ == "__main__":
    obj = AlbaemCoTiCtrl('test',{'Albaemname':'ELEM01R42S007.cells.es','SampleRate':1000})
    obj.AddDevice(1)
    obj.AddDevice(2)
    obj.LoadOne(1,1)
    print obj.PreStartAllCT()
    print obj.AemDevice.setFilters([['1', '3200'],['2', '3200'],['3', '3200'],['4', '3200']])
    print obj.AemDevice.setRanges([['1', '1mA'],['2', '1mA'],['3', '1mA'],['4', '1mA']])
    print obj.StartOneCT(1)
    print obj.StartOneCT(2)
    print obj.StartAllCT()
    ans1 = obj.StateOne(1)
    ans = obj.StateOne(2)
    ans = obj.StateAll()
    print ans
    i = 0
    while ans == PyTango.DevState.MOVING:
        print "ans:", ans
        #time.sleep(0.3)
        ans = obj.StateOne(1)
        ans1 = obj.StateOne(2)
        ans = obj.StateAll()
        print obj.ReadAll()
        print obj.ReadOne(1) 
        print obj.ReadOne(2) 
        print "State is running: %s"%i 
        i = i + 1
    print "ans:", ans
    print obj.ReadAll()
    print obj.ReadOne(1) 
    print obj.ReadOne(2) 
    obj.DeleteDevice(1)
    obj.DeleteDevice(2)
    
