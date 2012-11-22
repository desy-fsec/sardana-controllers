#from pool import PseudoCounterController
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController

class BL13OHSlitsPCController(PseudoCounterController):

    counter_roles = ('is1u', 'is1d', 'is1r', 'is1l', 'is2u', 'is2d', 'is3r', 'is3l')
    pseudo_counter_roles = ('is1z', 'is1x', 'is2z', 'is3x', 'is12z', 'is13x')
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
    
    def Calc(self, index, counter_values):
        is1u, is1d, is1r, is1l, is2u, is2d, is3r, is3l = counter_values
        if index == 1:
            return (is1u - is1d) / (is1u + is1d)
        elif index == 2:
            return (is1r - is1l) / (is1r + is1l)
        elif index == 3:
            return (is2u - is2d) / (is2u + is2d)
        elif index == 4:
            return (is3r - is3l) / (is3r + is3l)
        elif index == 5:
            return ((is2u - is2d) / (is2u + is2d)) - ((is1u - is1d) / (is1u + is1d))
        elif index == 6:
            return ((is3r - is3l) / (is3r + is3l)) - ((is1r - is1l) / (is1r + is1l))
