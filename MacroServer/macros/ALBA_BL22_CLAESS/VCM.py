import time
import PyTango

from macro import Macro, Type
#from icepap import home_group_strict, home_group, create_motor_info_dict
from macro_utils.motors import moveToPosHardLim, moveToNegHardLim
from macro_utils.icepap import *
            
class vcm_homing_vert(Macro):
    """ 
    This macro does the homing of vertical jacks BL22-CLAESS VCM(Vertical Collimating Mirror).
    Homing procedure is done in 4 steps:
  

    1. First of all software limits of pitch and roll pseudomotors are masked. 
    2. Simultaneous move all the jacks to their hardware positive limits.
       (whenever any of the jacks reaches its limit, simultaneous motion is continue with the rest of them, 
       until all of them are at the positive limit)
    3. When all of them reached extreams Icepap homing routine is started (GROUP STRICT) for all of the jacks
       simultaneously - in negative direction. (whenever any of the jacks is stopped by a STOP command, 
       a limit switch or an alarm condition, all the other axes in the group are forced to stop immediately)
       The Icepap homing routine is repeated until all three jacks finds their homes.
    4. After everything software limits of pitch and roll pseudomotors are unmasked.

    In case of successfully homing of all jacks macro returns True, in all other cases it return False
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    JACK1_NAME = 'oh_vcm_jack1'
    JACK2_NAME = 'oh_vcm_jack2'
    JACK3_NAME = 'oh_vcm_jack3'
    PITCH_NAME = 'oh_vcm_pitch'
    ROLL_NAME  = 'oh_vcm_roll'

    JACK1_HOMING_DIR = -1
    JACK2_HOMING_DIR = -1
    JACK3_HOMING_DIR = -1

    def prepare(self, *args, **opts):
       
        self.jack1 = self.getObj(self.JACK1_NAME, type_class=Type.Motor)
        self.jack2 = self.getObj(self.JACK2_NAME, type_class=Type.Motor)
        self.jack3 = self.getObj(self.JACK3_NAME, type_class=Type.Motor)

        pitch_pos = PyTango.AttributeProxy(self.PITCH_NAME + '/position')
        roll_pos = PyTango.AttributeProxy(self.ROLL_NAME + '/position')

        pitch_pos_conf = pitch_pos.get_config()
        roll_pos_conf = roll_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_pitch_max = pitch_pos_conf.max_value
        self.old_pitch_min = pitch_pos_conf.min_value
        self.old_roll_max = roll_pos_conf.max_value
        self.old_roll_min = roll_pos_conf.min_value
        
        pitch_pos_conf.max_value = '9.999E+003'
        pitch_pos_conf.min_value = '-9.999E+003'
        roll_pos_conf.max_value = '9.999E+003'
        roll_pos_conf.min_value = '-9.999E+003'
        
        pitch_pos.set_config(pitch_pos_conf)
        roll_pos.set_config(roll_pos_conf)
        
    def run(self, *args, **opts):        
        try:
            motors_pos_dict = {self.jack1:999, self.jack2:999, self.jack3:999}
            while len(motors_pos_dict):
                motorsOnPosLim = moveToPosHardLim(self, motors_pos_dict)
                for m in motorsOnPosLim:
                    motors_pos_dict.pop(m)
            jack1_info = create_motor_info_dict(self.jack1, self.JACK1_HOMING_DIR)
            jack2_info = create_motor_info_dict(self.jack2, self.JACK2_HOMING_DIR)
            jack3_info = create_motor_info_dict(self.jack3, self.JACK3_HOMING_DIR)
            info_dicts = [jack1_info, jack2_info, jack3_info]
            res = home_group_strict(self, info_dicts)
            if res and jack1_info['homed']:
                self.debug('Motor %s successfully homed.' % jack1_info['motor'].alias())
                res = home_group_strict(self, info_dicts)
                if res and jack2_info['homed']:
                    self.debug('Motor %s successfully homed.' % jack2_info['motor'].alias())
                    if jack3_info['homed']:
                        self.debug('Motor %s successfully homed.' % jack3_info['motor'].alias())
                        self.info('VCM vertical jacks successfully homed.')
                        return True
                    else:
                        res = home_group_strict(self, info_dicts)
                        if res and jack3_info['homed']:
                            self.debug('Motor %s successfully homed.' % jack3_info['motor'].alias())
                            self.info('VCM vertical jacks successfully homed.')
                            return True
                        else:
                            self.debug('Motor %s did not find home as the second one.' % jack3_info['motor'].alias())
                            self.error('VCM vertical jacks homing failed.')  
                            return False
                else: 
                    self.debug('Motor %s did not find home as the second one.' % jack2_info['motor'].alias())
                    self.error('VCM vertical jacks homing failed.')  
                    return False
            else:
                self.debug('Motor %s did not find home as the first one.' % jack1_info['motor'].alias())
                self.error('VCM vertical jacks homing failed.')  
                return False
                return False
        except Exception, e:
            self.error(repr(e))
            raise e
        finally:
            self.debug('Unmasking software limits...')
            pitch_pos = PyTango.AttributeProxy(self.PITCH_NAME + '/position')
            roll_pos = PyTango.AttributeProxy(self.ROLL_NAME + '/position')

            pitch_pos_conf = pitch_pos.get_config()
            roll_pos_conf = roll_pos.get_config()

            pitch_pos_conf.max_value = self.old_pitch_max
            pitch_pos_conf.min_value = self.old_pitch_min
            roll_pos_conf.max_value = self.old_roll_max
            roll_pos_conf.min_value = self.old_roll_min

            pitch_pos.set_config(pitch_pos_conf)
            roll_pos.set_config(roll_pos_conf)

class vcm_homing_hori(Macro):
    """ 
    This macro does the homing of vertical jacks BL22-CLAESS VFM(Vertical Focusing Mirror).
    Homing procedure is done in 3 steps:

    1. Simultaneously move all the jacks to their positive limits(software or hardware)
       Whenever any of the jacks reaches its limit, simultaneous motion is continue with the rest of them. 
    2. When all of them reached extreams Icepap homing routine is started (GROUP STRICT) for all of the jack
       simultaneously - in negative direction. Whenever any of the jacks is stopped by a STOP command, 
       a limit switch or an alarm condition, all the other axes in the group are forced to stop immediately.

    In case of successfully homing of all jacks macro returns True, in all other cases it return False
    """

    param_def = [
        ['limits', Type.String, 'soft', 'Type of limits used in homing: soft or hard']
    ]
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    X1_NAME = 'oh_vcm_x1'
    X2_NAME = 'oh_vcm_x2'

    X1_HOMING_DIR = 1
    X2_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        self.limits = args[0].lower()
        if not self.limits in ('soft','hard'):
            self.error("""limits parameter is expected to be 'soft' or 'hard'""")
            return False
        
        self.x1 = self.getObj(self.X1_NAME, type_class=Type.Motor)
        self.x2 = self.getObj(self.X2_NAME, type_class=Type.Motor)

        x1_pos = PyTango.AttributeProxy(self.X1_NAME + '/position')
        x2_pos = PyTango.AttributeProxy(self.X2_NAME + '/position')
        
        x1_pos_conf = x1_pos.get_config()
        x2_pos_conf = x2_pos.get_config()

        #here we mask software limits, to allow reaching hardware limits
        if self.limits == 'hard': 
            self.debug('Masking software limits...')
            self.old_x1_min = x1_pos_conf.min_value
            self.old_x2_min = x2_pos_conf.min_value
            x1_pos_conf.min_value = '-9.999E+003'
            x2_pos_conf.min_value = '-9.999E+003'
            x1_pos.set_config(x1_pos_conf)
            x2_pos.set_config(x2_pos_conf)
        
        self.x1_min = x1_pos_conf.min_value
        self.x2_min = x2_pos_conf.min_value
        
        self.debug("X1 motor min position: %s" % self.x1_min)
        self.debug("X2 motor min position: %s" % self.x2_min)

    def run(self, *args, **opts):        
        try:
            motors_pos_dict = {self.x1:float(self.x1_min), self.x2:float(self.x2_min)}
            while len(motors_pos_dict):
                motorsOnNegLim = moveToNegHardLim(self, motors_pos_dict)
                for m in motorsOnNegLim:
                    motors_pos_dict.pop(m)
            x1_info = create_motor_info_dict(self.x1, self.X1_HOMING_DIR)
            x2_info = create_motor_info_dict(self.x2, self.X2_HOMING_DIR)
            
            res = home_group(self, [x1_info, x2_info])
            if res:
                self.debug('Motors successfully homed.')
                return False
        except Exception, e:
            self.error(repr(e))
            raise e
        finally:
            if self.limits == 'hard':
                self.debug('Unmasking software limits...')
                x1_pos = PyTango.AttributeProxy(self.X1_NAME + '/position')
                x2_pos = PyTango.AttributeProxy(self.X2_NAME + '/position')
                x1_pos_conf = x1_pos.get_config()
                x2_pos_conf = x2_pos.get_config()
                x1_pos_conf.min_value = self.old_x1_min
                x2_pos_conf.min_value = self.old_x2_min
                x1_pos.set_config(x1_pos_conf)
                x2_pos.set_config(x2_pos_conf)
        
        #self.debug("Top motor max position: %s" % x1_pos_conf.max_value)
        #self.debug("Bottom motor min position: %s" % bottom_mot_pos_conf.min_value)