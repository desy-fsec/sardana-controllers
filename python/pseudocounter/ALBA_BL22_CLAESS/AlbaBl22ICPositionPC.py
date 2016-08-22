from sardana.pool.controller import PseudoCounterController
import PyTango
nan = float('Nan')

class ICPositionPCController(PseudoCounterController):

    counter_roles = ('ch1', 'ch2')
    pseudo_counter_roles = ('pos',)

    def __init__(self, inst, props):
        PseudoCounterController.__init__(self, inst, props)

    def calc(self, index, counter_values):
        value = nan
        if index == 1:
            value = counter_values[0] + counter_values[1]
        return value