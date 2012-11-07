#from pool import PseudoCounterController
import taurus

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController

class BL09MachinePCController(PseudoCounterController):

    counter_roles = ()
    pseudo_counter_roles = ('machine_current', 'fex', 'fez', 'ife1', 'ife2', 'ife3', 'ife4', 'ife')

    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        self.machine_attrs = {}
        self.MACH_CURRENT = 1
        self.machine_attrs[self.MACH_CURRENT] = 'tango://alba03:10000/expchan/srbl09_machine_attributes/1/Value'
        self.FEX = 2
        self.machine_attrs[self.FEX] = 'tango://alba03:10000/expchan/srbl09_machine_attributes/2/Value'
        self.FEZ = 3
        self.machine_attrs[self.FEZ] = 'tango://alba03:10000/expchan/srbl09_machine_attributes/3/Value'
        self.IFE1 = 4
        self.machine_attrs[self.IFE1] = 'tango://alba03:10000/expchan/srbl09_machine_attributes/4/Value'
        self.IFE2 = 5
        self.machine_attrs[self.IFE2] = 'tango://alba03:10000/expchan/srbl09_machine_attributes/5/Value'
        self.IFE3 = 6
        self.machine_attrs[self.IFE3] = 'tango://alba03:10000/expchan/srbl09_machine_attributes/6/Value'
        self.IFE4 = 7
        self.machine_attrs[self.IFE4] = 'tango://alba03:10000/expchan/srbl09_machine_attributes/7/Value'
        # Not from machine but calculated
        self.IFE = 8

    def read_tango_attribute(self, machine_tango_attribute):
        attr = taurus.Attribute(machine_tango_attribute)
        return attr.read().value

    def calc(self, index, counter_values):
        
        if index in self.machine_attrs.keys():
            return self.read_tango_attribute(self.machine_attrs[index])
        elif index == self.IFE:
            i1 = self.read_tango_attribute(self.machine_attrs[self.IFE1])
            i2 = self.read_tango_attribute(self.machine_attrs[self.IFE2])
            i3 = self.read_tango_attribute(self.machine_attrs[self.IFE3])
            i4 = self.read_tango_attribute(self.machine_attrs[self.IFE4])
            return i1 + i2 + i3 + i4
