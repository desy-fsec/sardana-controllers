
import PyTango
from sardana import State
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.controller import (TriggerGateController, Type, Description,
                                     DefaultValue, Access, DataAccess,
                                     Memorize, Memorized, NotMemorized)

class TFG2TriggerGateController(TriggerGateController):
    MaxDevice = 8
    min_time = 1e-8
    
    ctrl_properties = {
        'tfg2DeviceName': {
            Type: str,
            Description: "TFG2 Tango device name"
        },
    }

    StateMap = {
        "IDLE" : State.On,
        "EXT-ARMED" : State.Standby,
        "RUNNING" : State.Running, # .Moving?
        "PAUSED" : State.Standby,
    }

    def __init__(self, inst, props, *args, **kwargs):
        """
        Construct the TriggerGateController and prepare controller
        properties.
        """
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self.tfg2 = PyTango.DeviceProxy(self.tfg2DeviceName)
        self.mask = 0
        
    def AddDevice(self, axis):
        """
        Add axis to the controller
        """
        if 0 <= axis < 8:
            self.mask |= 1 << axis
    
    def DeleteDevice(self, axis):
        """
        Remove axis from the controller
        """
        if 0 <= axis < 8:
            self.mask &= 0xFF - 1 << axis

    def StateOne(self, axis):
        """
        Get state from the channel and translate it to the Sardana state
        """
        self._log.debug('StateOne(%d): entering...' % axis)
        
        acqStatus = self.tfg2.read_attribute('AcqStatus').value
        status = self.tfg2.read_attribute('Progress').value
        if acqStatus in StateMap:
            state = StateMap[acqStatus]
        else:
            state = State.Unknown

        self._log.debug('StateOne(%d): returning (%s, %s)'\
                             % (axis, state, status))
        return state, status

    def ReadOne(self, axis):
        """Get the specified trigger value"""
        return None # TODO What is expected?

    def SynchOne(self, axis, configuration):
        """
        Set axis configuration.
        """
        self._log.debug('SynchOne(%d): entering...' % axis)

        self._tfgConfig()
        
        group = configuration[0]
        delay = group[SynchParam.Delay][SynchDomain.Time]
        active = group[SynchParam.Active][SynchDomain.Time]
        total = group[SynchParam.Total][SynchDomain.Time]
        latency = total - active
        repeats = group[SynchParam.Repeats]

        arg0 = '8' #TFG conf send cycles
        arg1 = '1' #1 cycle
        arg2 = ''
        arg3 = ''
        grp0 = '1 %f %f 0 %d 0 0' % (delay, active, self.mask)
        grpn = '%d %f %f 0 %d 0 0' % (repeats - 1, latency, active, self.mask)
        arg_end = '-1 0 0 0 0 0 0'
        tfg_config = [arg0, arg1, arg2, arg3, grp0, grpn, arg_end]
        self._log.debug('SynchOne(%d): groups %s' % (axis," ".join(tfg_config)))

        self.tfg2.SetupGroups(tfg_config)

        self._log.debug('SynchOne(%d): leaving...' % axis)
    
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
        acqStatus = self.tfg2.read_attribute('AcqStatus').value
        self.tfg2.Start()
        self._log.debug('StartOne(%d): leaving...' % axis)

    def AbortOne(self, axis):
        """
        Abort generation - stop the specified channel
        """
        self._log.debug('AbortOne(%d): entering...' % axis)
        self.tfg2.Stop()
        self._log.debug('AbortOne(%d): leaving...' % axis)

    def _tfgConfig(self):
        self.tfg2.SetupPort([0,7]) # 8bit inversion, 8bit drive series terminated
        self.tfg2.SetupCCMode(2) # bit2: scaler64
        self.tfg2.SetupCCChan([2,-1,0,0,0]) # 
        self.tfg2.SetupTFout([1,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
        self.tfg2.Enable()
        self.tfg2.Clear([0,0,0,10000,1,100])
