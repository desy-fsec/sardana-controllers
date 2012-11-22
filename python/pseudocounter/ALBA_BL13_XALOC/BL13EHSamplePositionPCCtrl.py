from sardana import pool
from sardana.pool.controller import PseudoCounterController

class BL13EHSamplePositionPCController(PseudoCounterController):

    counter_roles = ()
    pseudo_counter_roles = ('samplex', 'sampley', 'samplez')
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
    
    def Calc(self, index, counter_values):
        import random
        return 100*random.random()
