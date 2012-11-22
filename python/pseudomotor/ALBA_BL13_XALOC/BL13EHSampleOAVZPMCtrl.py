from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController
import taurus
import math

class BL13EHSampleOAVZController(PseudoMotorController):
    """ This controller provides the sample OAV Z pseudomotor as a function of centx,centy."""

    pseudo_motor_roles = ('sampleoavz',)
    motor_roles = ('centx','centy','omega')

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        sampleoavz, = pseudos
        centx_init = curr_physicals[0]
        centy_init = curr_physicals[1]
        omega_init = curr_physicals[2]
        sampleoavz_init = self.CalcPseudo(1, curr_physicals, [])

        omega_rad = (math.pi/180.)*omega_init
	centx = centx_init + (sampleoavz-sampleoavz_init)*math.sin(-1.*omega_rad)
	centy = centy_init + (sampleoavz-sampleoavz_init)*math.cos(-1.*omega_rad)

        motor_role = self.motor_roles[index - 1]
        if 'centx' == motor_role:
            return centx 
        elif 'centy' == motor_role:
            return centy 
        elif 'omega' == motor_role:
            return omega_init

    def CalcPseudo(self, index, physicals, curr_pseudos):
        centx, centy, omega = physicals
        omega_rad = (math.pi/180.)*omega
        return centx*math.sin(-1.*omega_rad)+centy*math.cos(-1.*omega_rad)
