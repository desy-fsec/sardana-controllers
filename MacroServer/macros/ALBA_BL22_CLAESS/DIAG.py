import time
import PyTango

from sardana.macroserver.macro import Macro, Type
from macro_utils.icepap import *
from macro_utils.motors import moveToHardLim

class diag_homing_vert(Macro):
    """ 
    This macro does homing of vertical slits of the BL22-CLAESS Diagnostic Module.
    Homing procedure is done in 3 steps:
    1. Top blade is moved to its positive hardware limit and bottom blade is moved to its negative hardware limit (simultaneously).
    2. Icepap homing procedure is started looking for home in the following directions:
       - top blade moving negative
       - bottom blade moving positive
    3. When top blade finds its home, it is stopped and bottom continues in the same direction as before.
    In case of successfully homing of both blades macro returns True, in all other cases it returns False.
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    TOP_NAME = 'oh_diag_top'
    BOTTOM_NAME = 'oh_diag_bottom'
    
    TOP_HOMING_DIR = -1
    BOTTOM_HOMING_DIR = 1

    GROUP_STRICT = False

    def prepare(self, *args, **opts):
        self.top = self.getObj(self.TOP_NAME, type_class=Type.Motor)
        self.bottom = self.getObj(self.BOTTOM_NAME, type_class=Type.Motor)
        top_pos = PyTango.AttributeProxy(self.TOP_NAME + '/position')
        bottom_pos = PyTango.AttributeProxy(self.BOTTOM_NAME + '/position')
        top_pos_conf = top_pos.get_config()
        bottom_pos_conf = bottom_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_top_max = top_pos_conf.max_value
        self.old_bottom_min = bottom_pos_conf.min_value
        top_pos_conf.max_value = '9.999E+003'
        bottom_pos_conf.min_value = '-9.999E+003'
        top_pos.set_config(top_pos_conf)
        bottom_pos.set_config(bottom_pos_conf)

    def run(self, *args, **opts):        
        
        try:
            info_dict = {self.TOP_NAME:(self.top, 999, 1), self.BOTTOM_NAME:(self.bottom, -999, -1)}
            while len(info_dict):
                motorsOnLim = moveToHardLim(self, info_dict.values())
                for mot in motorsOnLim:
                    info_dict.pop(mot)
            
            top_info = create_motor_info_dict(self.top, self.TOP_HOMING_DIR)
            bottom_info = create_motor_info_dict(self.bottom, self.BOTTOM_HOMING_DIR)    
            
            res = home_group_strict(self, [top_info, bottom_info])
            if res and top_info['homed']:
                self.debug('Motor %s successfully homed.' % top_info['motor'].alias())
                res = home(self, [bottom_info])
                if res and bottom_info['homed']:
                    self.debug('Motor %s successfully homed.' % bottom_info['motor'].alias())
                    self.info('DIAG vertical slits successfully homed.')
                    return True
                else:
                    self.debug('Motor %s did not find home as the second one.' % bottom_info['motor'].alias())
                    self.error('DIAG vertical slits homing failed.')
                    return False
            else:
                self.debug('Motor %s did not find home as the first one.' % bottom_info['motor'].alias())
                self.error('DIAG vertical slits homing failed.')
                return False
          
        finally:
            #@TODO: remove this comment when serializaiton prolem fixed
            #self.debug('Unmasking software limits...')
            top_pos = PyTango.AttributeProxy(self.TOP_NAME + '/position')
            bottom_pos = PyTango.AttributeProxy(self.BOTTOM_NAME + '/position')
            top_pos_conf = top_pos.get_config()
            bottom_pos_conf = bottom_pos.get_config()
            top_pos_conf.max_value = self.old_top_max
            bottom_pos_conf.min_value = self.old_bottom_min
            top_pos.set_config(top_pos_conf)
            bottom_pos.set_config(bottom_pos_conf)
        

class diag_homing_hori(Macro):
    """ 
    This macro does homing of horizontal slits of the BL22-CLAESS Diagnostic Module.
    Homing procedure is done in 3 steps:
    1. Right blade is moved to its positive limit and left blade is moved to its negative limit(simultaneously).
    2. Icepap homing procedure is started looking for home in the following directions:
       - right blade moving negative
       - left blade moving positive
    3. When right blade finds its home, it is stopped and left continues in the same direction as before.
    In case of successfully homing of both blades macro returns True, on all other cases it return False.
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    RIGHT_NAME = 'oh_diag_right'
    LEFT_NAME = 'oh_diag_left'
    
    RIGHT_HOMING_DIR = -1
    LEFT_HOMING_DIR = 1

    def prepare(self, *args, **opts):

        self.right = self.getObj(self.RIGHT_NAME, type_class=Type.Motor)
        self.left = self.getObj(self.LEFT_NAME, type_class=Type.Motor)
        right_pos = PyTango.AttributeProxy(self.RIGHT_NAME + '/position')
        left_pos = PyTango.AttributeProxy(self.LEFT_NAME + '/position')
        right_pos_conf = right_pos.get_config()
        left_pos_conf = left_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_right_max = right_pos_conf.max_value
        self.old_left_min = left_pos_conf.min_value
        right_pos_conf.max_value = '9.999E+003'
        left_pos_conf.min_value = '-9.999E+003'
        right_pos.set_config(right_pos_conf)
        left_pos.set_config(left_pos_conf)
        
        self.right_max = right_pos_conf.max_value
        self.left_min = left_pos_conf.min_value     
        self.debug("Right motor max position: %s" % self.right_max)
        self.debug("Left motor min position: %s" % self.left_min)


    def run(self, *args, **opts):        
        try:
            info_dict = {self.RIGHT_NAME:(self.right, 999, 1), self.LEFT_NAME:(self.left, -999, -1)}
            while len(info_dict):
                motorsOnLim = moveToHardLim(self, info_dict.values())
                for mot in motorsOnLim:
                    info_dict.pop(mot)
            
            right_info = create_motor_info_dict(self.right, self.RIGHT_HOMING_DIR)
            left_info = create_motor_info_dict(self.left, self.LEFT_HOMING_DIR)    
            
            res = home_group_strict(self, [right_info, left_info])
            if res and right_info['homed']:
                self.debug('Motor %s successfully homed.' % right_info['motor'].alias())
                res = home(self, [left_info])
                if res and left_info['homed']:
                    self.debug('Motor %s successfully homed.' % left_info['motor'].alias())
                    self.info('DIAG horizontal slits successfully homed.')
                    return True
                else:
                    self.debug('Motor %s did not find home as the second one.' % left_info['motor'].alias())
                    self.error('DIAG horizontal slits homing failed.')
                    return False
            else:
                self.debug('Motor %s did not find home as the first one.' % left_info['motor'].alias())
                self.error('DIAG horizontal slits homing failed.')
                return False
            
        finally:
            #@TODO: remove this comment when serializaiton prolem fixed
            #self.debug('Unmasking software limits...')
            right_pos = PyTango.AttributeProxy(self.RIGHT_NAME + '/position')
            left_pos = PyTango.AttributeProxy(self.LEFT_NAME + '/position')
            right_pos_conf = right_pos.get_config()
            left_pos_conf = left_pos.get_config()
            right_pos_conf.max_value = self.old_right_max
            left_pos_conf.min_value = self.old_left_min
            right_pos.set_config(right_pos_conf)
            left_pos.set_config(left_pos_conf)


class diag_homing_foil(Macro):
    """ 
    This macro does homing of foil holder of the BL22-CLAESS Diagnostic Module.
    Homing procedure is done in 2 steps:
    1. Foil holder is moved to its negative limit.
    2. Icepap homing procedure is started looking for home in the positive direction.
    In case of successfully homing macro returns True, on all other cases it return False.
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    FOIL_NAME = 'oh_diag_foil_z'
    FOIL_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        
        self.foil = self.getObj(self.FOIL_NAME, type_class=Type.Motor) 
        foil_pos = PyTango.AttributeProxy(self.FOIL_NAME + '/position')
        foil_pos_conf = foil_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_foil_min = foil_pos_conf.min_value
        foil_pos_conf.min_value = '-9.999E+003'
        foil_pos.set_config(foil_pos_conf)

    def run(self, *args, **opts):        
        try:
            info_dict = {self.FOIL_NAME:(self.foil, -999, -1)}
            motorsOnLim = moveToHardLim(self, info_dict.values())
            if motorsOnLim[0] != self.FOIL_NAME: 
                self.error("Foil holder could not reach its negative limit.")
                return False
            foil_info = create_motor_info_dict(self.foil, self.FOIL_HOMING_DIR)
            ret = home(self, [foil_info])
            if ret == True:
                self.info("Foil holder successfully homed.")
                return True
            else: 
                self.error("Foil holder could not find home.")
                return False 
        
        finally:
            #@TODO: remove this comment when serializaiton prolem fixed
            #self.debug('Unmasking software limits...')
            foil_pos = PyTango.AttributeProxy(self.FOIL_NAME + '/position')
            foil_pos_conf = foil_pos.get_config()
            foil_pos_conf.min_value = self.old_foil_min
            foil_pos.set_config(foil_pos_conf)
        