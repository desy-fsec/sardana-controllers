from sardana import pool
from sardana.pool.controller import PseudoCounterController

class AlbaBl04XBPMPCController(PseudoCounterController):
    
    ctrl_extra_attributes = {"Offset":{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'}}
    
    counter_roles = ('ixbt', 'ixbb', 'ixbr', 'ixbl')
    pseudo_counter_roles = ('ixbz', 'ixbx', 'ixbtot')
   
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        self.extra_attributes = {1:{'offset':1.0},2:{'offset':1.0},3:{'offset':float('nan')}}

    def pseudo_current(self, first, second):
        return (first - second) / (first + second)

    def calc(self, index, counter_values):
        ixbt, ixbb, ixbr, ixbl = counter_values

        if index == 1: #vertical
            offset = self.extra_attributes[1]["offset"]
            ixbz = (ixbt * offset - ixbb)/(ixbt * offset + ixbb)
            return ixbz
        elif index == 2: #horizontal
            offset = self.extra_attributes[2]["offset"]
            ixbx = (ixbr * offset - ixbl)/(ixbr * offset + ixbl)
            return ixbx
        elif index == 3:
            ixbtot = (ixbt + ixbb + ixbr + ixbl) / 4
            return ixbtot
        
    def GetExtraAttributePar(self, axis, name):
        name = name.lower()
        if name == 'offset':
            return self.extra_attributes[axis]['offset']
       
    def SetExtraAttributePar(self, axis, name, value):
        name = name.lower()
        if name == 'offset':
            if axis in [1,2]:
                self.extra_attributes[axis]['offset'] = value
            else:
                raise Exception("Offset attribute is restricted only for 1 and 2 axes.")
