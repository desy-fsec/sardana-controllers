#!/usr/bin/env python

import math

from BL29Energy import Energy

from sardana import DataAccess
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue


class BL29EnergyMono(PseudoMotorController):
    """
    Energy pseudo motor controller for handling BL29-Boreas theoric energy of
    the monochromator given the positions of all the motors involved (and viceversa).
    This pseudo motor does not have access to the insertion device, so it gives
    or sets only the theoric energy
    """

    gender = 'Energy'
    model  = 'BL29-Boreas monochromator energy calculation'
    organization = 'CELLS - ALBA'
    image = 'energy.png'
    logo = 'ALBA_logo.png'

    pseudo_motor_roles = ('energy_mono',)
    motor_roles = ('gr_pitch',)

    #controller properties
    ctrl_properties = {
        'sm_pseudo' : {
            Type : str,
            Description : 'The name of the DiscretePseudoMotor to read/select which SM to use'
        },
        'gr_pseudo' : {
            Type : str,
            Description : 'The name of the DiscretePseudoMotor to read/select which grating to use'
        }
    }

    #axis attributes
    axis_attributes = {
        'lock_mirrors' : {
            Type : bool,
            Description : 'Whether or not allow me to change spherical mirror and/or gratings when asked to go to a given energy',
            Access : DataAccess.ReadWrite},
        'heg_sm2_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when HEG grating and SM2 are selected',
            Access : DataAccess.ReadWrite},
        'heg_sm1_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when HEG grating and SM1 are selected',
            Access : DataAccess.ReadWrite},
        'meg_sm2_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when MEG grating and SM2 are selected',
            Access : DataAccess.ReadWrite},
        'meg_sm1_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when MEG grating and SM1 are selected',
            Access : DataAccess.ReadWrite},
        'leg_sm2_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when LEG grating and SM2 are selected',
            Access : DataAccess.ReadWrite},
        'leg_sm1_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when LEG grating and SM1 are selected',
            Access : DataAccess.ReadWrite},
        'ranges' : {
            Type : str,
            Description : 'Energy ranges for each combination of SM and GR',
            Access : DataAccess.ReadOnly}
    }

    def __init__(self, inst, props, *args, **kwargs):
        """
        Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        @param *args extra arguments
        @param **kwargs keyword arguments
        """
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.sm_selected = PoolUtil.get_device(inst, self.sm_pseudo)
        self.gr_selected = PoolUtil.get_device(inst, self.gr_pseudo)
        self.lock_mirrors = True

    def CalcPhysical(self, axis, pseudo_pos, current_physical):
        """
        Given the motor number (gr-pitch) and the desired energy it
        returns the correct motor position for that motor and energy.
        @param[in] axis - motor number
        @param[in] pseudo_pos (sequence<float>) - a sequence containing pseudo motor positions (only target energy in our case)
        @param[in] current_physical (sequence<float>) - a sequence containing the current physical motor positions
        @return the correct motor position
        @throws exception
        """
        target_energy = pseudo_pos[0]
        try:
            sm_current = self.sm_selected.position
            gr_current = self.gr_selected.position
        except:
            msg = 'Unable to determine SM and/or GR selected'
            self._log.error(msg)
            raise Exception(msg)

        #check that target energy is possible with current mirrors combination
        range_found = False
        if (sm_current in Energy.SM_VALID) and (gr_current in Energy.GR_VALID):
            current_min_energy = Energy.energy_ranges[gr_current][sm_current][0]
            current_max_energy = Energy.energy_ranges[gr_current][sm_current][1]
            if (target_energy >= current_min_energy) and (target_energy <= current_max_energy):
                range_found = True
                sm_target = sm_current
                gr_target = gr_current

        #If target energy not possible with current combination, find which
        #grating and spherical mirrors can give me that energy. If not possible,
        #then raise exception
        if not range_found:
            for i in range(len(Energy.line_spacing)):
                for j in range(len(Energy.include_angles)):
                    if (target_energy >= Energy.energy_ranges[i][j][0] and target_energy <= Energy.energy_ranges[i][j][1]):
                        sm_target = j
                        gr_target = i
                        range_found = True
                        break
                if range_found:
                    break
            else:
                msg = 'Energy %s out of range in CalcPhysical()' % str(target_energy)
                self._log.error(msg)
                raise Exception(msg)

        #if we need to change mirrors then do it if possible
        if sm_current != sm_target or gr_current != gr_target:
            #if I'm allowed to change mirrors, then simply move them (but only if if estrictly necessary) 
            if not self.lock_mirrors:
                try:
                    if sm_current != sm_target:
                        self._log.debug('Moving SM to %d' % sm_target)
                        self.sm_selected.position = sm_target
                    if gr_current != gr_target:
                        self._log.debug('Moving GR to %d' % gr_target)
                        self.gr_selected.position = gr_target
                except:
                    msg = 'Got exception while trying to move SM or GR pseudo motors'
                    self._log.error(msg)
                    raise Exception(msg)
            elif not (sm_current in Energy.SM_VALID):
                msg = 'Spherical mirrors are incorrectly set. Unlock mirrors if you want to automatically set them'
                self._log.error(msg)
                raise Exception(msg)
            elif not (gr_current in Energy.GR_VALID): 
                msg = 'Grating mirror is incorrectly set. Unlock mirrors if you want to automatically set it'
                self._log.error(msg)
                raise Exception(msg)
            else:
                msg = \
                    'Energy %s not possible without changing current mirrors combination. Valid range with '\
                    'current combination is %s..%s. Unlock mirrors if you want to automatically change them' %\
                    (str(target_energy), str(Energy.energy_ranges[gr_current][sm_current][0]), str(Energy.energy_ranges[gr_current][sm_current][1]))
                self._log.error(msg)
                raise Exception(msg)

        if axis == 1:
            #get spherical mirror offset
            offset = Energy.offset[sm_target]

            #compute gr_pitch
            wave_length = Energy.constant / target_energy
            theta = Energy.include_angles[sm_target]
            D0 = Energy.line_spacing[gr_target]

            #Assuming m will always be 1.0 and doing basic simplification, the computation:
            #beta = -acos((m*lambbda*1.e-9*D0*1.e3/2) * tan(theta/2) + 
            #              sqrt(cos(theta/2)**2 - (m*lambbda*1.e-9*D0*1.e3/2)**2)
            #            )
            #Can be expressed as:
            beta = -1.0 * math.acos(
                             (wave_length*D0*5e-7) * math.tan(theta/2) + math.sqrt(math.cos(theta/2)**2 - (wave_length*D0*5e-7)**2 )
                            )

            alpha = theta + beta

            gr_pitch = (math.pi/2 - alpha - offset) #radians

            self._log.debug('<------------------------------------------------------- CalcPhysical')
            self._log.debug('target_energy: %f', target_energy)
            self._log.debug('offset: %f', offset)
            self._log.debug('lambda: %f', wave_length)
            self._log.debug('theta: %f', theta * 180 / math.pi)
            self._log.debug('beta: %f', beta * 180 / math.pi)
            self._log.debug('alpha: %f', alpha * 180 / math.pi)
            self._log.debug('(sm_target: %f, gr_target: %f, gr-pitch (rad): %f, gr-pitch (deg): %f, gr_pitch (microrad): %f', sm_target, gr_target, gr_pitch, gr_pitch * 180 / math.pi, gr_pitch * 1.0e6)
            self._log.debug('gr-pitch (rad): %f, gr-pitch (deg): %f', gr_pitch, gr_pitch * 180 / math.pi)
            self._log.debug('gr-pitch (urad): %f, gr-pitch (urad - OFFSET): %f', gr_pitch * 1e6, gr_pitch * 1e6 - Energy.mirrors_offsets[gr_target][sm_target])
            self._log.debug('-------------------------------------------------------> CalcPhysical')

            gr_pitch = gr_pitch * 1.0e6 #rads -> microrads
            #apply the corresponding mirrors combination offset
            return gr_pitch - Energy.mirrors_offsets[gr_target][sm_target]
        else:
            raise Exception('Invalid axis %s to compute energy %s CalcPhysical()' % (str(axis), str(target_energy)))

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the energy pseudomotor.
        @param[in] axis: (expected always 1, since we provide only 1 pseudo motor)
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of the energy pseudo motor itself
        @return the energy pseudo motor value
        @throws exception
        """
        try:
            #get currently selected grating and spherical mirror
            sm_selected = self.sm_selected.position
            gr_selected = self.gr_selected.position
            gr_pitch = physical_pos[0]
        except:
            msg = 'Unable to determine SM and/or GR selected and/or GR pitch'
            self._log.error(msg)
            raise Exception(msg)

        if not (sm_selected in Energy.SM_VALID) or not (gr_selected in Energy.GR_VALID) or (gr_pitch is None):
            msg = 'Spherical mirrors and/or grating mirror and/or grating pitch are not correctly set in CalcPseudo()'
            self._log.error(msg)
            raise Exception(msg)

        return Energy.get_energy(sm_selected,gr_selected,gr_pitch)

    def GetAxisExtraPar(self, axis, name):
        """
        Get extra controller parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to get (always one)
        @param name of the parameter to retrieve
        @return the value of the parameter
        """
        if name == 'lock_mirrors':
            return self.lock_mirrors
        elif name == 'heg_sm2_offset':
            return Energy.mirrors_offsets[Energy.HEG][Energy.SM2]
        elif name == 'heg_sm1_offset':
            return Energy.mirrors_offsets[Energy.HEG][Energy.SM1]
        elif name == 'meg_sm2_offset':
            return Energy.mirrors_offsets[Energy.MEG][Energy.SM2]
        elif name == 'meg_sm1_offset':
            return Energy.mirrors_offsets[Energy.MEG][Energy.SM1]
        elif name == 'leg_sm2_offset':
            return Energy.mirrors_offsets[Energy.LEG][Energy.SM2]
        elif name == 'leg_sm1_offset':
            return Energy.mirrors_offsets[Energy.LEG][Energy.SM1]
        elif name == 'ranges':
            return Energy.ranges

    def SetAxisExtraPar(self, axis, name, value):
        """
        Set extra axis parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to set (always one)
        @param name of the parameter to set
        @param value to be set
        """
        if name == 'lock_mirrors':
            self.lock_mirrors = value
        elif name == 'heg_sm2_offset':
            Energy.mirrors_offsets[Energy.HEG][Energy.SM2] = value
        elif name == 'heg_sm1_offset':
            Energy.mirrors_offsets[Energy.HEG][Energy.SM1] = value
        elif name == 'meg_sm2_offset':
            Energy.mirrors_offsets[Energy.MEG][Energy.SM2] = value
        elif name == 'meg_sm1_offset':
            Energy.mirrors_offsets[Energy.MEG][Energy.SM1] = value
        elif name == 'leg_sm2_offset':
            Energy.mirrors_offsets[Energy.LEG][Energy.SM2] = value
        elif name == 'leg_sm1_offset':
            Energy.mirrors_offsets[Energy.LEG][Energy.SM1] = value


class BL29Energy(PseudoMotorController):
    """
    Energy pseudo motor controller for handling BL29-Boreas energy coming out of
    the monochromator, given the energies reported both by the insertion device
    and the monochromator.
    This pseudo motor will give the real energy being delivered by the beamline,
    since it reads both the insertion device and the monochromator theoric energies
    When setting an energy, it will write that energy to both the insertion
    device and the monochromator
    """

    gender = 'Energy'
    model  = 'BL29-Boreas energy calculation'
    organization = 'CELLS - ALBA'
    image = 'energy.png'
    logo = 'ALBA_logo.png'

    pseudo_motor_roles = ('energy',)
    motor_roles = ('energy_id', 'energy_mono')

    #controller properties
    ctrl_properties = {
        'tolerance' : {
            Type : float,
            Description : 'The name of the DiscretePseudoMotor to read/select which SM to use',
            Access : DataAccess.ReadWrite,
            DefaultValue : 1.0
        }
    }

    def __init__(self, inst, props, *args, **kwargs):
        """
        Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        @param *args extra arguments
        @param **kwargs keyword arguments
        """
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, axis, pseudo_pos, current_physical):
        """
        Given the motor number (energy_id or energy_mono) and the desired energy
        it returns the correct motor position for that motor and energy.
        @param[in] axis - motor number
        @param[in] pseudo_pos (sequence<float>) - a sequence containing pseudo motor positions (only target energy in our case)
        @param[in] current_physical (sequence<float>) - a sequence containing the current physical motor positions
        @return the correct motor position
        @throws exception
        """
        target_energy = pseudo_pos[0]

        if axis in len(self.motor_roles):
            return target_energy
        else:
            raise Exception('Invalid axis %s to compute energy %s CalcPhysical()' % (str(axis), str(target_energy)))

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the energy pseudomotor.
        @param[in] axis: (expected always 1, since we provide only 1 pseudo motor)
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of the energy pseudo motor itself
        @return the energy pseudo motor value
        @throws exception
        """
        try:
            #get currently selected grating and spherical mirror
            energy_id = physical_pos[0]
            energy_mono = physical_pos[1]
        except:
            msg = 'Unable to retrieve insertion device and/or mono energies'
            self._log.error(msg)
            raise Exception(msg)

        if (energy_id is None) or (energy_mono is None):
            msg = 'Either insertion device or mono report invalid positions. ID: %s Mono: %s' % (str(energy_id), str(energy_mono))
            self._log.error(msg)
            raise Exception(msg)

        if (abs(energy_id - energy_mono) > self.tolerance):
            msg = 'Difference between insertion ID and mono is greater than tolerance. ID: %s Mono: %s' % (str(energy_id), str(energy_mono))
            self._log.error(msg)
            raise Exception(msg)

        return (energy_id + energy_mono) / 2.0
