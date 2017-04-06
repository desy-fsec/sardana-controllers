import PyTango

from sardana import State,
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.controller import TriggerGateController
from sardana.pool.controller import Type, Description,

from bl22dcmlib import energies4encoders

PMAC_REGISTERS = {'MotorDir': 4080, 'StartBuffer': 4081, 'RunProgram': 4082,
                  'NrTriggers': 4083, 'Index': 4084, 'StartPos': 4085,
                  'PulseWidth': 4086, 'AutoInc': 4087}

class BL22DcmTurboPmacPositionTGCtrl(TriggerGateController):
    """
    Tigger Gate contoller base on the turbo pmac of BL22. It use the new
    version of the PLC0 (git@git.cells.es:controls/bl22_turbopmac.git #7de2327)
    """

    organization = "ALBA-Cells"
    gender = "TriggerGate"
    model = "PMAC"
    MaxDevice = 1

    # The properties used to connect to the PMAC motor controller
    ctrl_properties = {
        'PMACDevice': {
            Type: str,
            Description: 'The PMAC device associated to the axis/motors',},
        'EnergyDSName': {
            Type: str,
            Description: 'Energy pseudomotor Tango device',},
        'BraggDSName': {
            Type: str,
            Description: 'Bragg motor Tango device',},
        'XtalIORDSNanme': {
            Type: str,
            Description: 'Crystal IORegister Tango device',},
        'VCMPitchDSName': {
            Type: str,
            Description: 'VCM pitch pseudomotor Tango device',},
        'BraggDSName': {
            Type: str,
            Description: 'Bragg motor Tango device',},
    }

    axis_attributes = {}

    def __init__(self, inst, props, *args, **kwargs):
        """
        """
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug('PMACPositionTriggerGateController init....')
        self.pmac = PyTango.DeviceProxy(self.TurboPmacDSName)
        self.energy = PyTango.DeviceProxy(self.EnergyDSName)
        self.bragg = PyTango.DeviceProxy(self.BraggDSName)
        self.vcm_pitch = PyTango.DeviceProxy(self.VCMPitchDSName)
        self.xtal = PyTango.DeviceProxy(self.XtalIORDSName)

    def AddDevice(self, axis):
        """
        """
        pass

    def DeleteDevice(self, axis):
        """
        """
        pass

    def SynchOne(self, axis, configuration):
        """
        Set axis configuration.
        """
        self._log.debug("SynchOne(): Entering...")

        group = configuration[0]
        initial = group[SynchParam.Initial][SynchDomain.Position]
        active = group[SynchParam.Active][SynchDomain.Position]
        total = group[SynchParam.Total][SynchDomain.Position]

        if total > 0:
            motor_dir = 1
        else:
            motor_dir = -1

        bragg_spu = self.bragg.read_attribute('step_per_unit').value
        bragg_offset = self.bragg.read_attribute('offset').value
        bragg_pos = self.bragg.read_attribute('position').value
        bragg_enc = float(self.pmac.GetMVariable(101))
        vcm_pitch_rad = self.vcm_pitch.read_attribute('position').value/1000
        xtal_value = self.xtal.read_attribute('value').value

        if xtal_value == 311:
            xtal_d_attr = 'dSi311'
            xtal_offset_attr = 'angularOffsetSi311'
        else:
            xtal_d_attr = 'dSi111'
            xtal_offset_attr = 'angularOffsetSi111'

        xtal_d = self.energy.read_attribute(xtal_d_attr).value
        xtal_offset = self.energy.read_attribute(xtal_offset_attr)


        self.pmac.SetPVariable([PMAC_REGISTERS['MotorDir'], motor_dir])
        self.pmac.SetPVariable([PMAC_REGISTERS['PulseWidth'], 10])
        # Program to generate and capture triggers at the same time.
        self.pmac.SetPVariable([PMAC_REGISTERS['RunProgram'], 3])
        # configuring position capture control
        self.pmac.SetIVariable([7012, 2])
        # configuring position capture flag select
        self.pmac.SetIVariable([7013, 3])
        # after enabling position capture, M117 is set to 1, forcing readout
        # of M103, to reset it, so PLC0 won't copy outdated data
        self.pmac.GetMVariable(103)
        # enabling plc0 execution
        self.pmac.SetIVariable([5, 3])



    def StateOne(self, axis):
        """
        Get the trigger/gate state
        """
        try:
            m = int(self.pmac.GetMVariable(3300))
        except PyTango.DevFailed, e:
            msg = "StateOne(%d): Could not verify state of the " \
                  "device: %s.\nException: %s" % \
                  (axis, self.TurboPmacDeviceName, e)
            self._log.error(msg)
            state = State.Unknown
            status = msg
            # value 0 means that plc0 is enabled, and value 1 means that plc0
            # is disabled
        if bool(m):
            state = State.On
            status = "Plc0 is disabled"
        else:
            state = State.Moving
            status = "Plc0 is enabled"

        return state, status


    def StartOne(self, axis):
        """Overwrite the StarOne method
        """
        self.pmac.command_inout("EnablePLC", 0)


    def AbortOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('AbortOne(%d): entering...' % axis)
        # TODO: the trigger circuit should be turn off?

