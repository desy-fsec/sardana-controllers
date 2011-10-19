import time
import PyTango

from macro import Macro, Type
from macro_utils.icepap import *
from macro_utils.motors import moveToHardLim, moveToReadPos

class m_homing_vert(Macro):
    """ 
    This macro does homing of vertical jacks of the BL04-MSPD Collimating mirror.

    Homing procedure tries to home all three jacks at the same time towards their negative hardware limits. 
    When any of them reaches its home position, homing is repeated for rest of them towards the same direction,
    untill all of them find home. If furing the motion, any of motors is stoped or gets into alarm state, 
    all the rest are sopped at the same time
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    ZL_NAME = 'm_zl'
    ZR_NAME = 'm_zr'
    ZC_NAME = 'm_zc'
    MZ_NAME = 'm_z'
    MPITCH_NAME = 'm_pitch'
    MROLL_NAME = 'm_roll'
    
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
            if res != True:
                self.error("None of the mirror's vertical motors found home.") 
                self.debug("home_group_strict returned: %s", repr(res))
                return False
            homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
            for mot_info_dict in homed_info_dicts:
                self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                info_dicts.remove(mot_info_dict)      
            
            if len(info_dicts) > 0 :
                #second attempt: with motors which were not homed in previous step
                home_group_strict(self, info_dicts)
                if res != True:
                    self.error("Rest of the mirror's vertical motors did not find home.") 
                    self.debug("home_group_strict returned: %s", repr(res))
                    return False
                homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                for mot_info_dict in homed_info_dicts:
                    self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                    info_dicts.remove(mot_info_dict)

                if len(info_dicts) > 0:
                    #third and last attempt: with last motor which was not homed in two previous steps
                    home_group_strict(self, info_dicts)
                    if res != True:
                        self.error("Last of the mirror's vertical motors did not find home.") 
                        self.debug("home_group_strict returned: %s", repr(res))
                        return False
                    homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                    for mot_info_dict in homed_info_dicts:
                        self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                        info_dicts.remove(mot_info_dict)
                    if len(info_dicts) != 0:
                        self.error('Unknown error. Please contact responsible control engineer.')
                        return False
                    
            
            #Because we were moving motors outside of the Sardana, 
            #before any motion of pseudomotors, we have to update its positions set values
            #we do it by reading current position of pseuodmotors and moving to that positions
            self.m_z = self.getObj(self.MZ_NAME, type_class=Type.Motor)
            self.m_pitch = self.getObj(self.MPITCH_NAME, type_class=Type.Motor)
            self.m_roll = self.getObj(self.MROLL_NAME, type_class=Type.Motor)
            moveToReadPos(self, [self.m_z,self.m_pitch,self.m_roll])

            self.info("Mirror's successfully homed all vertical motors.")
            return True
                
        except Exception, e:
            self.error(repr(e))
            raise e

class m_homing_hori(Macro):
    """ 
    This macro does homing of horizontal translations of the BL04-MSPD Collimating mirror.

    Homing procedure tries to home both translations at the same time towards their negative hardware limits. 
    When any of them reaches its home position, homing is repeated for the second one,
    untill it also finds home. If during the motion, any of motors is stoped or gets into alarm state, 
    all the rest are sopped at the same time.
    """
    
    result_def = [
        ['homed',  Type.Boolean, None, 'Motor homed state']
    ]

    X1_NAME = 'm_x1'
    X2_NAME = 'm_x2'
    MX_NAME = 'm_x'
    MYAW_NAME = 'm_yaw'
    
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
            if res != True:
                self.error("None of the mirror's horizontal motors found home.") 
                self.debug("home_group_strict returned: %s", repr(res))
                return False
            homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
            for mot_info_dict in homed_info_dicts:
                self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                info_dicts.remove(mot_info_dict)
      
            if len(info_dicts) > 0:
                #second attempt: with motor which was not homed in previous step
                home(self, info_dicts)
                if res != True:
                    self.error("Second mirror's vertical motor did not find home.") 
                    self.debug("home_group_strict returned: %s", repr(res))
                    return False
                homed_info_dicts = [mot_info_dict for mot_info_dict in info_dicts if mot_info_dict["homed"]]
                for mot_info_dict in homed_info_dicts:
                    self.info("Motor: %s successfully homed.", mot_info_dict["motor"].alias())
                    info_dicts.remove(mot_info_dict)
                if len(info_dicts) != 0:
                        self.error('Unknown error. Please contact responsible control engineer.')
                        return False

            #Because we were moving motors outside of the Sardana, 
            #before any motion of pseudomotors, we have to update its positions set values
            #we do it by reading current position of pseuodmotors and moving to that positions
            self.m_x = self.getObj(self.MX_NAME, type_class=Type.Motor)
            self.m_yaw = self.getObj(self.MYAW_NAME, type_class=Type.Motor)
            moveToReadPos(self, [self.m_x,self.m_yaw])
                      
            self.info("Mirror successfully homed all horizontal motors.")
            return True
        except Exception, e:
            self.error(repr(e))
            raise e

