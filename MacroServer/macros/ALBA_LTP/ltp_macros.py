from macro import Macro, Type
import time

################################################################################
#
# LTP related macros
#
################################################################################
PMAC_CTRL_TYPE = "PmacLTPCtrl.PmacLTPController"
ENABLLE_PLC_CMD_STR = "enableplc %d"
DISABLE_PLC_CMD_STR = "disableplc %d"
SET_P_VARIABLE_CMD_STR = "setpvariable %d %d"
GET_M_VARIABLE_CMD_STR = "getmvariable %d"

class LTP_homing(Macro):
    """ This macro is intended to be used for executing homing procedures for LTP.
    It receives as parameter motor to be homed.
    Aborting a macro will ask PMAC controller to abort enable PLC routine 
    as soon as possible (if PLC routine is in WHILE loop it will wait until it ends) 
    """

    
    param_def = [
        ['motor', Type.Motor, None, 'Motor name']
    ]
    
    result_def = [
        ['homed',  Type.Boole, None, 'Motor homed state']
    ]
    
    def run(self, motor):
    	self.motor = motor
        self.pool = self.motor.getPoolObj()
    	self.ctrl_name = self.motor.getControllerName()
    	self.ctrl_axis = self.motor.getAxis()
        
        #checking if this motor belongs to Pmac controller
        ctrls_list = self.pool.read_attribute("ControllerList")
        # line format: laop_pmac (PmacLTPCtrl.PmacLTPController/laop_pmac) - Motor Python ctrl (PmacLTPCtrl.py)
        for ctrl_line in ctrls_list:
            ctrl_line_splitted = ctrl_line.split()
            c_name = ctrl_line_splitted[0]
            if c_name == self.ctrl_name:
                c_type = ctrl_line.split()[1][1:-1].split("/")[0] 
            if  c_type !=  PMAC_CTRL_TYPE:
                self.error("""Couldn't start homing macro, this motor doesn't belong to Pmac Controller""")
                return False
        
        if self.ctrl_axis == 1: self.homing_plc_nr = 3
        elif self.ctrl_axis == 2: self.homing_plc_nr = 4
        else: 
            self.error("""Couldn't start homing macro, there is no PLC homing routine for this motor""")
            return False    
         
    	self.pool.SendToController([self.ctrl_name, ENABLLE_PLC_CMD_STR % homing_plc_nr])
    	self.pool.SendToController([self.ctrl_name, SET_P_VARIABLE_CMD_STR % (100, self.ctrl_axis)])
    	self.info('PLC homing routine for axis %d on controller %s started.' % (self.ctrl_axis, self.ctrl_name))
        
    	time.sleep(3)
    	mx40 = self.pool.SendToController([self.ctrl_name, GET_M_VARIABLE_CMD_STR % int('%d40' % self.ctrl_axis)])
    	while not float(mx40):
    	    time.sleep(1)
    	    mx40 = self.pool.SendToController([self.ctrl_name, GET_M_VARIABLE_CMD_STR % int('%d40' % self.ctrl_axis)])    
    	self.info('PLC homing routine for axis %d on controller %s finished.' % (self.ctrl_axis, self.ctrl_name))
        
    	if float(self.pool.SendToController([self.ctrl_name, GET_M_VARIABLE_CMD_STR % int('%d45' % self.ctrl_axis)])):
    	    self.info('Found home for axis %d' % self.ctrl_axis)
    	    return True
        
    	self.warning("""Couldn't find home for axis %d""" % self.ctrl_axis)
    	return False
        
    def on_abort(self):
        self.pool.SendToController([self.ctrl_name, DISABLE_PLC_CMD_STR % self.homing_plc_nr])
    	self.motor.abort()
    	self.info('PLC homing routine for axis %d on controller %s will be aborted as soon as possible.' % (self.ctrl_axis, self.ctrl_name))
	
	
