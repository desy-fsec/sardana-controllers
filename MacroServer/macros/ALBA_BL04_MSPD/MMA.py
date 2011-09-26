import time
import PyTango

from macro import Macro, Type
from macro_utils.motors import moveToPosHardLim, moveToNegHardLim
from macro_utils.icepap import *
            
class mma_homing_vert(Macro):
    """ 
    This macro does homing of vertical slits of White Beam Movable Masks situated in beamline's Front End.
    Homing procedure is done in 4 steps:
  

    1. First negative software limits of bottom and vgap motors are masked. 
    2. Simultaneous move of top and bottom motors towards their hardware negative limits.
       (they start simultaneous motion)
    3. When all of them reaches extreams Icepap homing routine is started (GROUP - see icepap_homing macro description) for top and bottom motors
       simultaneously - in positive direction. (whenever any of the these motors is stopped by a STOP command, 
       or an alarm condition, all the other axes in the group are forced to stop immediately)
       Homing routine is successful if both motors find home signal.
    4. At the end, software limits of bottom and vgap motors are unmasked.

    In case of successfully homing of all motors macro returns True, in all other cases it return False
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    MOVM_TOP = 'mma_t'
    MOVM_BOTTOM = 'mma_b'
    MOVM_VGAP = 'mma_v_gap'

    MOVM_TOP_HOMING_DIR = 1
    MOVM_BOTTOM_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        self.top = self.getObj(self.MOVM_TOP, type_class=Type.Motor)
        self.bottom = self.getObj(self.MOVM_BOTTOM, type_class=Type.Motor)

        bottom_pos = PyTango.AttributeProxy(self.MOVM_BOTTOM + '/position')
        vgap_pos = PyTango.AttributeProxy(self.MOVM_VGAP + '/position')

        bottom_pos_conf = bottom_pos.get_config()
        vgap_pos_conf = vgap_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_bottom_min = bottom_pos_conf.min_value
        self.old_vgap_min = vgap_pos_conf.min_value
        
        bottom_pos_conf.min_value = '-9.999E+003'
        vgap_pos_conf.min_value = '-9.999E+003'
        
        bottom_pos.set_config(bottom_pos_conf)
        vgap_pos.set_config(vgap_pos_conf)
        
    def run(self, *args, **opts):        
        try:
            motors_pos_dict = {self.top:-999, self.bottom:-999}
            while len(motors_pos_dict):
                motorsOnNegLim = moveToNegHardLim(self, motors_pos_dict)
                for m in motorsOnNegLim:
                    motors_pos_dict.pop(m)
            top_info = create_motor_info_dict(self.top, self.MOVM_TOP_HOMING_DIR)
            bottom_info = create_motor_info_dict(self.bottom, self.MOVM_BOTTOM_HOMING_DIR)
            info_dicts = [top_info, bottom_info]
            res = home_group(self, info_dicts)
            if res == True:
                self.info('Vertical movable mask slits (top,bottom) successfully homed.')
            elif res == False:
                self.error('Vertical movable mask slits (top,bottom) homing failed. See door debug for more information.')
                if top_info['homed']:
                    self.debug('Motor %s successfully homed.' % top_info['motor'].alias())
                else:
                    self.debug('Motor %s homing failed.' % top_info['motor'].alias())
                if bottom_info['homed']: 
                    self.debug('Motor %s successfully homed.' % bottom_info['motor'].alias())                
                else:
                    self.debug('Motor %s homing failed.' % bottom_info['motor'].alias())
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e
        finally:
	    #@TODO: uncoment when serialization bug fixed
            #self.debug('Unmasking software limits...')
            bottom_pos = PyTango.AttributeProxy(self.MOVM_BOTTOM + '/position')
            vgap_pos = PyTango.AttributeProxy(self.MOVM_VGAP + '/position')

            bottom_pos_conf = bottom_pos.get_config()
            vgap_pos_conf = vgap_pos.get_config()

            bottom_pos_conf.min_value = self.old_bottom_min
            vgap_pos_conf.min_value = self.old_vgap_min

            bottom_pos.set_config(bottom_pos_conf)
            vgap_pos.set_config(vgap_pos_conf)


class mma_homing_hori(Macro):
    """ 
    This macro does homing of horizontal slits of White Beam Movable Masks situated in beamline's Front End.
    Homing procedure is done in 4 steps:
  

    1. First negative software limits of left and hgap motors are masked. 
    2. Simultaneous move of right and left motors towards their hardware negative limits.
       (they start simultaneous motion)
    3. When all of them reaches extreams Icepap homing routine is started (GROUP - see icepap_homing macro description) for right and left motors
       simultaneously - in positive direction. (whenever any of the these motors is stopped by a STOP command, 
       or an alarm condition, all the other axes in the group are forced to stop immediately)
       Homing routine is successful if both motors find home signal.
    4. At the end, software limits of right and left motors are unmasked.

    In case of successfully homing of all motors macro returns True, in all other cases it return False
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    MOVM_RIGHT = 'mma_r'
    MOVM_LEFT  = 'mma_l'
    MOVM_HGAP  = 'mma_h_gap'

    MOVM_RIGHT_HOMING_DIR = 1
    MOVM_LEFT_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        self.right = self.getObj(self.MOVM_RIGHT, type_class=Type.Motor)
        self.left = self.getObj(self.MOVM_LEFT, type_class=Type.Motor)

        left_pos = PyTango.AttributeProxy(self.MOVM_LEFT + '/position')
        hgap_pos = PyTango.AttributeProxy(self.MOVM_HGAP + '/position')

        left_pos_conf = left_pos.get_config()
        hgap_pos_conf = hgap_pos.get_config()
        
        #here we mask software limits, to allow reaching hardware limits
        self.debug('Masking software limits...')
        self.old_left_min = left_pos_conf.min_value
        self.old_hgap_min = hgap_pos_conf.min_value
        
        left_pos_conf.min_value = '-9.999E+003'
        hgap_pos_conf.min_value = '-9.999E+003'
        
        left_pos.set_config(left_pos_conf)
        hgap_pos.set_config(hgap_pos_conf)
        
    def run(self, *args, **opts):        
        try:
            motors_pos_dict = {self.right:-999, self.left:-999}
            while len(motors_pos_dict):
                motorsOnNegLim = moveToNegHardLim(self, motors_pos_dict)
                for m in motorsOnNegLim:
                    motors_pos_dict.pop(m)
            right_info = create_motor_info_dict(self.right, self.MOVM_RIGHT_HOMING_DIR)
            left_info = create_motor_info_dict(self.left, self.MOVM_LEFT_HOMING_DIR)
            info_dicts = [right_info, left_info]
            res = home_group(self, info_dicts)
            if res == True:
                self.info('Horizontal movable mask slits (right,left) successfully homed.')
            elif res == False:
                self.error('Horizontal movable mask slits (right,left) homing failed. See door debug for more information.')
                if right_info['homed']:
                    self.debug('Motor %s successfully homed.' % right_info['motor'].alias())
                else:
                    self.debug('Motor %s homing failed.' % right_info['motor'].alias())
                if left_info['homed']: 
                    self.debug('Motor %s successfully homed.' % left_info['motor'].alias())                
                else:
                    self.debug('Motor %s homing failed.' % left_info['motor'].alias())
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e
        finally:
	    #@TODO: uncoment when serialization bug fixed
            #self.debug('Unmasking software limits...')
            left_pos = PyTango.AttributeProxy(self.MOVM_LEFT + '/position')
            hgap_pos = PyTango.AttributeProxy(self.MOVM_HGAP + '/position')

            left_pos_conf = left_pos.get_config()
            hgap_pos_conf = hgap_pos.get_config()

            left_pos_conf.min_value = self.old_left_min
            hgap_pos_conf.min_value = self.old_hgap_min

            left_pos.set_config(left_pos_conf)
            hgap_pos.set_config(hgap_pos_conf)