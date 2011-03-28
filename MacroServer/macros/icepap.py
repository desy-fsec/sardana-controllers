"""
    Macro library containing icepap related macros for the macro
    server Tango device server as part of the Sardana project.
"""

#import macro
import pyIcePAP
import time
from macro import *


class ipap_get_closed_loop(Macro):
    """Returns current closed loop configuration value for a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to request (must be and IcePAP motor)"],
    ]

    icepap_ctrl = "IcePAPCtrl.py"

    def prepare(self, motor):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type icepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s is not an IcePAP motor" % str(motor))

    def run(self, motor):
        """Run macro"""

        if motor.read_attribute("ClosedLoop").value:
            status = "ON"
        else:
            status = "OFF"

        self.output("Closed loop is %s in motor %s" % (status, str(motor)))
        return status


class ipap_set_closed_loop(Macro):
    """Enables/Disables closed loop in a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to configure (must be and IcePAP motor)"],
       ["ON/OFF", Type.String, None, "ON to enable / OFF to disable closed loop"]
    ]

    icepap_ctrl = "IcePAPCtrl.py"
    actions = ("ON", "OFF")

    def prepare(self, motor, action):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type icepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s is not an IcePAP motor" % str(motor))

        #check that "action" is valid
        if action.upper() in self.actions:
            pass
        else:
            raise Exception("action must be one of: %s" % str(self.actions))

    def run(self, motor, action):
        """Run macro"""
        action = action.upper()

        if action == "ON":
            closed_loop = True
        else:
            closed_loop = False
        #read back closed loop status to check it's the one we have just set
        motor.write_attribute("ClosedLoop",closed_loop)
        closed_loop_rb = motor.read_attribute("ClosedLoop").value
        if closed_loop == closed_loop_rb:
            self.output("Closed loop %s correctly set in motor %s" % (action,str(motor)))
            return True
        else:
            self.output("WARNING!: read back from the controller (%s) didn't match the requested parameter (%s)" %  (str(closed_loop_rb),str(closed_loop)))
            return False


class ipap_get_steps_per_turn(Macro):
    """Returns current steps per turn value for a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to request (must be and IcePAP motor)"],
    ]

    icepap_ctrl = "IcePAPCtrl.py"
    config_command = "%d:CONFIG"
    get_command = "%d:?CFG ANSTEP"

    def prepare(self, motor):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type icepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s doesn't support closed loop" % str(motor))

    def run(self, motor):
        """Run macro"""
        #get axis number, controller name and pool
        axis = motor.getAxis()
        controller = motor.getControllerName()
        pool = motor.getPoolObj()

        #write command to icepap
        cmd = self.get_command % axis
        result = pool.SendToController([controller,cmd])

        #read result and return value
        steps = result.split()[2]
        self.output("% s steps per turn in motor %s" % (steps, str(motor)))
        return int(steps)


class ipap_set_steps_per_turn(Macro):
    """Set steps per turn value for a given motor"""

    param_def = [
       ["motor",  Type.Motor,  None, "motor to configure (must be and IcePAP motor)"],
       ["steps", Type.Integer, None, "steps per turn value"]
    ]

    icepap_ctrl = "IcePAPCtrl.py"
    config_command = "%d:CONFIG" 
    set_command = "%d:CFG ANSTEP %d"
    get_command = "%d:?CFG ANSTEP"
    sign_command = "%d:CONFIG %s"

    def prepare(self, motor, steps):
        """Check that parameters for the macro are correct"""
        motorOk = False

        #check that motor controller is of type icepap
        controller = motor.getControllerName()
        pool = motor.getPoolObj()
        ctrls_list = pool.read_attribute("ControllerList").value
        for ctrl in ctrls_list:
            found = ctrl.find(controller)
            if found >= 0:
                if ctrl.find(self.icepap_ctrl) >= 0:
                    motorOk = True
                break
        if not motorOk:
            raise Exception("Motor %s is not an IcePAP motor" % str(motor))

    def run(self, motor, steps):
        """Run macro"""
        #get axis number, controller name and pool
        axis = motor.getAxis()
        controller = motor.getControllerName()
        pool = motor.getPoolObj()

        #set controller in config mode
        cmd = self.config_command % axis
        result = pool.SendToController([controller,cmd])

        #set the requested steps per turn
        cmd = self.set_command % (axis,steps)
        result = pool.SendToController([controller,cmd])

        #sign the change in icepap controller
        cmd = self.sign_command % (axis,"Steps per turn changed on user request from macro %s on %s" % (str(self.__class__.__name__),str(time.ctime())))
        result = pool.SendToController([controller,cmd])

        #read back steps per turn to confirm command worked OK
        cmd = self.get_command % axis
        result = pool.SendToController([controller,cmd])
        steps_rb = int(result.split()[2])
        if steps == steps_rb:
            self.output("Steps per turn %d correctly set in motor %s" % (steps,str(motor)))
            return True
        else:
            self.output("WARNING!: read back from the controller (%s) didn't match the requested parameter (%d)" %  (str(result),steps))
            return False

class ipap_homing(Macro):
    """Macro to do the homing procedure in more than one axis at the same time.
       Given a list of motors to do the home and the direction (in pool motor sense) in which you want
       to move, this macro will move all the motors at the same time waiting to 
       recieve the home signal.
       The macro ends when the home signal is detected or any axis receive an alarm
    """

    param_def = [
        ["strict",  Type.Boolean, False, "If performed strict homing."],         
        ['motor_direction_list',
        ParamRepeat(['motor', Type.Motor, None, 'Motor to perform the homing procedure.'],
                    ['direction', Type.Integer, None, 'Direction in which you will look for the home signal <-1|1>']),
        None, 'List of motors and homing directions.']
    ]

    result_def = [
        ['homed',  Type.Boolean, None, 'Motors homed state']
    ]
    
    CMD_HOME = '#home%s' #if pool throws the exception properly in case of starting the homing in config mode it doesn't need to start with #
    CMD_HOME_GROUP_STRICT = 'home group strict%s' 
    CMD_HOME_STAT = '?homestat%s'
    CMD_HOME_POS = '?homepos%s' #only works if all queried motors have found home 
    CMD_HOMEENC_ENCIN = '?homeenc encin%s' #only works if all queried motors have found home
    CMD_ABORT = 'abort%s'


    def prepare(self, *args, **opts):
        
        self.strict = args[0]
        self.motors = []

        motors_directions = args[1:]
        motors_axis_str = ''
        motors_directions_str = ''
        for motor_direction in motors_directions:
            motor = motor_direction[0]
            self.motors.append(motor)
            motor_axis = motor.getAxis()
            #if necessary we change homing direction from pool to icepap sense
            motor_sign = motor.getSign()
            direction = motor_direction[1] * motor_sign
            motors_directions_str += ' %d %d' % (motor_axis, direction)
            motors_axis_str += ' %d' % motor_axis 
        
        if self.strict:
            self.cmd_home = self.CMD_HOME_GROUP_STRICT % motors_directions_str
        else:
            self.cmd_home = self.CMD_HOME % motors_directions_str
        self.cmd_home_stat = self.CMD_HOME_STAT % motors_axis_str
        self.cmd_home_pos = self.CMD_HOME_POS % motors_axis_str
        self.cmd_abort = self.CMD_ABORT % motors_axis_str

        self.debug('Homing command: %s' % self.cmd_home)
        self.debug('Homing status command: %s' % self.cmd_home_stat)        
        
        #@todo: group motors by icepapcontrollers and perform motion on particular controllers
        first_motor = motors_directions[0][0]
        self.pool = first_motor.getPoolObj()
        self.ctrl_name = first_motor.getControllerName()
        self.home_pos_dict = {}
        self.debug('Pool: %s, Controller: %s' % (repr(self.pool), self.ctrl_name))

    def run(self, *args, **opts):
        self.info('Starting the homing procedure')
        self.execute_homing()

    def on_abort(self):
        self.aborted = True
        
    def execute_homing(self):
        self.aborted = False
        #@todo: pool should throw an exception in case of starting homing in a config mode and it should be caught here
        ans = self.pool.SendToController([self.ctrl_name , self.cmd_home])  
        if ans.startswith('HOME ERROR'):
            self.error(ans)
            return False
        while (not self.aborted):
            ans = self.pool.SendToController([self.ctrl_name, self.cmd_home_stat])
            home_stats = ans.split()[1::2]
            self.debug('Home stats: %s' % repr(home_stats))
            if self.strict:
                pass
            else:
                if any([stat == 'MOVING' for stat in home_stats]):
                    self.debug('Homing in progress...')
                elif any([stat == 'NOTFOUND' for stat in home_stats]):
                    ans = self.pool.SendToController([self.ctrl_name, self.cmd_home_pos])
                    self.debug(ans)
                    self.info('Homing precedure failed.')
                    return False
                else: 
                    ans = self.pool.SendToController([self.ctrl_name, self.cmd_home_pos])
                    home_positions = ans.split()[1:]
                    self.debug('Home positions: %s' % repr(home_positions))
                    for i,motor in enumerate(self.motors):
                        self.debug('Motor: %s, home position: %d' % (motor.getName(), int(home_positions[i])))
                    return True
            time.sleep(1)
