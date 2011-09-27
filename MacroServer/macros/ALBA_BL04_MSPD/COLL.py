import time
import PyTango

from macro import Macro, Type
from macro_utils.icepap import *
from macro_utils.motors import moveToHardLim

class coll_homing(Macro):
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

    MOT_NAME = 'coll_z'
    
    HOMING_DIR = 1    

    def prepare(self, *args, **opts):
        self.mot = self.getObj(self.MOT_NAME, type_class=Type.Motor)
        if self.mot.Limit_switches[1]:
            raise Exception('Motor %s is already at home position. Homing procedure can not be started.', self.mot.alias())

    def run(self, *args, **opts):        
        try:
            mot_info_dict = create_motor_info_dict(self.mot, self.HOMING_DIR)
            info_dicts = [mot_info_dict]
            res = home(self, info_dicts)
            if res == True:
                self.info('2nd collimator successfully homed.')
            elif res == False:
                self.error('2nd collimator homing failed.')
                return False
            else: 
                self.error('Unknown error. Please contact responsible control engineer.')
            return res
        except Exception, e:
            self.error(repr(e))
            raise e