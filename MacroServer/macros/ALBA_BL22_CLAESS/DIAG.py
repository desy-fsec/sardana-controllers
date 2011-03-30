import time
import PyTango

from macro import Macro, Type

class diag_homing_vert(Macro):
    """ 
    This macro does the homing of vertical slits of the BL22-CLAESS Diagnostic Module.
    Homing procedure is done in 3 steps:
    1. Top blade is moved to its positive limit(software or hardware)
    2. Bottom blade is moved to its negative limit(software or hardware)
    3. Icepap homing procedure is started looking for home in the follwing maner:
       - top blade moving negative
       - bottom blade moving positive
    In case of successfully homing of both blades macro returns True, on all other cases it return False
    """

    param_def = [
        ['limits', Type.String, 'soft', 'Type of limits used in homing: soft or hard']
    ]
    
#    result_def = [
#        ['homed',  Type.Bool, None, 'Motor homed state']
#    ]

    TOP_MOT = 'oh_diag_top'
    BOTTOM_MOT = 'oh_diag_bottom'
    
    TOP_HOMING_DIR = -1
    BOTTOM_HOMING_DIR = 1

    GROUP_STRICT = False

    def prepare(self, *args, **opts):
        self.limits = args[0].lower()
        if not self.limits in ('soft','hard'):
            self.error("""limits parameter is expected to be 'soft' or 'hard'""")
            return False
        top_mot_pos = PyTango.AttributeProxy(self.TOP_MOT + '/position')
        bottom_mot_pos = PyTango.AttributeProxy(self.BOTTOM_MOT + '/position')
        top_mot_pos_conf = top_mot_pos.get_config()
        bottom_mot_pos_conf = bottom_mot_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        if self.limits == 'hard': 
            self.debug('Masking software limits...')
            self.old_top_mot_max = top_mot_pos_conf.max_value
            self.old_bottom_mot_min = bottom_mot_pos_conf.min_value
            top_mot_pos_conf.max_value = '9.999E+003'
            bottom_mot_pos_conf.min_value = '-9.999E+003'
            top_mot_pos.set_config(top_mot_pos_conf)
            bottom_mot_pos.set_config(bottom_mot_pos_conf)
        
        self.top_mot_max = top_mot_pos_conf.max_value
        self.bottom_mot_min = bottom_mot_pos_conf.min_value     
        self.debug("Top motor max position: %s" % self.top_mot_max)
        self.debug("Bottom motor min position: %s" % self.bottom_mot_min)

    def run(self, *args, **opts):        
        #this motion is separeted because of limit activation which could breake a two motors simultaneous motion
        try:
            self.execMacro('mv', self.TOP_MOT, self.top_mot_max)
            self.execMacro('mv', self.BOTTOM_MOT, self.bottom_mot_min)
            return self.execMacro('ipap_homing', self.GROUP_STRICT, self.TOP_MOT, self.TOP_HOMING_DIR, self.BOTTOM_MOT, self.BOTTOM_HOMING_DIR)
        except:
            return False
        finally:
            if self.limits == 'hard':
                self.debug('Unmasking software limits...')
                top_mot_pos = PyTango.AttributeProxy(self.TOP_MOT + '/position')
                bottom_mot_pos = PyTango.AttributeProxy(self.BOTTOM_MOT + '/position')
                top_mot_pos_conf = top_mot_pos.get_config()
                bottom_mot_pos_conf = bottom_mot_pos.get_config()
                top_mot_pos_conf.max_value = self.old_top_mot_max
                bottom_mot_pos_conf.min_value = self.old_bottom_mot_min
                top_mot_pos.set_config(top_mot_pos_conf)
                bottom_mot_pos.set_config(bottom_mot_pos_conf)
        
        #self.debug("Top motor max position: %s" % top_mot_pos_conf.max_value)
        #self.debug("Bottom motor min position: %s" % bottom_mot_pos_conf.min_value)

    def on_abort(self):
        pass

class diag_homing_hor(Macro):
    """ 
    This macro does the homing of horizontal slits of the BL22-CLAESS Diagnostic Module.
    Homing procedure is done in 3 steps:
    1. Right blade is moved to its positive limit(software or hardware)
    2. Left blade is moved to its negative limit(software or hardware)
    3. Icepap homing procedure is started looking for home in the follwing maner:
       - right blade moving negative
       - left blade moving positive
    In case of successfully homing of both blades macro returns True, on all other cases it return False
    """

    param_def = [
        ['limits', Type.String, 'soft', 'Type of limits used in homing: soft or hard']
    ]
    
#    result_def = [
#        ['homed',  Type.Bool, None, 'Motor homed state']
#    ]

    RIGHT_MOT = 'oh_diag_right'
    LEFT_MOT = 'oh_diag_left'
    
    RIGHT_HOMING_DIR = -1
    LEFT_HOMING_DIR = 1

    GROUP_STRICT = False

    def prepare(self, *args, **opts):
        self.limits = args[0].lower()
        if not self.limits in ('soft','hard'):
            self.error("""limits parameter is expected to be 'soft' or 'hard'""")
            return False
        right_mot_pos = PyTango.AttributeProxy(self.RIGHT_MOT + '/position')
        left_mot_pos = PyTango.AttributeProxy(self.LEFT_MOT + '/position')
        right_mot_pos_conf = right_mot_pos.get_config()
        left_mot_pos_conf = left_mot_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        if self.limits == 'hard': 
            self.debug('Masking software limits...')
            self.old_top_mot_max = right_mot_pos_conf.max_value
            self.old_bottom_mot_min = left_mot_pos_conf.min_value
            right_mot_pos_conf.max_value = '9.999E+003'
            left_mot_pos_conf.min_value = '-9.999E+003'
            right_mot_pos.set_config(right_mot_pos_conf)
            left_mot_pos.set_config(left_mot_pos_conf)
        
        self.top_mot_max = right_mot_pos_conf.max_value
        self.bottom_mot_min = left_mot_pos_conf.min_value     
        self.debug("Right motor max position: %s" % self.top_mot_max)
        self.debug("Left motor min position: %s" % self.bottom_mot_min)

    def run(self, *args, **opts):        
        #this motion is separeted because of limit activation which could breake a two motors simultaneous motion
        try:
	    pass
            self.execMacro('mv', self.RIGHT_MOT, self.top_mot_max)
            self.execMacro('mv', self.LEFT_MOT, self.bottom_mot_min)
            return self.execMacro('ipap_homing', self.GROUP_STRICT, self.RIGHT_MOT, self.RIGHT_HOMING_DIR, self.LEFT_MOT, self.LEFT_HOMING_DIR)
        except:
            return False
        finally:
            if self.limits == 'hard':
                self.debug('Unmasking software limits...')
                right_mot_pos = PyTango.AttributeProxy(self.RIGHT_MOT + '/position')
                left_mot_pos = PyTango.AttributeProxy(self.LEFT_MOT + '/position')
                right_mot_pos_conf = right_mot_pos.get_config()
                left_mot_pos_conf = left_mot_pos.get_config()
                right_mot_pos_conf.max_value = self.old_top_mot_max
                left_mot_pos_conf.min_value = self.old_bottom_mot_min
                right_mot_pos.set_config(right_mot_pos_conf)
                left_mot_pos.set_config(left_mot_pos_conf)
        
        #self.debug("Right motor max position: %s" % right_mot_pos_conf.max_value)
        #self.debug("Left motor min position: %s" % left_mot_pos_conf.min_value)

    def on_abort(self):
        pass


class diag_homing_foil(Macro):
    """ 
    This macro does the homing of the foil holder of the BL22-CLAESS Diagnostic Module.
    Homing procedure is done in 2 steps:
    1. Foil holder is moved to its negative limit(software or hardware)
    2. Icepap homing procedure is started looking for home in the positive direction
    In case of successfully homing macro returns True, on all other cases it return False
    """

    param_def = [
        ['limits', Type.String, 'soft', 'Type of limits used in homing: soft or hard']
    ]
    
#    result_def = [
#        ['homed',  Type.Bool, None, 'Motor homed state']
#    ]

    GROUP_STRICT = 'False'
    FOIL_MOT = 'oh_diag_foil_z'
    FOIL_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        self.limits = args[0].lower()
        if not self.limits in ('soft','hard'):
            self.error("""Limits parameter is expected to be 'soft' or 'hard'""")
            return False
        foil_mot_pos = PyTango.AttributeProxy(self.FOIL_MOT + '/position')
        foil_mot_pos_conf = foil_mot_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        if self.limits == 'hard': 
            self.debug('Masking software limits...')
            self.old_foil_mot_min = foil_mot_pos_conf.min_value
            foil_mot_pos_conf.min_value = '-9.999E+003'
            foil_mot_pos.set_config(foil_mot_pos_conf)
        
        self.foil_mot_min = foil_mot_pos_conf.min_value
        self.debug("Foil motor min position: %s" % self.foil_mot_min)

    def run(self, *args, **opts):        
        try:
            self.execMacro('mv', self.FOIL_MOT, self.foil_mot_min)
            return self.execMacro('ipap_homing', self.GROUP_STRICT, self.FOIL_MOT, self.FOIL_HOMING_DIR)
        except:
            return False
        finally:
            if self.limits == 'hard':
                self.debug('Unmasking software limits...')
                foil_mot_pos = PyTango.AttributeProxy(self.FOIL_MOT + '/position')
                foil_mot_pos_conf = foil_mot_pos.get_config()
                foil_mot_pos_conf.min_value = self.old_foil_mot_min
                foil_mot_pos.set_config(foil_mot_pos_conf)
        
        #self.debug("Top motor min position: %s" % foil_mot_pos_conf.min_value)

    def on_abort(self):
        pass

