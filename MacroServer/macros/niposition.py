import logging, time, numpy
import PyTango

from macro import *
from pynidaqmx.nidaqmx import *

nidaqmx = loadNidaqmx()

class mv_x4_profile(Macro):
    '''This macro allows to profile motion of a sardana motor. It expect a quadrature signal (x4 encoded) hooked to 
       specified counter of NI6602 counter card. NI6602 card must be present in pc where MacroServer is running.
       Counter card will start sampling incoming quadrature signal before the motion was started 
       and will stop sampling when motion is already stopped. 
       After acquisition it postprocess acquired data to calculate ripple.
       '''
    param_def = [
                 [ 'motor', Type.Motor, None, 'Motor to move'],
                 [ 'pos', Type.Float, None, 'Position to move to'],
                 [ 'sampling_freq', Type.Integer, None, 'At which frequency sample a quadrature signal'], 
                 [ 'file', Type.String, None, 'File to store data' ],
                 [ 'counter', Type.String, None, 'Counter in NI6602 card']
                ]

    def prepare(self, *args, **kwargs):
        self.motor = args[0]
        self.pos = args[1]
        sampling_freq = args[2]
        if sampling_freq == 0:
            raise Exception('Sampling frequency must be different than 0')
        filename = args[3]
        counter = args[4].split('/')
        if len(counter) != 2:
            raise Exception('Counter has to specify device and counter e.g. Dev1/ctr1')
        self.device = counter[0]
        self.counter = counter[1]
        if self.counter == 'ctr0':
            raise Exception('Counter ctr0 is preserved as a sampling source. Use another counter')
        self.fileObj = open(filename, 'w')
        
        try:
            #trigger task variables
            self.triggerTask = TaskHandle()
            uInt32Array2 = uInt32 * 2
            self.triggerData = uInt32Array2(uInt32(0xffffffff), uInt32(0x0))
            self.triggerSamples = int32(2)
            self.triggerAutostart = bool32(1)
            self.triggerTimeout = float64(1)
            self.triggerWrittenSamples = int32()

            #position task variables            
            self.positionTask = TaskHandle()
            self.positionSamples = []
            AUX_BUFF_SIZE = 10000
            uInt32Array = uInt32 * AUX_BUFF_SIZE 
            self.positionData = uInt32Array()
            self.positionDataSize = uInt32(AUX_BUFF_SIZE)
            positionZidxEnable = bool32(0)
            positionZidxVal = float64(0.0)
            positionPulsesPerDist = float64(1.0)
            positionInitialPos = float64(0.0)            
            positionSamplingRate = float64(sampling_freq)
            self.positionSampsPerChanToAcquire = uInt64(AUX_BUFF_SIZE)
            self.positionSampsPerChanToRead = int32(10)
            self.positionSampsPerChanRead = int32()
            self.positionReadTimeout = float64(1)

            #pulse train variables
            self.pulseTrainTask = TaskHandle()
            pulseTrainDelay = int32(0)
            pulseTrainLow = 72000000/sampling_freq
            pulseTrainHigh = 8000000/sampling_freq
            self.debug("Sampling with a pulse train of high: %d and low: %d ticks" % (pulseTrainHigh, pulseTrainLow))
            pulseTrainLow = int32(pulseTrainLow)
            pulseTrainHigh = int32(pulseTrainHigh)
            pulseTrainTicks = uInt64(10)

            #triggering task
            self.DAQmxErrChk(nidaqmx.DAQmxCreateTask("TriggerTask",byref(self.triggerTask)))
            self.DAQmxErrChk(nidaqmx.DAQmxCreateDOChan(self.triggerTask,"Dev1/port0/line1","",DAQmx_Val_ChanForAllLines))
              
            #pulse train task
            self.DAQmxErrChk(nidaqmx.DAQmxCreateTask("PulseTrainTask",byref(self.pulseTrainTask)))
            self.DAQmxErrChk(nidaqmx.DAQmxSetReadAutoStart(self.pulseTrainTask,False))

            self.DAQmxErrChk(nidaqmx.DAQmxCreateCOPulseChanTicks(self.pulseTrainTask, "Dev1/ctr0", "Channel_0", "80MHzTimebase", DAQmx_Val_Low, pulseTrainDelay, pulseTrainLow, pulseTrainHigh))
            self.DAQmxErrChk(nidaqmx.DAQmxCfgImplicitTiming(self.pulseTrainTask, DAQmx_Val_ContSamps, pulseTrainTicks))

            self.DAQmxErrChk(nidaqmx.DAQmxSetStartTrigType(self.pulseTrainTask, DAQmx_Val_DigEdge))
            self.DAQmxErrChk(nidaqmx.DAQmxSetDigEdgeStartTrigSrc(self.pulseTrainTask, "/"+self.device+"/PFI1"))
            self.DAQmxErrChk(nidaqmx.DAQmxSetDigEdgeStartTrigEdge(self.pulseTrainTask, DAQmx_Val_Rising))
            self.debug('Before configuring position tasks')
            
            #position task
            counterName = 'Dev1/%s' % self.counter                
            self.DAQmxErrChk(nidaqmx.DAQmxCreateTask("PositionTask",byref(self.positionTask)))
            self.DAQmxErrChk(nidaqmx.DAQmxCreateCILinEncoderChan(self.positionTask, counterName, "PositionChannel", DAQmx_Val_X4, positionZidxEnable, positionZidxVal, DAQmx_Val_AHighBHigh, DAQmx_Val_Ticks, positionPulsesPerDist, positionInitialPos, None))
            self.DAQmxErrChk(nidaqmx.DAQmxCfgSampClkTiming(self.positionTask,"/"+self.device+"/PFI36",positionSamplingRate,DAQmx_Val_Rising,DAQmx_Val_ContSamps,self.positionSampsPerChanToAcquire))
            
            #starting tasks
            self.debug('Starting NI6602 tasks')
            self.DAQmxErrChk(nidaqmx.DAQmxStartTask(self.triggerTask))
            self.debug("Starting pulse train task")
            self.DAQmxErrChk(nidaqmx.DAQmxStartTask(self.pulseTrainTask))
            self.debug("Starting position task")
            self.DAQmxErrChk(nidaqmx.DAQmxStartTask(self.positionTask))
        except:
            self.debug("Exception in prepare")
            self.stopAndClearAllTasks()
            raise

    def run(self, *args, **kwargs):
        try:    
            motionId = None
            motion = self.getMotion([self.motor])            
            #triggering pulse train
            self.debug("Starting sampling of the positions.")
            self.DAQmxErrChk(nidaqmx.DAQmxWriteDigitalU32(self.triggerTask, self.triggerSamples, self.triggerAutostart, self.triggerTimeout, DAQmx_Val_GroupByChannel, self.triggerData, byref(self.triggerWrittenSamples), None))
            self.debug("Starting motion.")
            motionId = motion.startMove([self.pos])
            self.debug("Motion started")
            state = motion.readState()
            self.debug("State %s", state)
            while state == PyTango.DevState.MOVING:
                state = motion.readState()
                self.debug("State %s" % repr(state))            
                self.debug("Reading samples")
                #reading in U32 because of bug in counting in negative direction
                self.DAQmxErrChk(nidaqmx.DAQmxReadCounterU32(self.positionTask, DAQmx_Val_Auto, self.positionReadTimeout, self.positionData, self.positionDataSize, byref(self.positionSampsPerChanRead), None))
                nrOfAcquiredSamples = self.positionSampsPerChanRead.value
                self.debug("Acquired %d samples\n" % nrOfAcquiredSamples)
                if nrOfAcquiredSamples == 0:
                    continue
                acquiredSamples = self.positionData[:nrOfAcquiredSamples]
                self.positionSamples.extend(acquiredSamples)
                self.debug("Clearing auxiliary data")
                self.positionSampsPerChanRead = int32()
                for item in self.positionData:
                    item = float64()
                self.debug("After clearing auxiliary data")
            #data postprocessing:    
            #casting from uInt32 to int32 - because of bug in counting in negative direction
            #also going back from ctypes to pure python types
            #calculating velocity ripple
            self.positionSamples = [int32(sample).value for sample in self.positionSamples]
            self.positionSamples = numpy.array(self.positionSamples)
            self.velocityRipples = numpy.zeros(len(self.positionSamples))
            self.velocityRipples = self.positionSamples[1:] - self.positionSamples[0:-1]
            #dumping results to the file
            for position, ripple in zip(self.positionSamples, self.velocityRipples):
                sampleStr = str(sample)
                self.fileObj.write("%d\t%d\n" % (position, ripple))
        finally:
            if motionId != None:
                motion.waitMove(motionId)
            self.stopAndClearAllTasks()
            self.fileObj.close()
    
    def stopAndClearAllTasks(self):
        triggerTask = getattr(self, 'triggerTask', None)
        if triggerTask != None and triggerTask != TaskHandle():
            nidaqmx.DAQmxStopTask(triggerTask)
            nidaqmx.DAQmxClearTask(triggerTask)
        pulseTrainTask = getattr(self, 'pulseTrainTask', None)
        if pulseTrainTask != None and pulseTrainTask != TaskHandle():
            nidaqmx.DAQmxStopTask(pulseTrainTask)
            nidaqmx.DAQmxClearTask(pulseTrainTask)
        positionTask = getattr(self, 'positionTask', None)
        if positionTask != None and positionTask != TaskHandle():
            nidaqmx.DAQmxStopTask(positionTask)
            nidaqmx.DAQmxClearTask(positionTask)
        self.debug('Cleared all tasks.')
        fileObj = getattr(self, 'fileObj', None)
        if isinstance(fileObj, file):
            fileObj.close()
            self.debug('Data file closed')

    def DAQmxErrChk(self, status):
        if status < 0: 
            BUFF_LEN = 2048
            charArray = c_char * BUFF_LEN
            errBuff = charArray('\0')
            nidaqmx.DAQmxGetExtendedErrorInfo(errBuff,uInt32(BUFF_LEN))
            errStr = ""
            for c in errBuff:
                errStr+=c
            #in case of already created tasks, stopping and clearing them
            self.error(errStr)
            self.stopAndClearAllTasks()
            raise Exception("NI6602 card reported an error:\n%s" % errStr)
  
