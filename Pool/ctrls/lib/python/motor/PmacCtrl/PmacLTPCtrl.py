import PyTango
from poolcontroller import PmacController

class PmacLTPController(PmacController):
    """This class is the Tango Sardana motor controller for the Pmac motor controller device in LTP."""

    def StateOne(self, axis):
        self._log.info('RETURNING THE STATE OF AXIS %d'%axis)
        state = PyTango.DevState.ON
        switchstate = 0
        status = "No limits are active, motor is in position"
        if not bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d40" % axis))))):
               state = PyTango.DevState.MOVING
               status = '\nThe motor is moving'
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d21" % axis))))):
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the negative/positive limit is activated'
               switchstate += 4
        if bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d22" % axis))))):
               state = PyTango.DevState.ALARM
               status = '\nAt least one of the negative/positive limit is activated'
               switchstate += 2
        if not bool(int(self.pmacEth.command_inout("GetMVariable",(int("%d39" % axis))))):
               state = PyTango.DevState.FAULT
               status = '\nMotor's amplifier is not enabled'
	
        return (state, status, switchstate)
