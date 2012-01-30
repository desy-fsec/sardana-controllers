import time
import PyTango

from sardana.macroserver.macro import Macro, Type
from macro_utils.motors import moveToPosHardLim, moveToNegHardLim
from macro_utils.icepap import *

class dcm_homing_vert(Macro):
    """ 
    This macro does the homing of vertical jacks of BL22-CLAESS DCM(Double Crystal Monochromator).
    Homing procedure is done in 3 steps:

    1. Simultaneously move all the jacks to their negative limits(software or hardware)
       Whenever any of the jacks reaches its limit, simultaneous motion is continue with the rest of them. 
    2. When all of them reached extreams Icepap homing routine is started (GROUP STRICT) for all of the jacks
       simultaneously - in positive direction. Whenever any of the jacks is stopped by a STOP command, 
       a limit switch or an alarm condition, all the other axes in the group are forced to stop immediately.

    In case of successfully homing of all jacks macro returns True, in all other cases it return False
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    JACK1_NAME = 'oh_dcm_jack1'
    JACK2_NAME = 'oh_dcm_jack2'
    JACK3_NAME = 'oh_dcm_jack3'

    JACK1_HOMING_DIR = 1
    JACK2_HOMING_DIR = 1
    JACK3_HOMING_DIR = 1

    GROUP_STRICT = True

    def prepare(self, *args, **opts):
        self.jack1 = self.getObj(self.JACK1_NAME, type_class=Type.Motor)
        self.jack2 = self.getObj(self.JACK2_NAME, type_class=Type.Motor)
        self.jack3 = self.getObj(self.JACK3_NAME, type_class=Type.Motor)

        jack1_pos = PyTango.AttributeProxy(self.JACK1_NAME + '/position')
        jack2_pos = PyTango.AttributeProxy(self.JACK2_NAME + '/position')
        jack3_pos = PyTango.AttributeProxy(self.JACK3_NAME + '/position')
        
        jack1_pos_conf = jack1_pos.get_config()
        jack2_pos_conf = jack2_pos.get_config()
        jack3_pos_conf = jack3_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
         
        self.debug('Masking software limits...')
        self.old_jack1_min = jack1_pos_conf.min_value
        self.old_jack2_min = jack2_pos_conf.min_value
        self.old_jack3_min = jack3_pos_conf.min_value
        jack1_pos_conf.min_value = '-9.999E+003'
        jack2_pos_conf.min_value = '-9.999E+003'
        jack3_pos_conf.min_value = '-9.999E+003'
        jack1_pos.set_config(jack1_pos_conf)
        jack2_pos.set_config(jack2_pos_conf)
        jack3_pos.set_config(jack3_pos_conf)
        
        self.jack1_min = jack1_pos_conf.min_value
        self.jack2_min = jack2_pos_conf.min_value
        self.jack3_min = jack3_pos_conf.min_value
        
        self.debug("Jack1 motor min position: %s" % self.jack1_min)
        self.debug("Jack2 motor min position: %s" % self.jack2_min)
        self.debug("Jack3 motor min position: %s" % self.jack3_min)

    def run(self, *args, **opts):        
        try:
            motors_pos_dict = {self.jack1:float(self.jack1_min), self.jack2:float(self.jack2_min), self.jack3:float(self.jack3_min)}
            while len(motors_pos_dict):
                motorsOnNegLim = moveToNegHardLim(self, motors_pos_dict)
                for m in motorsOnNegLim:
                    motors_pos_dict.pop(m)
            jack1_info = create_motor_info_dict(self.jack1, self.JACK1_HOMING_DIR)
            jack2_info = create_motor_info_dict(self.jack2, self.JACK2_HOMING_DIR)
            jack3_info = create_motor_info_dict(self.jack3, self.JACK3_HOMING_DIR)
            
            res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
            if res and jack1_info['homed']:
                self.debug('Motor %s successfully homed.' % jack1_info['motor'].alias())
                res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
                if res and jack2_info['homed']:
                    self.debug('Motor %s successfully homed.' % jack2_info['motor'].alias())
                    res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
                    if jack3_info['homed']:
                        self.debug('Motor %s successfully homed.' % jack3_info['motor'].alias())
                        self.info('DCM vertical jacks successfully homed.')
                        return True
                    else:
                        self.debug('Motor %s did not find home as the third one.' % jack3_info['motor'].alias())
                        self.error('DCM vertical jacks homing failed.')  
                        return False
                else:
                        self.debug('Motor %s did not find home as the second one.' % jack2_info['motor'].alias())
                        self.error('DCM vertical jacks homing failed.')  
                        return False
            else: 
                self.debug('Motor %s did not find home as the first one.' % jack1_info['motor'].alias())
                self.error('DCM vertical jacks homing failed.')  
                return False
        finally:
            #self.debug('Unmasking software limits...')
            jack1_pos = PyTango.AttributeProxy(self.JACK1_NAME + '/position')
            jack2_pos = PyTango.AttributeProxy(self.JACK2_NAME + '/position')
            jack3_pos = PyTango.AttributeProxy(self.JACK3_NAME + '/position')
            jack1_pos_conf = jack1_pos.get_config()
            jack2_pos_conf = jack2_pos.get_config()
            jack3_pos_conf = jack3_pos.get_config()
            jack1_pos_conf.min_value = self.old_jack1_min
            jack2_pos_conf.min_value = self.old_jack2_min
            jack3_pos_conf.min_value = self.old_jack3_min
            jack1_pos.set_config(jack1_pos_conf)
            jack2_pos.set_config(jack2_pos_conf)
            jack3_pos.set_config(jack3_pos_conf)

class dcm_homing_hori(Macro):
    """ 
    This macro does the homing of horizontal translation of BL22-CLAESS DCM (Double Crystal Monochromator).
    Homing procedure is done in 2 steps:

    1. Move lateral translation motor to its negative limit.
       
    2. When it reaches extream, Icepap homing routine is started in positive direction. 
       Whenever motor is stopped by a STOP command, a limit switch or an alarm condition, 
       homing routine is stop immediately.

    In case of successful homing macro returns True, in all other cases it return False
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    X_NAME = 'oh_dcm_x'
   
    X_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        self.x = self.getObj(self.X_NAME, type_class=Type.Motor)

        x_pos = PyTango.AttributeProxy(self.X_NAME + '/position')
        x_pos_conf = x_pos.get_config()

        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_x_min = x_pos_conf.min_value
        x_pos_conf.min_value = '-9.999E+003'
        x_pos.set_config(x_pos_conf)
        
        self.x_min = x_pos_conf.min_value
        
        #self.debug("X motor min position: %s" % self.x_min)

    def run(self, *args, **opts):        
        try:
            motors_pos_dict = {self.x:float(self.x_min)}
            while len(motors_pos_dict):
                motorsOnNegLim = moveToNegHardLim(self, motors_pos_dict)
                for m in motorsOnNegLim:
                    motors_pos_dict.pop(m)
            x_info = create_motor_info_dict(self.x, self.X_HOMING_DIR)
           
            res = home(self, [x_info])
            if res:
                self.info('DCM horizontal translation successfully homed.')
                return True
            else: 
                self.error('DCM horizontal homing failed.')
                return False
        finally:
            #@TODO: uncomment this line when fixed serialization problem
            #self.debug('Unmasking software limits...')
            x_pos = PyTango.AttributeProxy(self.X_NAME + '/position')
            x_pos_conf = x_pos.get_config()
            x_pos_conf.min_value = self.old_x_min
            x_pos.set_config(x_pos_conf)
        

class dcm_startup(Macro):
    """ After each power-up (or PMAC reset) the system must execute a start-up procedure during which
    the Bragg motor is phased (Forced or Soft Phased), motors are homed to their home positions and
    motors assigned into appropriate PMAC coordinate system. 
    
    This macro will call Pmac's PLC - AN AUTOMATED SYSTEM STARTUP PLC (PLC 6) which has
    been created to automate the execution of all these tasks in correct sequence. This will reduce
    downtime and also reduce possibility of error from the operators. 
 
    """
    param_def = [
        ['phasing_mode', Type.String, "soft", 'Phasing mode: soft or forced']
    ]
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]
    env = ('PmacEth',)
    
    def prepare(self, phasing_mode):
        phasing_mode = phasing_mode.lower()
        if not phasing_mode in ["soft", "forced"]:
            self.error("""phasing_mode parameter is expected to be 'soft' or 'forced'""")
            return False
        PMAC_DEVICE_NAME = self.getEnv("PmacEth")
        try:
            self.pmacEth = PyTango.DeviceProxy(PMAC_DEVICE_NAME)
        except DevFailed,e:
            self.error("PmacEth DeviceProxy cannot be created. PmacEth environment variable is wrong")
            
        
    def run(self, phasing_mode):
#        This can be used to check state of motors (in position)
#        self.pool = self.motor.getPoolObj()
#        bragg_mot = self.pool.getPoolElement("dcm_bragg")
#        perp_mot = self.pool.getPoolElement("dcm_perp")
        
        self.pmacEth.command_inout("EnablePLC", 6)
        self.debug("""Command 'EnablePLC 6' was send to Pmac""")
        time.sleep(2)
        #ReadyForPhasing - P199 variable
        p199 = self.pmacEth.command_inout("GetPVariable", 199)
        self.debug("ReadyForPhasing (P199) = %f" % p199)
        if p199 != 1.0:
            self.error("DCM is not ready for phasing, exiting...")
            return False
        phasing_mode = phasing_mode.lower()
        if phasing_mode == "soft":
            #SoftPhasing - P57
            self.pmacEth.command_inout("SetPVariable", [57,1])
            self.debug("""Command 'P57=1 (SoftPhasing=1' was send to Pmac""")
        else:
            #ForcedPhasing - P58
            self.pmacEth.command_inout("SetPVariable", [58,1])
            self.debug("""Command 'P58=1 (ForcedPhasing=1)' was send to Pmac""")

        #M3306 monitors PLC6 Enabled/Disabled status 0.0 - Enabled, 1.0 - Disabled
        m3306 = 0.0
        while (m3306 == 0.0):
            time.sleep(1)
            m3306 = self.pmacEth.command_inout("GetMVariable",3306)
     
        #SystemHomed - P73
        p73 = self.pmacEth.command_inout("GetPVariable", 73)
        if p73:
            self.info("System homed successfully. DCM is ready for working. Exiting...")
            return True
        else:
            #p117 Bragg Phased Flag
            p117 = self.pmacEth.command_inout("GetPVariable", 117)
            #p69 Process Timeout Flag
            p69 = self.pmacEth.command_inout("GetPVariable", 69)
            #m68 Process Skipped Flag
            m68 = self.pmacEth.command_inout("GetMVariable", 68)
            if not p117:
                self.warning("Bragg motor phasing failed.")
            if p69:
                self.warning("Process timeout.")
            if m68:
                self.warning("Process skipped.")    
            self.info("System could not be homed. DCM is not ready for working. Please rerun macro. Exiting...")
            return False
                
    def on_abort(self):
        pass
    
class dcm_pre_energy_move(Macro):
    """ This macro should be run before every energy move. 
    However before scanning it is enough to run it only once. 
    It aborts all motion and checks correct coordinate system definition:
        &1#1->X#3->Y"""
        
    env = ('PmacEth',)
    
    def prepare(self):
        PMAC_DEVICE_NAME = self.getEnv("PmacEth")
        try:
            self.pmacEth = PyTango.DeviceProxy(PMAC_DEVICE_NAME)
        except DevFailed,e:
            self.error("PmacEth DeviceProxy cannot be created. PmacEth environment variable is wrong.")
            
    def run(self):
        self.pmacEth.command_inout("SendCtrlChar", "A")
        self.info("All motion activities were aborted.")
        bragg_ans = self.pmacEth.command_inout("OnlineCmd", "&1#1->")
        bragg_ok = bragg_ans.endswith("X") 
        if bragg_ok:
            self.debug("Bragg motor (first axis) is correctly assigned to the coordinate system.")
        else:
            self.warning("Bragg motor (first axis) is not correctly assigned to the coordinate system.")
        perp_ans = self.pmacEth.command_inout("OnlineCmd", "&1#3->")
        perp_ok = perp_ans.endswith("Y") 
        if perp_ok:
            self.debug("Perpendicular motor (third axis) is correctly assigned to the coordinate system.")
        else:
            self.warning("Perpendicular motor (third axis) is not correctly assigned to the coordinate system.")
        if bragg_ok and perp_ok:
            self.info("All motors are correctly assigned to coordinate system. DCM ready for energy move.")
        else:
            self.error("Coordination system needs to be reassigned. Doing it now...")
            self.pmacEth.command_inout("OnlineCmd","undefine all")
            self.pmacEth.command_inout("OnlineCmd", "&1#1->X#3->Y")
            self.info("Coordination system reassigned.")
        return
            
        
        
            
            
            
        
         

