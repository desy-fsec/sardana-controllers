import time, logging
from ctypes import *
import PyTango
from pool import CounterTimerController

TaskHandle = c_ulong
int32 = c_long
uInt32 = c_ulong
uInt64 = c_ulonglong
bool32 = uInt32
float64 = c_double

DAQmx_Val_ChanForAllLines = int32(1)
DAQmx_Val_Low = int32(10214)
DAQmx_Val_High = int32(10192)
DAQmx_Val_FiniteSamps = int32(10178)
DAQmx_Val_DigEdge = int32(10150)
DAQmx_Val_Rising = int32(10280)
DAQmx_Val_GroupByChannel = bool32(0)

MAX80MHZ = 53.6870911875
MAX20MHZ = 214.74836475
MAX100KHZ = 42949.67295

delay = int32(0)
nrOfPulses = uInt64(1)
charArray2048 = c_char * 2048
errBuff = charArray2048('\0')
uInt32Array2 = uInt32 * 2
doSamples = int32(2)
doAutostart = bool32(1)
doTimeout = float64(1)
doData = uInt32Array2(uInt32(0xffffffff),uInt32(0x0))
doWrittenSamples = int32()
isTaskDone = bool32()

nidaqmx = cdll.LoadLibrary("libnidaqmx.so.1")

def DAQmxErrChk (status):
    if status < 0: 
        nidaqmx.DAQmxGetExtendedErrorInfo(errBuff,uInt32(2048))
        errStr = ""
        for c in errBuff:
            errStr+=c
        print errStr

class NI6602CoTiCtrl(CounterTimerController):

    MaxDevice = 1
    class_prop = {'DaqName':{'Description' : 'Name of the daq device', 'Type' : 'PyTango.DevString'},
                  'TriggeringLineNr':{'Description' : 'Name of the daq device', 'Type' : 'PyTango.DevLong'}}

    def __init__(self, inst, props):
        CounterTimerController.__init__(self,inst,props)
        self._log.setLevel(logging.DEBUG)
        self._log.debug("__init__(%s, %s): Entering...", repr(inst), repr(props))
        self.time = 0
        self.high = None
        self.low = None
        self.source = None
        self.triggerTask = TaskHandle()
        self.mainTask = None
        DAQmxErrChk(nidaqmx.DAQmxCreateTask("TriggerTask",byref(self.triggerTask)))
        triggeringLineFullName = self.DaqName + "/port0/line" + str(self.TriggeringLineNr)
        DAQmxErrChk(nidaqmx.DAQmxCreateDOChan(self.triggerTask,triggeringLineFullName,"",DAQmx_Val_ChanForAllLines))
    
    def AddDevice(self, axis):  
        self._log.debug("AddDevice(%d): Entering...", axis)
        
    def DeleteDevice(self, axis):
        self._log.debug("DeleteDevice(%d): Entering...", axis)
        
    def StateOne(self, axis):
        self._log.debug("StateOne(%d): Entering...", axis)
        if self.mainTask is None:
            return (PyTango.DevState.ON, "State is ON")
        DAQmxErrChk(nidaqmx.DAQmxIsTaskDone(self.mainTask, byref(isTaskDone)))
        if bool(isTaskDone):    
            return (PyTango.DevState.ON, "State is ON")
        else:
            return (PyTango.DevState.MOVING, "State is MOVING")

    def ReadOne(self, axis):
        self._log.debug("ReadOne(%d): Entering...", axis)
        return self.time

    def AbortOne(self, axis):
        self._log.debug("AbortOne(%d): Entering...", axis)
        DAQmxErrChk(nidaqmx.DAQmxStopTask(self.mainTask));
        DAQmxErrChk(nidaqmx.DAQmxClearTask(self.mainTask));
        
    def PreStartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        DAQmxErrChk(nidaqmx.DAQmxStartTask(self.triggerTask))
        DAQmxErrChk(nidaqmx.DAQmxStartTask(self.mainTask))

    def PreStartOneCT(self, axis):
        self._log.debug("PreStartOneCT(%d): Entering...", axis)
        return True
    
    def StartOneCT(self, axis):
        self._log.debug("StartOneCT(%d): Entering...", axis)

    def StartAllCT(self):
        self._log.debug("PreStartAllCT(): Entering...")
        DAQmxErrChk(nidaqmx.DAQmxWriteDigitalU32(self.triggerTask,doSamples,doAutostart,doTimeout,DAQmx_Val_GroupByChannel,doData,byref(doWrittenSamples),None));
  
    def PreLoadOne(self, axis, value):
        self._log.debug("PreLoadOne(%d, %f): Entering...", axis, value)
        if self.mainTask is not None:
            DAQmxErrChk(nidaqmx.DAQmxClearTask(self.mainTask))
        if value < MAX80MHZ:
            self.source = "80MHzTimebase"
            nrOfPulses = int(value * 80000000)
        elif value < MAX20MHZ:
            self.source = "20MHzTimebase"
            nrOfPulses = int(value * 20000000)
        elif value < MAX100KHZ:
            self.source = "100KHzTimebase"
            nrOfPulses = int(value * 100000)
        else: 
            raise PyTango.DevFailed("Ni6602 card is not able to generate pulse longer than: %f" % MAX100KHZ)
        #self.high = int32(nrOfPulses)
        #self.low = int32(2)
        self.high = int32(2)
        self.low = int32(nrOfPulses)
        return True
        
    def LoadOne(self, axis, value):
        self._log.debug("LoadOne(%d, %f): Entering...", axis, value)
        self.time = value
        self.mainTask = TaskHandle()
        DAQmxErrChk(nidaqmx.DAQmxCreateTask("MainTask",byref(self.mainTask)))
        DAQmxErrChk(nidaqmx.DAQmxSetReadAutoStart(self.mainTask,False))
        DAQmxErrChk(nidaqmx.DAQmxCreateCOPulseChanTicks(self.mainTask, "Dev1/ctr0,Dev1/ctr1,Dev1/ctr2,Dev1/ctr3", "Channel_0,Channel_1,Channel_2,Channel_3", self.source, DAQmx_Val_High, delay, self.low, self.high))
        DAQmxErrChk(nidaqmx.DAQmxCfgImplicitTiming(self.mainTask, DAQmx_Val_FiniteSamps, nrOfPulses))
        DAQmxErrChk(nidaqmx.DAQmxSetStartTrigType(self.mainTask, DAQmx_Val_DigEdge))
        DAQmxErrChk(nidaqmx.DAQmxSetDigEdgeStartTrigSrc(self.mainTask, "/Dev1/PFI0"))
        DAQmxErrChk(nidaqmx.DAQmxSetDigEdgeStartTrigEdge(self.mainTask, DAQmx_Val_Rising))
    