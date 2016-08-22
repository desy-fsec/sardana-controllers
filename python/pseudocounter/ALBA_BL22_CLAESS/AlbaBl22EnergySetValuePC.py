from sardana.pool.controller import PseudoCounterController
import PyTango

class EnergySetValuePCController(PseudoCounterController):

    counter_roles = ()
    pseudo_counter_roles = ('energy_set',)

    def __init__(self, inst, props):
        PseudoCounterController.__init__(self, inst, props)
        self.energy = PyTango.DeviceProxy('pm/dcm_energy_ctrl/1')

    def calc(self, index, counter_values):
        energy_set = self.energy.read_attribute("Position").w_value
        return energy_set
