#from pool import PseudoCounterController
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController

class BL13EHXBPMCrossedPCController(PseudoCounterController):

    counter_roles = ('ib_ru', 'ib_rd', 'ib_lu', 'ib_ld')
    pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_')
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)

    def Calc(self, index, counter_values):
        ib_ru, ib_rd, ib_lu, ib_ld = counter_values

        if 'ib_x' == self.pseudo_counter_roles[index-1]:
            ib_x = self.pseudo_current(ib_ru, ib_rd, ib_lu, ib_rd)
            return ib_x
        elif 'ib_z' == self.pseudo_counter_roles[index-1]:
            ib_z = self.pseudo_current(ib_ru, ib_lu, ib_rd, ib_ld)
            return ib_z
        elif 'ib_' == self.pseudo_counter_roles[index-1]:
            return ib_ru + ib_rd + ib_lu + ib_ld

    def pseudo_current(self, first, second, third, forth):
        # ib5x = ((ib5ru+ib5rd) - (ib5lu+ib5ld)) / ((ib5ru+ib5rd) + (ib5lu+ib5ld))
        # ib6x = ((ib6ru+ib6rd) - (ib6lu+ib6ld)) / ((ib6ru+ib6rd) + (ib6lu+ib6ld))
        # x = ((ru+rd) - (lu+ld)) / ((ru+rd) + (lu+ld))
        # ru=first, rd=second, lu=third, ld=forth
        # x = ((first+second) - (third+forth)) / ((first+second) + (third+forth))
        
        # ib5z = ((ib5ru+ib5lu) - (ib5rd+ib5ld)) / ((ib5ru+ib5lu) + (ib5rd+ib5ld))
        # ib6z = ((ib6ru+ib6lu) - (ib6rd+ib6ld)) / ((ib6ru+ib6lu) + (ib6rd+ib6ld))
        # z = ((ru+lu) - (rd+ld)) / ((ru+lu) + (rd+ld))
        # ru=first, lu=second, rd=third, ld=forth
        # z = ((first+second) - (third+forth)) / ((first+second) + (third+forth))

        return ((first+second) - (third+forth)) / ((first+second) + (third+forth))
