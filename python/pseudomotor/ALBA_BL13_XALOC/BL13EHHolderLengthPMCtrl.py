from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController

class BL13EHHolderLengthPMController(PseudoMotorController):
    """ This controller provides the holderlength pseudomotor as a function of omegax."""

    pseudo_motor_roles = ('holderlength',)
    motor_roles = ('omegax',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        return pseudos[index - 1] - 22

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return physicals[index - 1] + 22
