""" The standard pseudo counter controller library for the device pool """

# from sardana import pool
# from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController

# from math import *

# try:
#     import scipy
#     __SCIPY_AVAILABLE__ = True
# except Exception:
#     __SCIPY_AVAILABLE__ = False


# Will disapear when we have pseudo counters
# that can have other pseudo counters
# in their counter roles.
class MCA2SCACtrl(PseudoCounterController):
    """ A counter controller which receives an MCA Spectrum
        and return a single value"""

    # NO COUNTERS NEEDED
    counter_roles = 'mca',

    pseudo_counter_roles = 'sca',

    # THE EXTRA ATTRIBUTES: RoIs definition

    axis_attributes = {
        'RoI1': {
            'Type': 'PyTango.DevLong',
            'Description': 'The low limit of the Region of Interest ',
            'R/W Type': 'PyTango.READ_WRITE'
        },
        'RoI2': {
            'Type': 'PyTango.DevLong',
            'Description': 'The upper limit of the Region of Interest',
            'R/W Type': 'PyTango.READ_WRITE'
        }
    }

    def __init__(self, inst, props, *args, **kwargs):

        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)

        self.counterExtraAttributes = {}
        self.counterExtraAttributes[1] = {"RoI1": 0,
                                          "RoI2": 0}

    def GetAxisExtraPar(self, index, name):
        return self.counterExtraAttributes[1][name]

    def SetAxisExtraPar(self, counter, name, value):
        self.counterExtraAttributes[1][name] = value

    def Calc(self, index, counter_values):
        sum = 0
        for i in range(self.counterExtraAttributes[1]['RoI1'],
                       self.counterExtraAttributes[1]['RoI2']):
            sum = sum + counter_values[0][i]
        return float(sum)
