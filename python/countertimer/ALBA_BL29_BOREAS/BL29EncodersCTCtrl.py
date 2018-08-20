#!/usr/bin/env python

import Ni660XPositionCTCtrl

from sardana import DataAccess
from sardana.pool.controller import Type, Access, Memorize, Memorized


class BL29EncodersCTCtrl(Ni660XPositionCTCtrl.Ni660XPositionCTCtrl):
    """Alba BL29 specific controller for hardware encoder position capture of
    physical motors and optional pseudo computations based on them
    The controller admits 2 kind of axes:
    - hardware. These are the raw values read from the Ni660X card, to which
      the encoders cable should be connected. Note that the maximum allowed
      channels are the same as items in 'ChannelDevNames' controller property
    - pseudo. After defining all the hardware axes then you can optinally
      define pseudo axes that take their corresponding hardware axis value and
      then applies a user defined formula to that value.

    It inherits the main functionality from Ni660XPositionCTCtrl

    IMPORTANT: in order to use one of the pseudo axis in the measurement group
    the timer and the corresponding hardware axis must also be included
    """

    axis_attributes = dict(
        Ni660XPositionCTCtrl.Ni660XPositionCTCtrl.axis_attributes)
    axis_attributes.update({
        'formula': {
            Type: str,
            Access: DataAccess.ReadWrite,
            Memorize: Memorized,
        },
    })

    def __init__(self, inst, props, *args, **kwargs):
        self.parent = super(BL29EncodersCTCtrl, self)
        self.parent.__init__(inst, props, *args, **kwargs)
        # list for temp storage lists of hardware channels values (excl timer)
        self.hw_axes = [[] for i in range(
            len(self.channelDevNames.split(','))-1)]
        BL29EncodersCTCtrl.MaxDevice = len(self.hw_axes)*2+1  # hw+pseudo+timer
        self.formulas = []  # pseudo axes formulas in str for user inspection
        self.functions = []  # pseudo axes formulas converted to code with eval

    def AddDevice(self, axis):
        # pseudo axis: initialize with empty formula
        if axis > len(self.hw_axes)+1:
            self.formulas.append('')
            self.functions.append(None)
        else:
            return self.parent.AddDevice(axis)

    def DeleteDevice(self, axis):
        # do nothing for pseudo axes
        if axis > len(self.hw_axes)+1:
            return
        else:
            return self.parent.DeleteDevice(axis)

    def AbortOne(self, axis):
        # do nothing for pseudo axes
        if axis > len(self.hw_axes)+1:
            return
        else:
            return self.parent.AbortOne(axis)

    def StateOne(self, axis):
        # for pseudo axes return state of physical axis
        if axis > len(self.hw_axes)+1:
            axis -= len(self.hw_axes)
        return self.parent.StateOne(axis)

    def PreStartOneCT(self, axis):
        # do nothing for pseudo axes
        if axis > len(self.hw_axes)+1:
            return True
        return self.parent.PreStartOneCT(axis)

    def StartOneCT(self, axis):
        # do nothing for pseudo axes
        if axis > len(self.hw_axes)+1:
            return
        else:
            return self.parent.StartOneCT(axis)

    def ReadAll(self):
        # read value of all the physical axes and store them for calculation
        # or direct return when ReadOne method is called
        for idx in range(len(self.hw_axes)):
            self.hw_axes[idx][:] = self.parent.ReadOne(idx+2)

    def ReadOne(self, axis):
        # just the default implementation for timer
        if axis == 1:
            return self.parent.ReadOne(axis)
        # hardware axis: return encoder counts
        elif axis-2 < len(self.hw_axes):
            return self.hw_axes[axis-2]
        # pseudo axis: apply formula and return values
        else:
            values = []
            idx0 = axis-len(self.hw_axes)-2  # -2 = -timer -idx_1
            function = self.functions[idx0]
            if function is not None:
                for hw_value in self.hw_axes[idx0]:
                    values.append(function(hw_value))
            else:
                values = self.hw_axes[idx0]
            return values

    def GetAxisExtraPar(self, axis, name):
        idx0 = axis-len(self.hw_axes)-2  # -2 = -timer -idx_starts_at_1
        if name.lower() == 'formula':
            if idx0 in range(len(self.formulas)):
                return self.formulas[idx0]
            else:
                return ''
        else:
            return self.parent.GetAxisExtraPar(axis, name)

    def SetAxisExtraPar(self, axis, name, value):
        idx0 = axis-len(self.hw_axes)-2  # -2 = -timer -idx_starts_at_1
        if name.lower() == 'formula':
            function = eval('lambda value: %s' % value)
            try:
                function(0)
            except Exception as e:
                msg = 'Check formula! It fails with 0: %s' % str(e)
                raise Exception(msg)
            if idx0 in range(len(self.formulas)):
                self.formulas[idx0] = value
                self.functions[idx0] = function
            elif idx0 >= len(self.formulas):
                self.formulas.append(value)
                self.functions.append(function)
            else:
                pass  # asking to set formula in a hw axis or timer
        else:
            return self.parent.SetAxisExtraPar(axis, name, value)
