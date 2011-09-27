import time
import PyTango

from macro import Macro, Type
from macro_utils.icepap import *
            
class dcm_homing_vert(Macro):
    """ 
    This macro does homing of vertical motor of DCM (BL04).
    It will start looking for homing position into negative direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    DCM_VERT = 'dcm_vert'
    
    DCM_VERT_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.vert = self.getObj(self.DCM_VERT, type_class=Type.Motor)
        if self.vert.Limit_switches[2]:
            raise Exception('Motor dcm_vert is already at home position. Homing procedure can not be started.')
        
    def run(self, *args, **opts):
        vert_info = create_motor_info_dict(self.vert, self.DCM_VERT_HOMING_DIR)
        info_dicts = [vert_info]
        try:
            res = home(self, info_dicts)
            if res == True:
                self.info('Dcm vertical motor successfully homed.')
            elif res == False:
                self.error('Dcm vertical motor homing failed.')
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e


class dcm_homing_bragg(Macro):
    """ 
    This macro does homing of bragg motor of DCM (BL04).
    It will start looking for homing position into negative direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    DCM_BRAGG = 'dcm_bragg'
    
    DCM_BRAGG_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.bragg = self.getObj(self.DCM_BRAGG, type_class=Type.Motor)
        if self.bragg.Limit_switches[2]:
            raise Exception('Motor dcm_bragg is already at home position. Homing procedure can not be started.')
        
    def run(self, *args, **opts):
        bragg_info = create_motor_info_dict(self.bragg, self.DCM_BRAGG_HOMING_DIR)
        info_dicts = [bragg_info]
        try:
            res = home(self, info_dicts)
            if res == True:
                self.info('Dcm bragg motor successfully homed.')
            elif res == False:
                self.error('Dcm bragg motor homing failed.')
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e

class dcm_homing_t2(Macro):
    """ 
    This macro does homing of t2 motor of DCM (BL04).
    It will start looking for homing position into positive direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    DCM_T2 = 'dcm_t2'
    
    DCM_T2_HOMING_DIR = 1

    def prepare(self, *args, **opts):
        self.t2 = self.getObj(self.DCM_T2, type_class=Type.Motor)
        if self.t2.Limit_switches[1]:
            raise Exception('Motor dcm_t2 is already at home position. Homing procedure can not be started.')
        
    def run(self, *args, **opts):
        t2_info = create_motor_info_dict(self.t2, self.DCM_T2_HOMING_DIR)
        info_dicts = [t2_info]
        try:
            res = home(self, info_dicts)
            if res == True:
                self.info('Dcm t2 motor successfully homed.')
            elif res == False:
                self.error('Dcm t2 motor homing failed.')
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e


class dcm_homing_roll1(Macro):
    """ 
    This macro does homing of roll1 motor of DCM (BL04).
    It will start looking for homing position into negative direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    DCM_ROLL1 = 'dcm_roll1'
    
    DCM_ROLL1_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.roll1 = self.getObj(self.DCM_ROLL1, type_class=Type.Motor)
        if self.roll1.Limit_switches[2]:
            raise Exception('Motor dcm_roll1 is already at home position. Homing procedure can not be started.')
        
    def run(self, *args, **opts):
        roll1_info = create_motor_info_dict(self.roll1, self.DCM_ROLL1_HOMING_DIR)
        info_dicts = [roll1_info]
        try:
            res = home(self, info_dicts)
            if res == True:
                self.info('Dcm roll1 motor successfully homed.')
            elif res == False:
                self.error('Dcm roll1 motor homing failed.')
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e

class dcm_homing_roll2(Macro):
    """ 
    This macro does homing of roll2 motor of DCM (BL04).
    It will start looking for homing position into negative direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    DCM_ROLL2 = 'dcm_roll2'
    
    DCM_ROLL2_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.roll2 = self.getObj(self.DCM_ROLL2, type_class=Type.Motor)
        if self.roll2.Limit_switches[2]:
            raise Exception('Motor dcm_roll2 is already at home position. Homing procedure can not be started.')
        
    def run(self, *args, **opts):
        roll2_info = create_motor_info_dict(self.roll2, self.DCM_ROLL2_HOMING_DIR)
        info_dicts = [roll2_info]
        try:
            res = home(self, info_dicts)
            if res == True:
                self.info('Dcm roll2 motor successfully homed.')
            elif res == False:
                self.error('Dcm roll2 motor homing failed.')
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e


class dcm_homing_pitch2(Macro):
    """ 
    This macro does homing of pitch2 motor of DCM (BL04).
    It will start looking for homing position into negative direction.
    In case of successfully homing macro returns True, in all other cases it return False.
    """

    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    DCM_PITCH2 = 'dcm_pitch2'
    
    DCM_PITCH2_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.pitch2 = self.getObj(self.DCM_PITCH2, type_class=Type.Motor)
        if self.pitch2.Limit_switches[2]:
            raise Exception('Motor dcm_pitch2 is already at home position. Homing procedure can not be started.')
        
    def run(self, *args, **opts):
        pitch2_info = create_motor_info_dict(self.pitch2, self.DCM_PITCH2_HOMING_DIR)
        info_dicts = [pitch2_info]
        try:
            res = home(self, info_dicts)
            if res == True:
                self.info('Dcm pitch2 motor successfully homed.')
            elif res == False:
                self.error('Dcm pitch2 motor homing failed.')
            else:
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e