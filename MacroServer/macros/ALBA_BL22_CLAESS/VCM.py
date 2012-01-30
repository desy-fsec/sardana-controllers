import time
import PyTango

from sardana.macroserver.macro import Macro, Type

from macro_utils.motors import moveToHardLim
from macro_utils.icepap import *
            
class vcm_homing_vert(Macro):
    """ 
    This macro does homing of vertical jacks BL22-CLAESS VCM(Vertical Collimating Mirror).
    Homing procedure is done in 4 steps:
  

    1. First of all, software limits of pitch and roll pseudomotors are masked. 
    2. Simultaneous move all the jacks to their hardware positive limits.
       (whenever any of the jacks reaches its limit, simultaneous motion is continue with the rest of them, 
       until all of them are at the positive limit)
    3. When all of them reach extreams Icepap homing routine is started (GROUP STRICT) for all of the jacks
       simultaneously - in negative direction. (whenever any of the jacks is stopped by a STOP command, 
       a limit switch or an alarm condition, all the other axes in the group are forced to stop immediately)
       The Icepap homing routine is repeated until all three jacks find their homes.
    4. At the very end, software limits of pitch and roll pseudomotors are unmasked.

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
            info_dict = {self.JACK1_NAME:(self.jack1, 999, 1), self.JACK2_NAME:(self.jack2, 999, 1), self.JACK3_NAME:(self.jack3, 999, 1)}
            while len(info_dict):
                motorsOnLim = moveToHardLim(self, info_dict.values())
                for mot in motorsOnLim:
                    info_dict.pop(mot)

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
        except Exception, e:
            self.error(repr(e))
            raise e
        finally:
            #@TODO: Uncomment below line when serialization problem will be fixed
            #self.debug('Unmasking software limits...')
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
    This macro does homing of horizontal translations of BL22-CLAESS VCM(Vertical Collimating Mirror).
    Homing procedure is done in 2 steps:

    1. Simultaneously move of all the jacks to their negative hardware limits.
       Whenever any of the translations reaches its limit, simultaneous motion is continued with the second one. 
    2. When all of them reach extreams Icepap homing routine is started (GROUP) for both translations
       simultaneously - in positive direction. Whenever any of the translations is stopped by a STOP command, 
       a limit switch or an alarm condition, all the other axes in the group are forced to stop immediately.

    In case of successfully homing of both translations macro returns True, in all other cases it return False
    """

    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    X1_NAME = 'oh_vcm_x1'
    X2_NAME = 'oh_vcm_x2'

    X1_HOMING_DIR = 1
    X2_HOMING_DIR = 1

    def prepare(self, *args, **opts):        
        self.x1 = self.getObj(self.X1_NAME, type_class=Type.Motor)
        self.x2 = self.getObj(self.X2_NAME, type_class=Type.Motor)

        x1_pos = PyTango.AttributeProxy(self.X1_NAME + '/position')
        x2_pos = PyTango.AttributeProxy(self.X2_NAME + '/position')
        
        x1_pos_conf = x1_pos.get_config()
        x2_pos_conf = x2_pos.get_config()

        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_x1_min = x1_pos_conf.min_value
        self.old_x2_min = x2_pos_conf.min_value
        x1_pos_conf.min_value = '-9.999E+003'
        x2_pos_conf.min_value = '-9.999E+003'
        x1_pos.set_config(x1_pos_conf)
        x2_pos.set_config(x2_pos_conf)
        
    def run(self, *args, **opts):        
        try:
            #motors_pos_dict = {self.x1:float(self.x1_min), self.x2:float(self.x2_min)}
            #while len(motors_pos_dict):
                #motorsOnNegLim = moveToNegHardLim(self, motors_pos_dict)
                #for m in motorsOnNegLim:
                    #motors_pos_dict.pop(m)
            info_dict = {self.X1_NAME:(self.x1, -999, -1), self.X2_NAME:(self.x2, -999, -1)}
            while len(info_dict):
                motorsOnLim = moveToHardLim(self, info_dict.values())
                for mot in motorsOnLim:
                    info_dict.pop(mot)

            x1_info = create_motor_info_dict(self.x1, self.X1_HOMING_DIR)
            x2_info = create_motor_info_dict(self.x2, self.X2_HOMING_DIR)
            
            res = home_group(self, [x1_info, x2_info])
            if x1_info['homed']:
                self.debug('Motor %s successfully homed.' % x1_info['motor'].alias())
            else:
                self.debug('Motor %s could not find home.' % x1_info['motor'].alias())
            if x2_info['homed']:
                self.debug('Motor %s successfully homed.' % x2_info['motor'].alias())
            else:
                self.debug('Motor %s could not find home.' % x2_info['motor'].alias())
            if res == True:
                self.info('VCM lateral motors successfully homed.')
                return True
            else: 
                self.info('VCM lateral motors homing failed.')
                return False
        finally:
            #@TODO: Uncomment below line if the serialization problem will be fixed
            #self.debug('Unmasking software limits...')
            x1_pos = PyTango.AttributeProxy(self.X1_NAME + '/position')
            x2_pos = PyTango.AttributeProxy(self.X2_NAME + '/position')
            x1_pos_conf = x1_pos.get_config()
            x2_pos_conf = x2_pos.get_config()
            x1_pos_conf.min_value = self.old_x1_min
            x2_pos_conf.min_value = self.old_x2_min
            x1_pos.set_config(x1_pos_conf)
            x2_pos.set_config(x2_pos_conf)


class vcm_homing_bend(Macro):
    """ 
    This macro does homing of the bender motor of BL22-CLAESS Vertical Collimating Mirror.
    Homing procedure is started from current possition into negative direction.
    In case of successful homing macro returns True, on all other cases it returns False
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    MOT_NAME = 'oh_vcm_bend'
    
    HOMING_DIR = -1    

    def prepare(self, *args, **opts):
        self.mot = self.getObj(self.MOT_NAME, type_class=Type.Motor)
        if self.mot.Limit_switches[2]:
            raise Exception('Motor %s is already at home position. Homing procedure can not be started.' % self.mot.alias())

    def run(self, *args, **opts):        
        try:
            mot_info_dict = create_motor_info_dict(self.mot, self.HOMING_DIR)
            info_dicts = [mot_info_dict]
            res = home(self, info_dicts)
            if res == True:
                self.info('Bender of VCM successfully homed.')
            elif res == False:
                self.error('Bender of VCM homing failed.')
                return False
            else: 
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e