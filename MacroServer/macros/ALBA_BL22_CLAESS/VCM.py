import time
import PyTango

from macro import Macro, Type
from icepap import home_group_strict, create_motor_info_dict

def moveToPosHardLim(macro, motors_pos_dict):
    try:
        motors = motors_pos_dict.keys()
        positions = motors_pos_dict.values()
        #Checking positive limits state (maybe they were already active)
        motorsOnPosLim = []
        for m in motors:
            if m.Limit_switches[1]:
                macro.debug('Motor %s is already at the positive limit.', m.alias())
                motorsOnPosLim.append(m)
        if len(motorsOnPosLim): return motorsOnPosLim
        macro.debug('Moving motors: %s towards positive limit...', 
                   repr([m.alias() for m in motors_pos_dict.keys()]))
        for m,p in zip(motors,positions):
            macro.debug('Moving motor %s to position: %f).', m.alias(), p)
        motion = macro.getMotion(motors)
        motion.move(positions)
        #Checking stop code (if we reached positive limits)
        motorsWhichReachedPosLim = []
        for m in motors:
            if m.StatusStopCode == 'Limit+ reached':
                macro.debug('Motor %s reached its positive limit.', m.alias())
                motorsWhichReachedPosLim.append(m)
        return motorsWhichReachedPosLim
    except PyTango.DevFailed, e: 
        macro.error(repr(e))
        macro.error('Moving motors: %s to positive limits was interupted.', repr(motors))
        raise e
        
def moveToNegHardLim(macro, motors_pos_dict):
    try:
        motors = motors_pos_dict.keys()
        positions = motors_pos_dict.values()
        macro.debug('Moving motors: %s towards negative limit...', 
                   repr([m.alias() for m in motors_pos_dict.keys()]))
        for m,p in zip(motors,positions):
            macro.debug('Moving motor %s to position: %f).', m.alias(), p)
        motion = macro.getMotion(motors)
        motion.move(positions)
        for m in motors:
            if m.StatusStopCode == 'Limit- reached':
                macro.debug('Motor %s reached its negative limit.', m.alias())
                motors_pos_dict.pop(m)
        return m
    except PyTango.DevFailed, e: 
        macro.error('Moving motors: %s to positive limits was interupted.', repr(motors))
        raise e        
            
class vcm_homing_vert(Macro):
    """ 
    This macro does the homing of vertical jacks BL22-CLAESS VCM(Vertical Collimating Mirror).
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

    JACK1_NAME = 'oh_vcm_jack1'
    JACK2_NAME = 'oh_vcm_jack2'
    JACK3_NAME = 'oh_vcm_jack3'

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
            if res and jack1_info['homed']:
                self.debug('Motor %s successfully homed.' % jack1_info['motor'].alias())
                res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
                if res and jack2_info['homed']:
                    self.debug('Motor %s successfully homed.' % jack2_info['motor'].alias())
                    if jack3_info['homed']:
                        self.debug('Motor %s successfully homed.' % jack3_info['motor'].alias())
                        self.info('VCM vertical jacks successfully homed.')
                        return True
                    else:
                        res = home_group_strict(self, [jack1_info, jack2_info, jack3_info])
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