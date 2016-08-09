#!/usr/bin/env python

import math
import numpy
from scipy.optimize import fsolve

from BL29Energy import Energy

from sardana import DataAccess
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue


class BL29EnergyMono(PseudoMotorController):
    """
    Energy pseudo motor controller for handling BL29-Boreas theoretical energy of
    the monochromator given the positions of all the motors involved (and vice versa).
    This pseudo motor does not have access to the insertion device, so it gives
    or sets only the theoretical energy
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
            Access : DataAccess.ReadWrite,
            DefaultValue : False
        },
        'heg_sm2_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when HEG grating and SM2 are selected',
            Access : DataAccess.ReadWrite
        },
        'heg_sm1_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when HEG grating and SM1 are selected',
            Access : DataAccess.ReadWrite
        },
        'meg_sm2_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when MEG grating and SM2 are selected',
            Access : DataAccess.ReadWrite
        },
        'meg_sm1_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when MEG grating and SM1 are selected',
            Access : DataAccess.ReadWrite
        },
        'leg_sm2_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when LEG grating and SM2 are selected',
            Access : DataAccess.ReadWrite
        },
        'leg_sm1_offset' : {
            Type : float,
            Description : 'Offset to apply to the computed energy when LEG grating and SM1 are selected',
            Access : DataAccess.ReadWrite
        },
        'ranges' : {
            Type : str,
            Description : 'Energy ranges for each combination of SM and GR',
            Access : DataAccess.ReadOnly
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
            sm_current = int(self.sm_selected.position)
            gr_current = int(self.gr_selected.position)
        except:
            msg = 'Unable to determine SM and/or GR selected'
            self._log.error(msg)
            raise Exception(msg)

        target_reachable, sm_target, gr_target = Energy.check_mirrors(target_energy, sm_current, gr_current)

        #We need to change mirrors
        if not target_reachable:
            #if I'm allowed to change mirrors, then move them 
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
                    'Energy %s not possible without changing current mirrors combination.\n'\
                    'Valid range with current combination is %s..%s.\n' \
                    'Unlock mirrors if you want to automatically change them' %\
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
            msg = 'Invalid axis %s to compute energy %s CalcPhysical()' % (str(axis), str(target_energy))
            self._log.error(msg)
            raise Exception(msg)

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
            sm_selected = int(self.sm_selected.position)
            gr_selected = int(self.gr_selected.position)
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
        elif name == 'ranges':
            pass


class BL29EnergyMonoCorrected(BL29EnergyMono):
    """
    Energy pseudo motor controller for handling BL29-Boreas theoretical energy of
    the monochromator given the positions of all the motors involved (and vice versa).
    This pseudo motor does not have access to the insertion device, so it gives
    or sets only the theoretical energy.
    This controller is the very similar to BL29EnergyMono but it takes into
    account the non linearity between the grating pitch position and the energy,
    resulting in a more precise value of energy (both for reading and writing)
    """

    gender = 'Energy'
    model  = 'BL29-Boreas monochromator corrected energy calculation'
    organization = 'CELLS - ALBA'
    image = 'energy.png'
    logo = 'ALBA_logo.png'

    pseudo_motor_roles = ('energy_mono_corrected',)
    motor_roles = ('gr_pitch',)

    axis_attributes = {
        'enc_to_axis_factor' : {
            Type : float,
            Description : 'factor conversion between grating pitch encoder counts and axis counts',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.606697
        },
        'factor' : {
            Type : float,
            Access : DataAccess.ReadWrite,
            DefaultValue : 67.9905256862177
        },
        'offset' : {
            Type : float,
            Access : DataAccess.ReadWrite,
            DefaultValue : 418.0597939461368
        },
        'polynomials' : {
            Type : str,
            Description : 'polynomial factors',
            Access : DataAccess.ReadWrite,
            DefaultValue : '1074.28569845, -0.000865526898686, 1.68808503408e-10'
        },
        'amplitudes' : {
            Type : str,
            Description : 'amplitudes',
            Access : DataAccess.ReadWrite,
            DefaultValue : '31.59466847240000000 25.33828834800000000 12.92291016760000000 -2.60000435980000000 5.62300918241000000 -23.32303143910000000 148.49535194600000000 6.22915605381000000 -17.24367677390000000 0.60843513032300000'
        },
        'frequencies' : {
            Type : str,
            Description : 'frequencies',
            Access : DataAccess.ReadWrite,
            DefaultValue : '0.00000429173850425 0.00000535377109201 0.00003771785082810 0.00009176016823240 0.00007098244748240 0.00005848232526060 0.00001967372194620 0.00006394964256620 0.00001133551638280 0.00029402883062200'
        },
        'phases' : {
            Type : str,
            Description : 'frequencies',
            Access : DataAccess.ReadWrite,
            DefaultValue : '0.98456925250500000 7.57729621054000000 -8.64132917249000000 4.08645541884000000 8.77004121150000000 0.94163867557300000 -1.21582957911000000 1.50920490820000000 3.05628113377000000 1.43572736488000000'
        },
    }
    axis_attributes.update(BL29EnergyMono.axis_attributes)

    def __init__(self, inst, props, *args, **kwargs):
        """
        Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        @param *args extra arguments
        @param **kwargs keyword arguments
        """
        #for some reason setting default values doesn't seem to work if value never set (maybe a sardana bug?)
        self.enc_to_axis_factor = 0.606697
        self.factor = 67.9905256862177
        self.offset = 418.0597939461368
        self.polynomials = [1074.28569845, -0.000865526898686, 1.68808503408e-10]
        self.amplitudes = [31.59466847240000000,25.33828834800000000,12.92291016760000000,-2.60000435980000000,5.62300918241000000,-23.32303143910000000, 148.49535194600000000, 6.22915605381000000, -17.24367677390000000, 0.60843513032300000]
        self.frequencies = [0.00000429173850425,0.00000535377109201,0.00003771785082810,0.00009176016823240,0.00007098244748240, 0.00005848232526060, 0.00001967372194620, 0.00006394964256620, 0.00001133551638280, 0.00029402883062200]
        self.phases = [0.98456925250500000,7.57729621054000000,-8.64132917249000000,4.08645541884000000,8.77004121150000000, 0.94163867557300000, -1.21582957911000000, 1.50920490820000000, 3.05628113377000000, 1.43572736488000000]
        BL29EnergyMono.__init__(self, inst, props, *args, **kwargs)
        self.gr_pitch_motor = None

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
        if self.gr_pitch_motor == None: #this cannot be initialize in __init__
            self.gr_pitch_motor = self.GetMotor(self.motor_roles[0])
        gr_pitch = BL29EnergyMono.CalcPhysical(self, axis, pseudo_pos, current_physical)
        result, info, rc, mesg = fsolve(self.resolve_pitch, gr_pitch, args=gr_pitch, full_output=True)
        if rc != 1:
            msg = 'Unable to find a solution for %s: %s' % (str(self.motor_roles[0]), str(mesg))
            self._log.error(msg)
            raise Exception(msg)
        if type(result) != numpy.ndarray: #in old versions result was a float
            return result
        else:
            return result[0]

    def resolve_pitch(self, x, gr_pitch):
        """
        this function is the one that needs to be solved (find a 0) to go from
        gr_pitch_corrected to the real gr_pitch
        """
        return self.correct_gr_pitch(x) - gr_pitch

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the energy pseudomotor.
        @param[in] axis: (expected always 1, since we provide only 1 pseudo motor)
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of the energy pseudo motor itself
        @return the energy pseudo motor value
        @throws exception
        """
        if self.gr_pitch_motor == None: #this cannot be initialize in __init__
            self.gr_pitch_motor = self.GetMotor(self.motor_roles[0])
        try:
            #get currently selected grating and spherical mirror
            sm_selected = int(self.sm_selected.position)
            gr_selected = int(self.gr_selected.position)
            gr_pitch = physical_pos[0]
        except:
            msg = 'Unable to determine SM and/or GR selected and/or GR pitch'
            self._log.error(msg)
            raise Exception(msg)

        gr_pitch = physical_pos[0]
        gr_pitch_corrected = self.correct_gr_pitch(gr_pitch)
        return Energy.get_energy(sm_selected,gr_selected,gr_pitch_corrected)

    def correct_gr_pitch(self, gr_pitch):
        """
        This functions converts corrects the position of gr_pitch (in user units)
        to a new value which is much more closed to the actual value which would
        be necessary for computing a more realistic energy value.
        This new value is due to the fact that a movement in the gr_pitch motor
        does not really correspond to the computed value of energy. This error
        is due to the fact that gr_pitch pitch makes a linear movement which
        does not linearly match the real energy value.
        The correction is computed taking into account the axis position of the
        grating pitch motor (gr_pitch), not the user position.
        """
        total_offsets = self.offset + Energy.offset0
        gr_pitch_offset = self.gr_pitch_motor.get_offset().get_value()
        gr_pitch_axis = (gr_pitch_offset - gr_pitch) * self.gr_pitch_motor.step_per_unit
        axis_increment = self.compute_pitch(gr_pitch_axis)
        gr_pitch_corrected = total_offsets - axis_increment / self.factor
        return gr_pitch_corrected

    def compute_pitch(self, gr_pitch_axis):
        """
        This function computes the conversion between real axis counts to
        corrected axis counts. This value is a factor conversion between encoder
        counts and axis counts
        """
        #first the polynomial part is computed
        correction = 0.0
        for idx, polynomial in enumerate(self.polynomials):
            correction += (polynomial * math.pow(gr_pitch_axis,idx))

        #then the sinusoidal part is added
        if len(self.amplitudes)!=len(self.frequencies) or len(self.frequencies)!=len(self.phases):
            raise Exception('Amplitudes, frequencies and phases must be the same length')
        for amplitude, frequency, phase in zip(self.amplitudes,self.frequencies,self.phases):
            correction += (amplitude * math.sin(frequency*gr_pitch_axis + phase))

        #the new axis values are finally computed
        #the correction factor is necessary as the first computation was done using the encoder as driving value
        gr_corrected = gr_pitch_axis + correction / self.enc_to_axis_factor
        return gr_corrected

    def GetAxisExtraPar(self, axis, name):
        if name == 'enc_to_axis_factor':
            return self.enc_to_axis_factor
        elif name == 'factor':
            return self.factor
        elif name == 'offset':
            return self.offset
        elif name == 'polynomials':
            return str(self.polynomials).strip('[]').replace(',','')
        elif name == 'amplitudes':
            return str(self.amplitudes).strip('[]').replace(',','')
        elif name == 'frequencies':
            return str(self.frequencies).strip('[]').replace(',','')
        elif name == 'phases':
            return str(self.phases).strip('[]').replace(',','')
        else:
            return BL29EnergyMono.GetAxisExtraPar(self, axis, name)

    def SetAxisExtraPar(self, axis, name, value):
        if name == 'enc_to_axis_factor':
            if value==0:
                raise Exception('%s cannot be 0' % name)
            self.enc_to_axis_factor = value
        elif name == 'factor':
            if value==0:
                raise Exception('%s cannot be 0' % name)
            self.factor = value
        elif name == 'offset':
            self.offset = value
        elif name == 'polynomials':
            self.polynomials = [float(val) for val in value.split()]
        elif name == 'amplitudes':
            self.amplitudes = [float(val) for val in value.split()]
        elif name == 'frequencies':
            self.frequencies = [float(val) for val in value.split()]
        elif name == 'phases':
            self.phases = [float(val) for val in value.split()]
        else:
            return BL29EnergyMono.SetAxisExtraPar(self, axis, name, value)


class BL29Energy(PseudoMotorController):
    """
    Energy pseudo motor controller for handling BL29-Boreas energy coming out of
    the monochromator, given the energies reported both by the insertion device
    and the monochromator.
    This pseudo motor will give the real energy being delivered by the beamline,
    since it reads both the insertion device and the monochromator theoretical
    energies.
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
        'tolerance' : {
            Type : float,
            Description : 'Tolerance to consider that both the insertion device and the monochromator are in the same energy',
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
        self.sm_selected = PoolUtil.get_device(inst, self.sm_pseudo)
        self.gr_selected = PoolUtil.get_device(inst, self.gr_pseudo)
        self.tolerance = 1.0 #default value (will be overwritten if specified)


    def check_target(self, target_energy):
        """
        Given a target energy, it will check that it is reachable with current
        mirrors combination. If it isn't it will throw an exception
        it returns the correct motor position for that motor and energy.
        @param[in] target_energy - energy to check
        @throws exception
        """
        try:
            sm_current = self.sm_selected.position
            gr_current = self.gr_selected.position
        except:
            msg = 'Unable to determine SM and/or GR selected'
            self._log.error(msg)
            raise Exception(msg)

        #check if target energy is reachable with current mirrors combination
        target_reachable, sm_target, gr_target = Energy.check_mirrors(target_energy, sm_current, gr_current)
        if not target_reachable:
            msg = \
                'Energy %s not possible for the monochromator without changing current mirrors combination.\n'\
                'Valid range with current combination is %s..%s.\n' \
                'Unlock monochromator mirrors if you want to automatically change them' %\
                (str(target_energy), str(Energy.energy_ranges[gr_current][sm_current][0]), str(Energy.energy_ranges[gr_current][sm_current][1]))
            self._log.error(msg)
            raise Exception(msg)


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
        #get target energy and check if it is reachable with current mirrors
        target_energy = pseudo_pos[0]
        self.check_target(target_energy)

        if axis in range(1,len(self.motor_roles)+1):
            return target_energy
        else:
            msg = 'Invalid axis %s to compute energy %s CalcPhysical()' % (str(axis), str(target_energy))
            self._log.error(msg)
            raise Exception(msg)


    def CalcAllPhysical(self, pseudo_pos, current_physical):
        """
        """
        #get target energy and check if it is reachable with current mirrors
        target_energy = pseudo_pos[0]
        self.check_target(target_energy)
        return [target_energy, target_energy]


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

        self._log.debug('returning %f' % energy_mono)
        return energy_mono

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
        if name == 'tolerance':
            return self.tolerance

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
        if name == 'tolerance':
            self.tolerance = value


class BL29MaresReflectivity(object):
    """
    Utility class for computing physical and pseudo motors for BL29 MARES end
    station X Ray reflectivity for RSXS experiments.
    On the one hand it can compute the positions that the physical motors should
    be set to for a given a pseudo position.
    On the other hand, given the current values of the physical motors it can
    compute the value of any of the reflectivity pseudo motors.

                    _________
                  /           \
                 /  D1     D2  \
                /      ___      \
               /      /   \      \
    beam -->   |      | S | D3,4 |
               \      \___/      /
                \               /
                 \  D6     D5  /
                  \           /
                    ---------

    The reflectivity system is composed by 3 physical angular motors (see figure
    above, which represents the top view of the system):

    1) theta. This motor moves the theta plate (the inner plate shown in the
    figure), which is mounted on top of the 2theta plate. theta movement does
    not affect the 2theta position. On top of this plate the sample holder is
    mounted (S in the figure). The positive direction of the theta plate is
    counterclockwise.

    2) 2theta. This is the main plate on top of which the theta plate and all
    the detector arms are mounted. Each detector arm may have more than one
    detector. Note that when moving 2theta plate the theta plate (and hence the
    sample holder) will be dragged with it.
    The positive direction of the 2theta plate is clockwise.

    3) polar: this is the motorized sample holder (S in the figure) angular
    movement, which is clockwise positive.

    These 3 physical motor provide 3 useful pseudo motors:

    1) Sample. This is the sample angular position with respect to the beam.
    Note that this is affected by all the 3 physical motors listed above:
        sample = (theta2 - theta) + polar

    2) Detector. This is the detector angular position with respect to the beam:
    note that is is exactly the 2theta angular position + the nominal angular
    offset of the detector that is currently being used.

    3) Specular. This only makes sense when both the sample and the detector are
    aligned in a given position: in this case the specular position is the same
    as the sample angular position. Sample and detector are considered to be
    aligned if detector angular position is exactly the double of the sample:
         if 2*sample == detector then specular==sample else specular = NaN

    Note that users required to be able to use different offsets for the sample
    and all the detectors: this is useful for fine grain alignment of the sample.
    All these offsets have to be taken into account when computing the motor
    positions
    """

    THETA, THETA2 = range(1,3) #physical motors
    SAMPLE, SPECULAR, DETECTOR, BOTH = range(1,5) #pseudo motors

    #static variables (common to all subclasses and instances)
    detector_nominal_offset=0.0 #detector nominal position offset
    detector_offset=0.0 #detector fine grain user offset from respect its nominal position
    sample_offset=0.0 #sample offset from respect to its nominal position

    @classmethod
    def compute_physical(self, target_pseudo_pos, current_physical, pseudo_motor):
        """
        Given the desired pseudo motor position it returns the positions that
        physical motors should have in order to provide that pseudo motor position.
        """
        current_theta, current_theta2, current_polar = current_physical
        #compute target physical positions depending on requested pseudo motor
        #1) if we just want to move the sample then the theta2 motor must keep its current value
        if pseudo_motor == self.SAMPLE:
            target_theta2 = current_theta2
            target_theta = current_theta2 - target_pseudo_pos[0] + current_polar + self.sample_offset
        elif pseudo_motor == self.SPECULAR:
            target_theta2 = 2*target_pseudo_pos[0] - self.detector_nominal_offset - self.detector_offset
            target_theta = target_pseudo_pos[0] - self.detector_nominal_offset - self.detector_offset + current_polar + self.sample_offset
        elif pseudo_motor == self.DETECTOR:
            target_theta2 = target_pseudo_pos[0] - self.detector_nominal_offset - self.detector_offset
            target_theta = current_theta - (current_theta2 - target_theta2)
        elif pseudo_motor == self.BOTH: #compute th and th2 for a given sample and detector positions
            target_sample = target_pseudo_pos[0]
            target_detector = target_pseudo_pos[1]
            target_theta2 = target_detector - self.detector_nominal_offset - self.detector_offset
            target_theta = target_theta2 - target_sample + current_polar + self.sample_offset
        else:
            msg = 'Invalid pseudo_motor %s in compute_physical()' % str(pseudo_motor)
            self._log.error(msg)
            raise Exception(msg)

        return target_theta, target_theta2

    @classmethod
    def compute_pseudo(self, pseudo_axis, physical_pos, tolerance=0.0):
        """
        Given the physical motor positions, it computes the pseudo motor
        specified by pseudo_axis.
        """
        theta, theta2, polar = physical_pos
        sample = (theta2  - theta) + polar + self.sample_offset
        specular = theta2 + self.detector_nominal_offset + self.detector_offset
        if pseudo_axis == self.SAMPLE:
            return sample
        elif pseudo_axis == self.SPECULAR:
            if abs(2*sample - specular) <= tolerance:
                return sample
            else:
                return float('NaN')
        else:
            msg = 'Invalid axis %s to compute reflectivity compute_pseudo()' % str(axis)
            self._log.error(msg)
            raise Exception(msg)


class BL29MaresDetector(PseudoMotorController):
    """
    @deprecated: BL29MaresSampleDetector now implements this controller
    PseudoMotorController that provides the detectors angular position pseudo motors.
    See BL29MaresReflectivity documentation for more details on the system
    This motor provides the following pseudo motors:
        - detector
        - detector01
        - detector02
        ...
        - detector(MAX_DETECTORS)

    Note that unfortunately MAX_DETECTORS needs to be hardcoded. Ideally we
    should be able to add detectorXX just with the sardana API (e.g. defelem in
    spock) but this is not currently supported by sardana, and hence we have to
    define before hand which are the total number of detectors.
    *detector* is just a pointer to any of the *detectorXX*, which is considered
    to be the one in use. Note that when moving it will always be assumed that we
    want to move the detector in use (no matter if you try to move detectorXX)

    It only requires the 2theta angular position to compute the detectors positions
    However, it can optionally automatically correct the sample position in order
    to keep it at the value it was before moving the detector (note that 2theta
    plate drags the theta plate) and hence it also needs access to both theta and
    polar motors (these are provided as controller properties).

    There are several axis properties:
    - correct_sample (should be ctrl property, but we made like this for user
      simplicity): whether or not to automatically correct the sample position
      when moving the detector.
    - detector_in_use (should be ctrl property, but we made like this for user
      simplicity): this is a pointer to which of the different detectors is
      currently been used
    - nominal_offset: this is the nominal position in which the detector is
      positioned when the 2theta plate is at 0 degrees
    - offset: this is a fine grain offset for small user adjustments of detector
      position
    """

    gender = 'XRayReflectivity'
    model  = 'BL29-Boreas MARES (RSXS) end station detector positioning'
    organization = 'CELLS - ALBA'
    image = 'rsxs.png'
    logo = 'ALBA_logo.png'

    #internal variables
    FIRST_DETECTOR = 2 #first axis number that corresponds to a detector
    MAX_DETECTORS = 10 #maximum number of detectors
    detectors_nominal_offsets = []
    detectors_offsets = []
    detectors_user_names = []
    detector_used = 0
    correct_sample = False

    pseudo_motor_roles = tuple(['detector'] + ['detector%d' % i for i in range(MAX_DETECTORS)])
    motor_roles = ('2theta',)

    #controller properties
    ctrl_properties = {
        'theta_motor' : {
            Type : str,
            Description : 'The name of the theta motor (which may be necessary to reposition)'
        },
        'polar_motor' : {
            Type : str,
            Description : 'The name of the polar motor (which is necessary to compute pseudo, but we should never move it)'
        }
    }

    #axis attributes
    axis_attributes = {
        'correct_sample' : {
            Type : bool,
            Description : 'Whether or not to automatically move sample motor in order to keep sample position when moving detector',
            Access : DataAccess.ReadWrite,
            DefaultValue : False
        },
        'detector_in_use' : {
            Type : str,
            Description : 'Detector in use',
            Access : DataAccess.ReadWrite,
            DefaultValue : ''
        },
        'nominal_offset' : {
            Type : float,
            Description : 'Nominal offset of detector with respect to 0 alignment (in degrees)',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0
        },
        'offset' : {
            Type : float,
            Description : 'User fine grain offset of detector with respect to 0 alignment (in degrees)',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0
        },
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
        self.theta = PoolUtil.get_device(inst,self.theta_motor)
        self.polar = PoolUtil.get_device(inst,self.polar_motor)

    def get_detectors_info(self):
        """
        Get detectors information (offsets and names)
        """
        i=self.FIRST_DETECTOR
        while True:
            try:
                motor_name = self.GetAxisName(i)
                if motor_name != str(i): #GetAxisName returns str(i) if not found
                    self.detectors_offsets.append(0.0)
                    self.detectors_nominal_offsets.append(0.0)
                    self.detectors_user_names.append(motor_name.lower())
                    i+=1
                else:
                    break
            except:
                break

    def CalcPhysical(self, axis, pseudo_pos, current_physical):
        """
        Given the motor number and the desired pseudomotor positions it
        returns the correct motor position for that motor and pseudomotor position.
        @param[in] axis - motor number
        @param[in] pseudo_pos (sequence<float>) - a sequence containing target pseudo motor positions
        @param[in] current_physical (sequence<float>) - a sequence containing the current physical motor positions
        @return the correct motor position
        @throws exception
        """
        if axis==1: #2theta motor
            #it looks like the controller reuses current_physical between calls, so create a copy to avoid modifying it:
            #thought in this case there is only one axis it doesn't matter (only one call should be done), but you never know
            physical = current_physical[:]
            physical.insert(0,self.theta.position)
            physical.append(self.polar.position)
            th, th2 = BL29MaresReflectivity.compute_physical(pseudo_pos, physical, BL29MaresReflectivity.DETECTOR)
            #if automatic sample position correction is enable then move theta to necessary position
            if self.correct_sample:
                self.theta.position = th
            return th2
        else:
            msg = '%d is not valid axis' % axis
            self._log.error(msg)
            raise Exception(msg)

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the pseudomotor specified by axis.
        @param[in] axis: the pseudo motor to be computed
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of all the pseudo motors
        @return the corresponding pseudo
        @throws exception
        """
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        num_detectors = len(self.detectors_user_names)
        if num_detectors== 0:
            self.get_detectors_info()
        if axis==1: #detector in use
            return physical_pos[0] + self.detectors_nominal_offsets[self.detector_used] + self.detectors_offsets[self.detector_used]
        elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors): #a given detector
            return physical_pos[0] + self.detectors_nominal_offsets[axis-self.FIRST_DETECTOR] + self.detectors_offsets[axis-self.FIRST_DETECTOR]

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
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        num_detectors = len(self.detectors_user_names)
        if num_detectors== 0:
            self.get_detectors_info()
            num_detectors = len(self.detectors_user_names)
        if name == 'correct_sample':
            return self.correct_sample
        elif name == 'detector_in_use':
            return self.detectors_user_names[self.detector_used]
        elif name == 'nominal_offset':
            if axis==1:
                return self.detectors_nominal_offsets[self.detector_used]
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                return self.detectors_nominal_offsets[axis-self.FIRST_DETECTOR]
            else:
                msg = 'Axis %d does not have property nominal_offset' % axis
                self._log.error(msg)
                raise Exception(msg)
        elif name == 'offset':
            if axis==1:
                return self.detectors_offsets[self.detector_used]
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                return self.detectors_offsets[axis-self.FIRST_DETECTOR]
            else:
                msg = 'Axis %d does not have property offset' % axis
                self._log.error(msg)
                raise Exception(msg)

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
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        num_detectors = len(self.detectors_user_names)
        if num_detectors== 0:
            self.get_detectors_info()
            num_detectors = len(self.detectors_user_names)
        if name == 'correct_sample':
            self.correct_sample = value
        elif name == 'detector_in_use':
            #we asume that it is not possible to have repeated user motor names
            try:
                self.detector_used = self.detectors_user_names.index(value.lower())
                BL29MaresReflectivity.detector_offset = self.detectors_offsets[self.detector_used]
                BL29MaresReflectivity.detector_nominal_offset = self.detectors_nominal_offsets[self.detector_used]
            except ValueError:
                msg = '%s is not valid detector name' % value
                self._log.error(msg)
                raise Exception(msg)
        elif name == 'nominal_offset':
            if axis==1:
                self.detectors_nominal_offsets[self.detector_used] = value
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                self.detectors_nominal_offsets[axis-self.FIRST_DETECTOR] = value
            else:
                msg = 'Axis %d does not have property nominal_offset' % axis
                self._log.error(msg)
                raise Exception(msg)
            BL29MaresReflectivity.detector_nominal_offset = self.detectors_nominal_offsets[self.detector_used]
        elif name == 'offset':
            if axis==1:
                self.detectors_offsets[self.detector_used] = value
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                self.detectors_offsets[axis-self.FIRST_DETECTOR] = value
            else:
                msg = 'Axis %d does not have property offset' % axis
                self._log.error(msg)
                raise Exception(msg)
            BL29MaresReflectivity.detector_offset = self.detectors_offsets[self.detector_used]


class BL29MaresSample(PseudoMotorController):
    """
    @deprecated: BL29MaresSampleDetector now implements this controller
    PseudoMotorController that provides the sample angular position pseudo motor.
    See BL29MaresReflectivity documentation for more details on the system
    """

    gender = 'XRayReflectivity'
    model  = 'BL29-Boreas MARES (RSXS) end station sample positioning'
    organization = 'CELLS - ALBA'
    image = 'rsxs.png'
    logo = 'ALBA_logo.png'

    pseudo_motor_roles = ('sample',)
    motor_roles = ('theta',)

    #controller properties
    ctrl_properties = {
        'theta2_motor' : {
            Type : str,
            Description : 'The name of the 2theta motor'
        },
        'polar_motor' : {
            Type : str,
            Description : 'The name of the polar motor'
        }
    }

    #axis attributes
    axis_attributes = {
        'offset' : {
            Type : float,
            Description : 'sample offset (in degrees)',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0
        },
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
        self.theta2 = PoolUtil.get_device(inst,self.theta2_motor)
        self.polar = PoolUtil.get_device(inst,self.polar_motor)

    def CalcPhysical(self, axis, pseudo_pos, current_physical):
        """
        Given the motor number and the desired pseudomotor positions it
        returns the correct motor position for that motor and pseudomotor position.
        @param[in] axis - motor number
        @param[in] pseudo_pos (sequence<float>) - a sequence containing pseudo motor positions
        @param[in] current_physical (sequence<float>) - a sequence containing the current physical motor positions
        @return the correct motor position
        @throws exception
        """
        #it looks like the controller reuses current_physical between calls, so create a copy to avoid modifying it:
        #thought in this case there is only one axis it doesn't matter (only one call should be done), but you never know
        physical = current_physical[:]
        physical.append(self.theta2.position)
        physical.append(self.polar.position)
        th, th2 = BL29MaresReflectivity.compute_physical(pseudo_pos, physical, BL29MaresReflectivity.SAMPLE)
        return th

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the pseudomotor specified by axis.
        @param[in] axis: the pseudo motor to be computed
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of all the pseudo motors
        @return the corresponding pseudo
        @throws exception
        """
        physical = physical_pos[:]
        physical.append(self.theta2.position)
        physical.append(self.polar.position)
        return BL29MaresReflectivity.compute_pseudo(BL29MaresReflectivity.SAMPLE, physical)

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
        if name == 'offset':
            return BL29MaresReflectivity.sample_offset

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
        if name == 'offset':
            BL29MaresReflectivity.sample_offset = value


class BL29MaresSpecular(PseudoMotorController):
    """
    PseudoMotorController that provides the specular position pseudo motor.
    See BL29MaresReflectivity documentation for more details on the system
    """

    gender = 'XRayReflectivity'
    model  = 'BL29-Boreas MARES (RSXS) end station X ray reflectivity pseudomotors'
    organization = 'CELLS - ALBA'
    image = 'rsxs.png'
    logo = 'ALBA_logo.png'

    pseudo_motor_roles = ('specular',)
    motor_roles = ('theta', '2theta')

    #controller properties
    ctrl_properties = {
        'polar_motor' : {
            Type : str,
            Description : 'The name of the polar motor (which is necessary to compute pseudo, but we should never move it)'
        }
    }

    #axis attributes
    axis_attributes = {
        #tolerance should actually be a controller property but since it may be
        #necessary to be modified by user it is defined like this for user
        #convenience: users know the motor names, but don't care at all about
        #controller names
        'tolerance' : {
            Type : float,
            Description : 'Tolerance to consider that theta and 2theta are properly aligned',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0
        }
    }

    #internal variable
    tolerance = 0.0

    def __init__(self, inst, props, *args, **kwargs):
        """
        Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        @param *args extra arguments
        @param **kwargs keyword arguments
        """
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.polar = PoolUtil.get_device(inst,self.polar_motor)

    def CalcAllPhysical(self, pseudo_pos, current_physical):
        """
        Given the motor number and the desired pseudomotor positions it
        returns the correct motor position for that motor and pseudomotor position.
        :param sequence<float> pseudo_pos: a sequence containing pseudo motor
        positions
        :param sequence<float> curr_physical_pos: a sequence containing the
        current physical motor positions
        :return: a sequece of motor positions (one for each motor role)
        :rtype: sequence<float>
        """
        #it looks like the controller reuses current_physical between calls, so create a copy to avoid modifying it
        physical = current_physical[:]
        physical.append(self.polar.position)
        targets = BL29MaresReflectivity.compute_physical(pseudo_pos, physical, BL29MaresReflectivity.SPECULAR)
        return targets

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the pseudomotor specified by axis.
        @param[in] axis: the pseudo motor to be computed
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of all the pseudo motors
        @return the corresponding pseudo
        @throws exception
        """
        physical = physical_pos[:]
        physical.append(self.polar.position)
        if axis==1: #specular
            return BL29MaresReflectivity.compute_pseudo(BL29MaresReflectivity.SPECULAR, physical, self.tolerance)
        else:
            msg = '%d is not valid axis' % axis, physical_pos, current_pseudo
            self._log.error(msg)
            raise Exception(msg)

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
        if name == 'tolerance':
            return self.tolerance

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
        if name == 'tolerance':
            self.tolerance = value


class BL29MaresSampleDetector(PseudoMotorController):
    """
    PseudoMotorController that provides angular position pseudo motors for the
    sample and all detectors.
    See BL29MaresReflectivity documentation for more details on the system
    This motor provides the following pseudo motors:
        - sample
        - detector
        - detector01
        - detector02
        ...
        - detector(MAX_DETECTORS)

    Note that unfortunately MAX_DETECTORS needs to be hardcoded. Ideally we
    should be able to dynamically add detectorXX just with the sardana API (e.g.
    defelem in spock) but this is not currently supported by sardana, and hence
    we have to define before hand which are the total number of detectors.
    *detector* is just a pointer to any of the *detectorXX*, which is considered
    to be the one in use. Note that when moving it will always be assumed that
    we want to move the detector in use (even if you try to move detectorXX)

    It requires the theta, 2theta and polar  angular positions in order to
    compute the sample position, but only the 2theta position in order to
    compute the detectors positions

    There are several axis properties:
    - detector_in_use (should be ctrl property, but we made it like this for
      user simplicity): this is a pointer to which of the different detectors is
      currently been used
    - nominal_offset: this is the nominal position in which the detector is
      positioned when the 2theta plate is at 0 degrees
    - offset: this is a fine grain offset for small user adjustments both for
      sample and detector positions
    """

    gender = 'XRayReflectivity'
    model  = 'MARES (RSXS) end station of BL29-Boreas sample and detector positions'
    organization = 'CELLS - ALBA'
    image = 'rsxs.png'
    logo = 'ALBA_logo.png'

    #internal variables
    FIRST_DETECTOR = 3 #first axis number that corresponds to a detector
    MAX_DETECTORS = 10 #maximum number of detectors
    detectors_nominal_offsets = []
    detectors_offsets = []
    detectors_user_names = []

    pseudo_motor_roles = tuple(['sample','detector'] + ['detector%d' % i for i in range(MAX_DETECTORS)])
    motor_roles = ('theta','2theta',)

    #controller properties
    ctrl_properties = {
        'polar_motor' : {
            Type : str,
            Description : 'The name of the polar motor (which is necessary to compute pseudo, but we should never move it)'
        }
    }

    #axis attributes
    axis_attributes = {
        'detector_in_use' : {
            Type : str,
            Description : 'Detector in use',
            Access : DataAccess.ReadWrite,
            DefaultValue : ''
        },
        'nominal_offset' : {
            Type : float,
            Description : 'Nominal offset of detector arm with respect to 0 alignment (in degrees)',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0
        },
        'offset' : {
            Type : float,
            Description : 'Sample offset or fine grain offset of detector with respect to detector\'s arm (in degrees)',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0
        },
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
        self.polar = PoolUtil.get_device(inst,self.polar_motor)
        self.detector_used = None

    def get_detectors_info(self):
        """
        Get detectors information (offsets and names)
        """
        i=self.FIRST_DETECTOR
        while True:
            try:
                motor_name = self.GetAxisName(i)
                if motor_name != str(i): #GetAxisName returns str(i) if not found
                    self.detectors_offsets.append(0.0)
                    self.detectors_nominal_offsets.append(0.0)
                    self.detectors_user_names.append(motor_name.lower())
                    i+=1
                else:
                    break
            except:
                break

    def CalcAllPhysical(self, pseudo_pos, current_physical):
        """
        Given the desired pseudomotor positions it returns the correct motor
        position for all motors that would provide those pseudomotor positions.
        :param sequence<float> pseudo_pos: a sequence containing pseudo motor
        positions
        :param sequence<float> curr_physical_pos: a sequence containing the
        current physical motor positions
        :return: a sequece of motor positions (one for each motor role)
        :rtype: sequence<float>
        """
        physical = current_physical[:]
        physical.append(self.polar.position)
        th, th2 = BL29MaresReflectivity.compute_physical(pseudo_pos, physical, BL29MaresReflectivity.BOTH)
        return (th, th2)

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the pseudomotor specified by axis.
        @param[in] axis: the pseudo motor to be computed
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of all the pseudo motors
        @return the corresponding pseudo
        @throws exception
        """
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        num_detectors = len(self.detectors_user_names)
        if num_detectors== 0:
            self.get_detectors_info()
        physical = physical_pos[:]
        physical.append(self.polar.position)
        if axis==1: #sample
            return BL29MaresReflectivity.compute_pseudo(BL29MaresReflectivity.SAMPLE, physical)
        elif axis==2: #detector in use
            return physical_pos[1] + self.detectors_nominal_offsets[self.detector_used] + self.detectors_offsets[self.detector_used]
        elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors): #a given detector
            return physical_pos[1] + self.detectors_nominal_offsets[axis-self.FIRST_DETECTOR] + self.detectors_offsets[axis-self.FIRST_DETECTOR]

    def GetAxisExtraPar(self, axis, name):
        """
        Get extra controller parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to get
        @param name of the parameter to retrieve
        @return the value of the parameter
        """
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        num_detectors = len(self.detectors_user_names)
        if num_detectors== 0:
            self.get_detectors_info()
            num_detectors = len(self.detectors_user_names)
        if name == 'detector_in_use':
            return self.detectors_user_names[self.detector_used]
        elif name == 'nominal_offset':
            if axis==2:
                return self.detectors_nominal_offsets[self.detector_used]
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                return self.detectors_nominal_offsets[axis-self.FIRST_DETECTOR]
            else:
                msg = 'Axis %d does not have property nominal_offset' % axis
                self._log.error(msg)
                raise Exception(msg)
        elif name == 'offset':
            if axis==1:
                return BL29MaresReflectivity.sample_offset
            if axis==2:
                return self.detectors_offsets[self.detector_used]
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                return self.detectors_offsets[axis-self.FIRST_DETECTOR]
            else:
                msg = 'Axis %d does not have property offset' % axis
                self._log.error(msg)
                raise Exception(msg)

    def SetAxisExtraPar(self, axis, name, value):
        """
        Set extra axis parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to set
        @param name of the parameter to set
        @param value to be set
        """
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        num_detectors = len(self.detectors_user_names)
        if num_detectors== 0:
            self.get_detectors_info()
            num_detectors = len(self.detectors_user_names)
        if name == 'detector_in_use':
            #we asume that it is not possible to have repeated user motor names
            try:
                self.detector_used = self.detectors_user_names.index(value.lower())
            except ValueError:
                msg = '%s is not valid detector name' % value
                self._log.error(msg)
                raise Exception(msg)
        elif name == 'nominal_offset':
            if axis==2:
                self.detectors_nominal_offsets[self.detector_used] = value
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                self.detectors_nominal_offsets[axis-self.FIRST_DETECTOR] = value
            else:
                msg = 'Axis %d does not have property nominal_offset' % axis
                self._log.error(msg)
                raise Exception(msg)
        elif name == 'offset':
            if axis==1:
                BL29MaresReflectivity.sample_offset = value
            elif axis==2:
                if self.detector_used != None: #only if detector_used was already initialized
                    self.detectors_offsets[self.detector_used] = value
            elif axis in range(self.FIRST_DETECTOR,self.FIRST_DETECTOR+num_detectors):
                self.detectors_offsets[axis-self.FIRST_DETECTOR] = value
            else:
                msg = 'Axis %d does not have property offset' % axis
                self._log.error(msg)
                raise Exception(msg)
        #this is necessary since we don't know the order in which parameters
        #will be set when initializing the controller
        self.update_info()

    def update_info(self):
        if self.detector_used != None:
            BL29MaresReflectivity.detector_offset = self.detectors_offsets[self.detector_used]
            BL29MaresReflectivity.detector_nominal_offset = self.detectors_nominal_offsets[self.detector_used]
