import time
import PyTango

from macro import Macro, Type
from macro_utils.icepap import *
from macro_utils.motors import moveToHardLim

class xbo_homing_hori(Macro):
    """ 
    This macro does homing of horizontal axis of XBPM situated in diagnostic module of BL04-MSPD.
    Homing procedure is done in 2 steps:

    1. Move motor to its positive limit.
       
    2. When it reaches extream, Icepap homing routine is started in negative direction. 
       Whenever motor is stopped by a STOP command, a limit switch or an alarm condition, 
       homing routine is stop immediately.

    In case of successful homing macro returns True, in all other cases it return False
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    MOT_NAME = 'xbo_h'
   
    MOT_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.mot = self.getObj(self.MOT_NAME, type_class=Type.Motor)

        mot_pos = PyTango.AttributeProxy(self.MOT_NAME + '/position')
        mot_pos_conf = mot_pos.get_config()

        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_mot_max = mot_pos_conf.max_value
        mot_pos_conf.max_value = '9.999E+003'
        mot_pos.set_config(mot_pos_conf)
        

    def run(self, *args, **opts):        
        try:
            info_dict = {self.MOT_NAME:(self.mot, 999, 1)}
            motorsOnLim = moveToHardLim(self, info_dict.values())
            if len(motorsOnLim) != 1 or motorsOnLim[0] != self.MOT_NAME:
                self.error("%s motor didn't get to it's positive limit. Homing failed." % self.mot.alias())
                return False
            mot_info = create_motor_info_dict(self.mot, self.MOT_HOMING_DIR)
            res = home(self, [mot_info])
            if res:
                self.info('%s motor successfully homed.' % self.mot.alias())
                return True
            else: 
                self.error('%s motor homing failed.' % self.mot.alias())
                return False
        finally:
            #@TODO: uncomment this line when fixed serialization problem
            #self.debug('Unmasking software limits...')
            mot_pos = PyTango.AttributeProxy(self.MOT_NAME + '/position')
            mot_pos_conf = mot_pos.get_config()
            mot_pos_conf.max_value = self.old_mot_max
            mot_pos.set_config(mot_pos_conf)

class xbo_homing_vert(Macro):
    """ 
    This macro does homing of vertical axis of XBPM situated in diagnostic module of BL04-MSPD.
    Homing procedure is done in 2 steps:

    1. Move motor to its positive limit.
       
    2. When it reaches extream, Icepap homing routine is started in negative direction. 
       Whenever motor is stopped by a STOP command, a limit switch or an alarm condition, 
       homing routine is stop immediately.

    In case of successful homing macro returns True, in all other cases it return False.
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    MOT_NAME = 'xbo_v'
   
    MOT_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.mot = self.getObj(self.MOT_NAME, type_class=Type.Motor)

        mot_pos = PyTango.AttributeProxy(self.MOT_NAME + '/position')
        mot_pos_conf = mot_pos.get_config()

        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_mot_max = mot_pos_conf.max_value
        mot_pos_conf.max_value = '9.999E+003'
        mot_pos.set_config(mot_pos_conf)
        

    def run(self, *args, **opts):        
        try:
            info_dict = {self.MOT_NAME:(self.mot, 999, 1)}
            motorsOnLim = moveToHardLim(self, info_dict.values())
            if len(motorsOnLim) != 1 or motorsOnLim[0] != self.MOT_NAME:
                self.error("%s motor didn't get to it's positive limit. Homing failed." % self.mot.alias())
                return False
            mot_info = create_motor_info_dict(self.mot, self.MOT_HOMING_DIR)
            res = home(self, [mot_info])
            if res:
                self.info('%s motor successfully homed.' % self.mot.alias())
                return True
            else: 
                self.error('%s motor homing failed.' % self.mot.alias())
                return False
        finally:
            #@TODO: uncomment this line when fixed serialization problem
            #self.debug('Unmasking software limits...')
            mot_pos = PyTango.AttributeProxy(self.MOT_NAME + '/position')
            mot_pos_conf = mot_pos.get_config()
            mot_pos_conf.max_value = self.old_mot_max
            mot_pos.set_config(mot_pos_conf)

            
class xbo_homing_foil(Macro):
    """ 
    This macro does homing of foil holder axis of XBPM situated in diagnostic module of BL04-MSPD.
    It will start looking for homing position into positive direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    MOT_NAME = 'xbo_foil'
    
    MOT_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        self.mot = self.getObj(self.MOT_NAME, type_class=Type.Motor)
        if self.mot.Limit_switches[1]:
            raise Exception('Motor %s is already at home position. Homing procedure can not be started.' % self.mot.alias())
        
    def run(self, *args, **opts):
        mot_info = create_motor_info_dict(self.mot, self.MOT_HOMING_DIR)
        info_dicts = [mot_info]
        try:
            res = home(self, info_dicts)
            if res == True:
                self.info('%s motor successfully homed.' % self.mot.alias())
            elif res == False:
                self.error('%s motor homing failed.'% self.mot.alias())
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e