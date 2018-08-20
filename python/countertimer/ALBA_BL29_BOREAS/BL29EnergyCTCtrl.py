#!/usr/bin/env python
import copy
import datetime
import numpy

import PyTango
import taurus
from sardana import State, DataAccess
from sardana.pool import AcqSynch, AcqMode
from sardana.pool.controller import CounterTimerController, Memorize, NotMemorized
from sardana.pool.controller import Type, Access, Description, MaxDimSize
from sardana.tango.core.util import from_tango_state_to_state

from BL29Energy import Energy
import Ni660XPositionCTCtrl

SM_PSEUDO_DESC = (
    'The name of the DiscretePseudoMotor to read/select which SM to use'
)
GR_PSEUDO_DESC = (
    'The name of the DiscretePseudoMotor to read/select which grating to use'
)


class BL29EnergyCTCtrl(Ni660XPositionCTCtrl.Ni660XPositionCTCtrl):
    """Alba BL29 specific controller for encoder position capture with the
    capability to calculate pseudo values e.g. angle, energy.

    It inherits the functionality from Ni600X position capture controller
    and is limited to 4 axes: 1 - timer, 2 - position capture (physical),
    3 - grating angle in microradians (pseudo) and 4 - energy (pseudo).

    The energy calculation is done by the BL29Energy library and it requires
    positions of the sm_selected and gr_selected pseudomotors.

    IMPORTANT: in order to use a pseudo axis in the measurement group, the
    timer and the real axis must be also used.
    """

    MaxDevice = 4

    ctrl_properties = copy.deepcopy(
        Ni660XPositionCTCtrl.Ni660XPositionCTCtrl.ctrl_properties
    )
    ctrl_properties['sm_pseudo'] = {Type: str, Description: SM_PSEUDO_DESC}
    ctrl_properties['gr_pseudo'] = {Type: str, Description: GR_PSEUDO_DESC}

    def __init__(self, inst, props, *args, **kwargs):
        super(BL29EnergyCTCtrl, self).__init__(inst, props, *args, **kwargs)
        self.sm = PyTango.DeviceProxy(self.sm_pseudo)
        self.gr = PyTango.DeviceProxy(self.gr_pseudo)

    def AddDevice(self, axis):
        # do nothing for pseudo axes
        if axis > 2:
            return
        super(BL29EnergyCTCtrl, self).AddDevice(axis)

    def DeleteDevice(self, axis):
        # do nothing for pseudo axes
        if axis > 2:
            return
        super(BL29EnergyCTCtrl, self).DeleteDevice(axis)

    def GetAxisExtraPar(self, axis, name):
        # for pseudo axes return values of physical axis
        if axis > 2:
            axis = 2
        return super(BL29EnergyCTCtrl, self).GetAxisExtraPar(axis, name)

    def SetAxisExtraPar(self, axis, name, value):
        # for pseudo axes set values of physical axis
        if axis > 2:
            axis = 2
        super(BL29EnergyCTCtrl, self).SetAxisExtraPar(axis, name, value)

    def StateOne(self, axis):
        # for pseudo axes return state of physical axis
        if axis > 2:
            axis = 2
        return super(BL29EnergyCTCtrl, self).StateOne(axis)

    def PreStartAllCT(self):
        super(BL29EnergyCTCtrl, self).PreStartAllCT()
        self.sm_selected = int(self.sm.read_attribute('Position').value)
        self.gr_selected = int(self.gr.read_attribute('Position').value)
        # sm position definition was changed on user request, but we have to
        # work with the library's definition
        self.sm_selected = Energy.user2lib(self.sm_selected,
                                           self.sm.user_idx_offset)

    def PreStartOneCT(self, axis):
        # do nothing for pseudo axes
        if axis > 2:
            return True
        return super(BL29EnergyCTCtrl, self).PreStartOneCT(axis)

    def StartOneCT(self, axis):
        # do nothing for pseudo axes
        if axis > 2:
            return
        return super(BL29EnergyCTCtrl, self).StartOneCT(axis)

    def AbortOne(self, axis):
        # do nothing for pseudo axes
        if axis > 2:
            return
        return super(BL29EnergyCTCtrl, self).AbortOne(axis)

    def ReadAll(self):
        # read value of the physical axis and store it for calculation or direct
        # return when ReadOne method is called
        self.enc_counts = super(BL29EnergyCTCtrl, self).ReadOne(2)

    def ReadOne(self, axis):
        # just the default implementation
        if axis == 1:
            return super(BL29EnergyCTCtrl, self).ReadOne(axis)
        # encoder counts
        elif axis == 2:
            return self.enc_counts
        # grating angle (in microradians) computed from encoder counts
        elif axis == 3:
            # 1 transform encoder counts to pitch angle (in microradians)
            pitch = numpy.array(self.enc_counts)
            pitch /= Energy.step_per_unit
            # 2 apply offset to get correct readings from 0 position
            pitch += Energy.offset0
            # 3 apply the user supplied mirrors combination offset
            # depending on the GR and SM selected
            pitch += Energy.mirrors_offsets[self.gr_selected][self.sm_selected]
            return pitch.tolist()  # note that values are in microradians
        # calculate energy using BL29Energy library
        elif axis == 4:
            values = []
            for encoder_value in self.enc_counts:
                energy_value = Energy.get_energy(
                    self.sm_selected, self.gr_selected, encoder_value,
                    gr_source_is_encoder=True
                )
                values.append(energy_value)
            return values
