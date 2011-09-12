from macro import Macro, Type
import time

################################################################################
#
# LTP related macros
#
################################################################################
ENABLLE_PLC_CMD_STR = "enableplc %d"
DISABLE_PLC_CMD_STR = "disableplc %d"
SET_P_VARIABLE_CMD_STR = "setpvariable %d %d"
GET_M_VARIABLE_CMD_STR = "getmvariable %d"

class LTP_home(Macro):
    """ This macro runs homing procedures of LTP motors.
    It expects as a parameter motor name. However ony PmacLTPController motors will be accepted.
    Aborting macro will ask PMAC controller to abort enabled PLC routine as soon as possible 
    (if PLC routine is in WHILE loop it will wait until it ends).
    """

    param_def = [
        ['motor', Type.Motor, None, 'Motor name']
    ]
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]
    
    def run(self, motor):
    	self.motor = motor
        self.pool = self.motor.getPoolObj()
    	self.ctrl_name = self.motor.getControllerName()
    	self.ctrl_axis = self.motor.getAxis()
        #checking if this motor belongs to PmacLTPController
        controllerObj = self.pool.getObj("Controller", self.ctrl_name)
        controllerClassName = controllerObj.getClassName()
        if controllerClassName != "LtpTurboPmacController":
            self.error("Could not start homing macro. This Motor does not belong to PmacLTPController")
            return False       

        if self.ctrl_axis == 1: 
	    self.homing_plc_nr = 3
	    self.homing_plc_status_mvar = 3323
	    self.homing_status = 145
	    self.axis_ampl_mvar = 139
        elif self.ctrl_axis == 2: 
	    self.homing_plc_nr = 4
	    self.homing_plc_status_mvar = 3324
	    self.homing_status = 245
	    self.axis_ampl_mvar = 239
        else: 
            self.error("""Couldn't start homing macro, there is no PLC homing routine for this motor""")
            return False    
         
    	self.pool.SendToController([self.ctrl_name, ENABLLE_PLC_CMD_STR % self.homing_plc_nr])
    	self.pool.SendToController([self.ctrl_name, SET_P_VARIABLE_CMD_STR % (100, self.ctrl_axis)])
    	self.info('PLC homing routine for axis %d on controller %s started.' % (self.ctrl_axis, self.ctrl_name))
        
    	homing_plc_status = self.pool.SendToController([self.ctrl_name, GET_M_VARIABLE_CMD_STR % self.homing_plc_status_mvar])
	self.debug("Mvar %d = %s" % (self.homing_plc_status_mvar, homing_plc_status))
    	while not float(homing_plc_status):
	    axis_ampl_enabled = self.pool.SendToController([self.ctrl_name, GET_M_VARIABLE_CMD_STR % self.axis_ampl_mvar])
	    self.debug("Mvar %d = %s" % (self.axis_ampl_mvar, axis_ampl_enabled))
	    if not float(axis_ampl_enabled):
		self.error("Axis %d ampliefier disabled. Please reset PMAC and start homing macro again." % self.ctrl_axis)
		break
    	    time.sleep(1)
    	    homing_plc_status = self.pool.SendToController([self.ctrl_name, GET_M_VARIABLE_CMD_STR % self.homing_plc_status_mvar])    
	    self.debug("Mvar %d = %s" % (self.homing_plc_status_mvar, homing_plc_status))
       
    	if float(self.pool.SendToController([self.ctrl_name, GET_M_VARIABLE_CMD_STR % self.homing_status])):
	    self.info('Homing succeed for axis %d' % self.ctrl_axis)
	    return True
	else: 
	    self.error('Homing failed for axis %d' % self.ctrl_axis)
	    return False
        
    def on_abort(self):
	self.info("Axis %d motion was aborted. Please reset PMAC and start homing macro again." % self.ctrl_axis)
	#self.pool.SendToController([self.ctrl_name, DISABLE_PLC_CMD_STR % self.homing_plc_nr])
	#self.debug(DISABLE_PLC_CMD_STR % self.homing_plc_nr)
    	#self.info('PLC homing routine for axis %d on controller %s will be aborted as soon as possible.' % (self.ctrl_axis, self.ctrl_name))

class LTP_lift(Macro):
    """This macro is used to lift an axis of LTP motor.
    Each axis is represented by IORegister. 
    Lifting the axis will set values of IORegister to zeros."""
    
    param_def = [
       ['ioregister',      Type.IORegister,   None, 'IORegister to lift ']
    ]
    
    def run(self, ioregister):
        self.debug("ior name: " + ioregister.name())
        controllerName = ioregister.getControllerName()
        self.debug("controller name: %s" % controllerName)
        poolObj = ioregister.getPoolObj()
        controllerObj = poolObj.getObj("Controller", controllerName)
        controllerClassName = controllerObj.getClassName()
        self.debug("controller class name: %s" % controllerClassName)
        if controllerClassName != "PmacLTPIOController":
            self.warning("This IORegister does not belong to PmacLTPIOController")
            return
        ior_properties = ioregister.get_property(['axis'])
        axis = int(ior_properties['axis'][0])
        if axis == 1:
            self.warning("Axis: %d is read-only" % axis)
            return
        elif axis == 2 or axis == 3:
            self.debug("axis: %d" % axis)
            ioregister.writeValue(0)
            
class LTP_land(Macro):
    """This macro is used to lift an axis of LTP motor.
    Each axis is represented by IORegister. 
    Lifting the axis will set values of IORegister to zeros."""
    
    param_def = [
       ['ioregister',      Type.IORegister,   None, 'IORegister to lift ']
    ]
    
    def run(self, ioregister):
        self.debug("ior name: " + ioregister.name())
        controllerName = ioregister.getControllerName()
        self.debug("controller name: %s" % controllerName)
        poolObj = ioregister.getPoolObj()
        controllerObj = poolObj.getObj("Controller", controllerName)
        controllerClassName = controllerObj.getClassName()
        self.debug("controller class name: %s" % controllerClassName)
        if controllerClassName != "PmacLTPIOController":
            self.warning("This IORegister does not belong to PmacLTPIOController")
            return
        ior_properties = ioregister.get_property(['axis'])
        axis = int(ior_properties['axis'][0])
        if axis == 1:
            self.warning("Axis: %d is read-only" % axis)
            return
        elif axis == 2:
            ioregister.writeValue(63)
            self.debug("after writing 63")
        elif axis == 3:
            ioregister.writeValue(3)
            self.debug("after writing 3")
	
	
