from MythenLib import Mythen, UDP_PORT, TCP_PORT

from sardana import State, DataAccess
from sardana.pool.controller import OneDController, MaxDimSize, FSet, FGet
from sardana.pool.controller import DefaultValue, Description, Access, Type


def debug(func):
    def new_fun(*args,**kwargs):
        klass = args[0]
        klass._log.debug('Entering to: %s(%s)' % (func.func_name, repr(args)))
        result = func(*args,**kwargs)
        klass._log.debug('Leaving the function: %s .....' % func.func_name)
        return result
    return new_fun   

class MythenController(OneDController):
    """ 
    This class is the Sardana CounterTimer controller for the Dectris Mythen
    Detector. 
  
    The only way to use this controller is to define up to 1 channel. This 
    channels export some attributes. The Ch0D attribute is the integration of 
    the channels defined in the Ch0DROI attribute. You can use this attribute 
    in the measurement group as a Tango attribute.
    
    To read/write the threshold the module must be connected. 
    """   

    gender = ""
    model = "Basic"
    organization = "Sardana team" 
    MaxDevice = 1
  
  
    class_prop = {'MythenHostName':{'Description':'IP or host name',
                                      'Type' : 'PyTango.DevString'},
                  'ProtocolType':{'Description': 'UDP or TCP',
                                  'Type': 'PyTango.DevString'},
                  'NMod':{'Description':'Number of Modules',
                          'Type':'PyTango.DevLong'}}

    axis_attributes = {
        'Ch0D' : { 
            Type : float,
            FGet: 'getCh0d',
            Description : 'Integration of the spectrum.',
            Access : DataAccess.ReadOnly},
        'Ch0DROI' : { 
            Type : (int,),
            FSet: 'setCh0dROI',
            FGet: 'getCh0dROI',
            Description : 'Integration of the spectrum.',
            Access : DataAccess.ReadWrite},
        'Threshold' : { 
            Type : float,
            FSet: 'setThreshold',
            FGet: 'getThreshold',
            Description : 'Threshold in keV.',
            Access : DataAccess.ReadWrite},
        'BitResolution' : { 
            Type : int,
            FSet: 'setNbits',
            FGet: 'getNbits',
            Description : 'The number of bits to be read out.',
            Access : DataAccess.ReadWrite},             
        }
    
    def __init__(self, inst, props, *args, **kwargs):
        super(MythenController,self).__init__(inst, props, *args, **kwargs)
        if self.ProtocolType == 'UDP':
            port = UDP_PORT
        elif self.ProtocolType == 'TCP':
            port = TCP_PORT
        else:
            msg = 'ProtocolType property has a wrong value.'
            self._log.error(msg)
            raise Exception(msg)
                  
        try: 
            self.mythen_device = Mythen(self.MythenHostName, port)
        except Exception, e:
            msg = ("__init__(): Could not create the socket to the Mythen. "
                   "Exception %s" % e)
            self._log.error(msg)
            raise Exception(msg)
        self.StateOne(1)
        
   
    @debug
    def AddDevice(self, axis):
        if axis != 1:
            raise Exception('This controller can support one axis')
        
        self.channels = None
        self.max_channels = self.NMod * 1280
        self.ch0d_roi = [0 , self.max_channels]
        self._calcCh0d()

    @debug
    def DeleteDevice(self, axis):
        self.channels = None
    
    @debug
    def StateOne(self, axis):
        state = self.mythen_device.getStatus()
        print state
        if state == 'RUNNING':
            self.state = State.Moving
            self.status = 'Mythen is running'
        elif state == 'WAIT_TRIGGER':
            self.state = State.Moving
            self.status = 'Mythen is waiting for trigger'
        elif state == 'ON':
            self.state = State.On
            self.status = 'Mythen is ON'
        else:
            self.state = State.Fault
            self.status = 'State Unknown'
        return self.state, self.status

    @debug
    def ReadOne(self, axis):
        if self.state == State.On:
            self.channels = self.mythen_device.getReadOut()
            self._calcCh0d()
        else:
            raise Exception('Acquisition did not finish correctly')
        
        return self.channels
    
    @debug
    def StartOne(self, axis, value):
        if self.state == State.On:
            self.mythen_device.startAcquisition()
        else:
            raise Exception('The device must be ON. State: %s' % self.state)

    @debug
    def LoadOne(self, axis, value):
        if value > 0:
            self.mythen_device.setTime(value)
        else:
            raise Exception('The monitor mode does not implement yet.')
  
    @debug
    def AbortOne(self, axis):
        self.mythen_device.stopAcquisition()
        self.channels = None

    @debug
    def getCh0d(self, axis):
        return self.ch0d
    
    @debug
    def _calcCh0d(self):
        if self.channels == None:
           self.ch0d = 0
        else:
            if self.state == State.On:
                channels_value = [i if i!=-2 else 0 for i in self.channels]
                s, e  = self.ch0d_roi
                channels_value = channels_value[s:e]
                self.ch0d = sum(channels_value)
                print self.ch0d
            else:
                self.ch0d = 0

   
    @debug
    def getCh0dROI(self, axis):
        return self.ch0d_roi
    
    @debug
    def setCh0dROI(self, axis, value):
        s, e = value
        if s < 0 or s > e or e > self.max_channels:
            raise Exception('Error: Wrong parameter.')
        self.ch0d_roi = value
        
    @debug
    def setThreshold(self, axis, value):
        self.mythen_device.setThreshold(value)
    
    @debug
    def getThreshold(self, axis):
        return self.mythen_device.getThreshold()
    
    @debug
    def setNbits(self, axis, value):
        self.mythen_device.setBitsReadOut(value)
    
    @debug
    def getNbits(self, axis):
        return self.mythen_device.getBitsReadOut()
