import time
import PyTango

from macro import Macro, Type
from macro_utils.icepap import *
from macro_utils.motors import moveToHardLim

class m_homing_vert(Macro):
    """ 
    This macro does the homing of vertical slits of the BL22-CLAESS Diagnostic Module.
    Homing procedure is done in 3 steps:
    0. Software limits are masked. 
    1. Top blade is moved to its positive harware limit and bottom blade is moved to its negative hardware limit (simultaneously).
    3. Icepap homing procedure is started looking for home in the following directions:
       - top blade moving negative
       - bottom blade moving positive
    4. When top blade finds its home, it is stopped and bottom continues in the same direction as before.
    In case of successfully homing of both blades macro returns True, on all other cases it return False
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    ZL_NAME = 'm_zl'
    ZR_NAME = 'm_zr'
    ZC_NAME = 'm_zc'
    
    ZL_HOMING_DIR = -1
    ZR_HOMING_DIR = -1
    ZC_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.zl = self.getObj(self.ZL_NAME, type_class=Type.Motor)
        self.zr = self.getObj(self.ZR_NAME, type_class=Type.Motor)
        self.zc = self.getObj(self.ZC_NAME, type_class=Type.Motor)

        motors_on_home = []
        if self.zl.Limit_switches[2]:
            motors_on_home.append(self.zl)
        if self.zr.Limit_switches[2]:
            motors_on_home.append(self.zr)
        if self.zc.Limit_switches[2]:
            motors_on_home.append(self.zc)
        if len(motors_on_home):
            raise Exception('Motors: %s are already at home position. Homing procedure can not be started.' % [mot.alias() for mot in motors_on_home])

    def run(self, *args, **opts):        
        try:
            zl_info_dict = create_motor_info_dict(self.zl, self.ZL_HOMING_DIR)
            zr_info_dict = create_motor_info_dict(self.zr, self.ZR_HOMING_DIR)
            zc_info_dict = create_motor_info_dict(self.zc, self.ZC_HOMING_DIR)

            info_dicts = [zl_info_dict, zr_info_dict, zc_info_dict]
            #first attempt: with all motors            
            res = home_group_strict(self, info_dicts)
            if res == True:
                homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                for mot_info_dict in homed_info_dicts:
                    self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                    info_dicts.remove(mot_info_dict)
                  
                if len(info_dicts) > 0 :
                    #second attempt: with motors which were not homed in previous step
                    home_group_strict(self, info_dicts)
                    if res == True:
                        homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                        for mot_info_dict in homed_info_dicts:
                            self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                            info_dicts.remove(mot_info_dict)

                        if len(info_dicts) > 0:
                            #third and last attempt: with last motor which was not homed in two previous steps
                            home_group_strict(self, info_dicts)
                            if res == True:
                                homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                                for mot_info_dict in homed_info_dicts:
                                    self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                                    info_dicts.remove(mot_info_dict)
                                if len(info_dicts) == 0:
                                    #third attempt succeed: rest of the motors homed 
                                    self.info("Mirror's successfully homed all vertical motors.")
                                    return True
                                else: 
                                    self.error('Unknown error. Please contact responsible control engineer.')
                                    return False
                            elif res == False:
                                self.error("Last of the mirror's vertical motors did not find home.") 
                                return False
                            else: 
                                self.error('Unknown error. Please contact responsible control engineer.')
                                return False
                        else:
                            #second attempt succeed: rest of the motors homed 
                            self.info("Mirror's successfully homed all vertical motors.")
                            return True
                    elif res == False:
                        self.error("Rest of the mirror's vertical motors did not find home.") 
                        return False
                    else: 
                        self.error('Unknown error. Please contact responsible control engineer.')
                        return False
                else:
                    #first attempt succeed: all motors homed at the same time
                    self.info("Mirror's successfully homed all vertical motors.")
                    return True
            elif res == False:
                self.error("None of the mirror's vertical motors found home.") 
                return False
            else: 
                self.error('Unknown error. Please contact responsible control engineer.')
                return False
        except Exception, e:
            self.error(repr(e))
            raise e

class m_homing_hori(Macro):
    """ 
    
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    X1_NAME = 'm_x1'
    X2_NAME = 'm_x2'
    
    X1_HOMING_DIR = -1
    X2_HOMING_DIR = -1

    def prepare(self, *args, **opts):
        self.x1 = self.getObj(self.X1_NAME, type_class=Type.Motor)
        self.x2 = self.getObj(self.X2_NAME, type_class=Type.Motor)

        motors_on_home = []
        if self.x1.Limit_switches[2]:
            motors_on_home.append(self.x1)
        if self.x2.Limit_switches[2]:
            motors_on_home.append(self.x2)
        if len(motors_on_home):
            raise Exception('Motors: %s are already at home position. Homing procedure can not be started.' % [mot.alias() for mot in motors_on_home])

    def run(self, *args, **opts):        
        try:
            x1_info_dict = create_motor_info_dict(self.x1, self.X1_HOMING_DIR)
            x2_info_dict = create_motor_info_dict(self.x2, self.X2_HOMING_DIR)

            info_dicts = [x1_info_dict, x2_info_dict]
            #first attempt: with all motors            
            res = home_group_strict(self, info_dicts)
            if res == True:
                homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                for mot_info_dict in homed_info_dicts:
                    self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                    info_dicts.remove(mot_info_dict)
                  
                if len(info_dicts) > 0:
                    #second attempt: with motor which was not homed in previous step
                    home(self, info_dicts)
                    if res == True:
                        homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                        for mot_info_dict in homed_info_dicts:
                            self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                            info_dicts.remove(mot_info_dict)

                            if len(info_dicts) == 0:
                                #second attempt succeed: last motor homed 
                                self.info("Mirror successfully homed all horizontal motors.")
                                return True
                            else: 
                                self.error('Unknown error. Please contact responsible control engineer.')
                                return False
                    elif res == False:
                        self.error("Second mirror's vertical motor did not find home.") 
                        return False
                    else: 
                        self.error('Unknown error. Please contact responsible control engineer.')
                        return False
                else:
                    #first attempt succeed: all motors homed at the same time
                    self.info("Mirror successfully homed all horizontal motors.")
                    return True
            elif res == False:
                self.error("None of the mirror's vertical motors found home.") 
                return False
            else: 
                self.error('Unknown error. Please contact responsible control engineer.')
                return False
        except Exception, e:
            self.error(repr(e))
            raise e