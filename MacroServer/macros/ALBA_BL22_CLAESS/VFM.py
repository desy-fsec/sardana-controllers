import time
import PyTango

from macro import Macro, Type
#from icepap import home_group_strict, home_group, create_motor_info_dict
from macro_utils.motors import moveToPosHardLim, moveToNegHardLim
from macro_utils.icepap import *
            
class vfm_homing_vert(Macro):
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

    JACK1_NAME = 'oh_vfm_jack1'
    JACK2_NAME = 'oh_vfm_jack2'
    JACK3_NAME = 'oh_vfm_jack3'

    JACK1_HOMING_DIR = -1
    JACK2_HOMING_DIR = -1
    JACK3_HOMING_DIR = -1

    GROUP_STRICT = True

    def prepare(self, *args, **opts):
        self.limits = args[0].lower()
        if not self.limits in ('soft','hard'):
            self.error("""limits parameter is expected to be 'soft' or 'hard'""")
            return False
        
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
        if self.limits == 'hard': 
            self.debug('Masking software limits...')
            self.old_jack1_max = jack1_pos_conf.max_value
            self.old_jack2_max = jack2_pos_conf.max_value
            self.old_jack3_max = jack3_pos_conf.max_value
            jack1_pos_conf.max_value = '9.999E+003'
            jack2_pos_conf.max_value = '9.999E+003'
            jack3_pos_conf.max_value = '9.999E+003'
            jack1_pos.set_config(jack1_pos_conf)
            jack2_pos.set_config(jack2_pos_conf)
            jack3_pos.set_config(jack3_pos_conf)
        
        self.jack1_max = jack1_pos_conf.max_value
        self.jack2_max = jack2_pos_conf.max_value
        self.jack3_max = jack3_pos_conf.max_value
        
        self.debug("Jack1 motor max position: %s" % self.jack1_max)
        self.debug("Jack2 motor max position: %s" % self.jack2_max)
        self.debug("Jack3 motor max position: %s" % self.jack3_max)

    def run(self, *args, **opts):        
        try:
            motors_pos_dict = {self.jack1:float(self.jack1_max), self.jack2:float(self.jack2_max), self.jack3:float(self.jack3_max)}
            while len(motors_pos_dict):
                motorsOnPosLim = moveToPosHardLim(self, motors_pos_dict)
                for m in motorsOnPosLim:
                    motors_pos_dict.pop(m)
            jack1_info = create_motor_info_dict(self.jack1, self.JACK1_HOMING_DIR)
            jack2_info = create_motor_info_dict(self.jack2, self.JACK2_HOMING_DIR)
            jack3_info = create_motor_info_dict(self.jack3, self.JACK3_HOMING_DIR)
            
            self.aborted = False
            res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
            if res and jack2_info['homed']:
                self.debug('Motor %s successfully homed.' % jack2_info['motor'].alias())
                res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
                if res and jack1_info['homed']:
                    self.debug('Motor %s successfully homed.' % jack1_info['motor'].alias())
                    res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
                    if jack3_info['homed']:
                        self.debug('Motor %s successfully homed.' % jack3_info['motor'].alias())
                        self.info('VCM vertical jacks successfully homed.')
                        return True
                    else:
                        self.debug('Motor %s did not find home as the third one.' % jack3_info['motor'].alias())
                        self.error('VCM vertical jacks homing failed.')  
                        return False
                else:
                        self.debug('Motor %s did not find home as the second one.' % jack1_info['motor'].alias())
                        self.error('VCM vertical jacks homing failed.')  
                        return False
            else: 
                self.debug('Motor %s did not find home as the first one.' % jack2_info['motor'].alias())
                self.error('VCM vertical jacks homing failed.')  
                return False
        except Exception, e:
            #@TODO: abort all motion
            self.error(repr(e))
            raise e
        finally:
            if self.limits == 'hard':
                self.debug('Unmasking software limits...')
                jack1_pos = PyTango.AttributeProxy(self.JACK1_NAME + '/position')
                jack2_pos = PyTango.AttributeProxy(self.JACK2_NAME + '/position')
                jack3_pos = PyTango.AttributeProxy(self.JACK3_NAME + '/position')
                jack1_pos_conf = jack1_pos.get_config()
                jack2_pos_conf = jack2_pos.get_config()
                jack3_pos_conf = jack3_pos.get_config()
                jack1_pos_conf.max_value = self.old_jack1_max
                jack2_pos_conf.max_value = self.old_jack2_max
                jack3_pos_conf.max_value = self.old_jack3_max
                jack1_pos.set_config(jack1_pos_conf)
                jack2_pos.set_config(jack2_pos_conf)
                jack3_pos.set_config(jack3_pos_conf)
        
        #self.debug("Top motor max position: %s" % jack1_pos_conf.max_value)
        #self.debug("Bottom motor min position: %s" % bottom_mot_pos_conf.min_value)

    def on_abort(self):
        self.aborted = True

class vfm_homing_hori(Macro):
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

    X1_NAME = 'oh_vfm_x1'
    X2_NAME = 'oh_vfm_x2'

    X1_HOMING_DIR = 1
    X2_HOMING_DIR = 1

    GROUP_STRICT = True

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
            
            self.aborted = False
            res = home_group(self, [x1_info, x2_info])
            if res:
                self.debug('Motors successfully homed.')
                return False
        except Exception, e:
            #@TODO: abort all motion
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

    def on_abort(self):
        self.aborted = True