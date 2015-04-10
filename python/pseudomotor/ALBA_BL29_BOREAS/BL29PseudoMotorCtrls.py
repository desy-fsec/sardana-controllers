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
            Access : DataAccess.ReadWrite
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
            raise Exception('Invalid axis %s to compute energy %s CalcPhysical()' % (str(axis), str(target_energy)))


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

    THETA, THETA2 = range(1,3)
    SAMPLE, SPECULAR = range(1,3)

    @classmethod
    def compute_physical(self, axis, pseudo_pos, current_physical, pseudo, detector_offset=0.0):
        """
        Given the motor number and the desired pseudomotor position it
        returns the correct motor position for that motor and pseudomotor position.
        """
        #compute target physical positions
        target = pseudo_pos[0]
        current_theta, current_theta2, current_polar = current_physical
        if pseudo == self.SAMPLE:
            target_theta = current_theta2 - target + current_polar
            target_theta2 = current_theta2
        elif pseudo == self.SPECULAR:
            target_theta =    target - detector_offset + current_polar  
            target_theta2 = 2*target - detector_offset
        else:
            raise Exception('Invalid pseudo %s in compute_physical()' % str(pseudo))

        #return the proper physical position
        if (axis == self.THETA):
            return target_theta
        elif (axis == self.THETA2):
            return target_theta2
        else:
            raise Exception('Invalid axis %s in compute_physical()' % str(axis))

    @classmethod
    def compute_pseudo(self, axis, physical_pos, current_pseudo, tolerance=0.0, detector_offset=0.0):
        """
        Given the physical motor positions, it computes the pseudomotor specified by axis.
        """
        theta, theta2, polar = physical_pos
        sample = -theta + polar + theta2
        if axis == self.SAMPLE:
            return sample
        elif axis == self.SPECULAR:
            if ( abs(2*sample - (theta2 + detector_offset)) <= tolerance ):
                return sample
            else:
                return float('NaN')
        else:
            raise Exception('Invalid axis %s to compute reflectivity compute_pseudo()' % str(axis))


class BL29MaresSample(PseudoMotorController):
    """
    """

    gender = 'XRayReflectivity'
    model  = 'BL29-Boreas MARES (RSXS) end station X ray reflectivity pseudomotors'
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
        return BL29MaresReflectivity.compute_physical(axis, pseudo_pos, physical, BL29MaresReflectivity.SAMPLE)

    def CalcPseudo(self, axis, physical_pos, current_pseudo):
        """
        Given the physical motor positions, it computes the pseudomotor specified by axis.
        @param[in] axis: the pseudo motor to be computed
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @param[in] current_pseudo: current value of all the pseudo motors
        @return the corresponding pseudo
        @throws exception
        """
        physical_pos.append(self.theta2.position)
        physical_pos.append(self.polar.position)
        return BL29MaresReflectivity.compute_pseudo(BL29MaresReflectivity.SAMPLE, physical_pos, current_pseudo)


class BL29MaresSpecular(PseudoMotorController):
    """
    """

    gender = 'XRayReflectivity'
    model  = 'BL29-Boreas MARES (RSXS) end station X ray reflectivity pseudomotors'
    organization = 'CELLS - ALBA'
    image = 'rsxs.png'
    logo = 'ALBA_logo.png'

    #internal variables
    DETECTORS = 5 #number of detectors
    detectors_offsets = [0.0 for i in range(DETECTORS)]
    detectors_user_names = []
    detector_used = 0
    tolerance = 0.0

    pseudo_motor_roles = tuple(['specular'] + ['detector%d' % i for i in range(DETECTORS)])
    motor_roles = ('theta', '2theta')

    #controller properties
    ctrl_properties = {
        'polar_motor' : {
            Type : str,
            Description : 'The name of the polar motor'
        }
    }

    #axis attributes
    axis_attributes = {
        #tolerance should actually be a controller property but since it may be necessary to
        #be modified by user it is defined like this for user convenience:
        #users know the motor names, but don't care at all about controller names
        'tolerance' : {
            Type : float,
            Description : 'Tolerance to consider that theta and 2theta are properly aligned',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0
        },
        'detector_in_use' : {
            Type : str,
            Description : 'Detector in use',
            Access : DataAccess.ReadWrite,
            DefaultValue : ''
        },
        'offset' : {
            Type : float,
            Description : 'Arrays of offsets of detectors with respect to 0 alignment (in degrees)',
            Access : DataAccess.ReadWrite,
            DefaultValue : 0.0 #[0.0 for i in range(self.DETECTORS)]
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

    def retrieve_detectors_names(self):
        """
        """
        for i in range(1,self.DETECTORS+1):
            motor = self.GetPseudoMotor(i)
            self.detectors_user_names.append(motor.get_name().lower())

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
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        if len(self.detectors_user_names) == 0:
            self.retrieve_detectors_names()
        #it looks like the controller reuses current_physical between calls, so create a copy to avoid modifying it
        physical = current_physical[:]
        physical.append(self.polar.position)
        return BL29MaresReflectivity.compute_physical(axis, pseudo_pos, physical, BL29MaresReflectivity.SPECULAR, self.detectors_offsets[self.detector_used])


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
        if len(self.detectors_user_names) == 0:
            self.retrieve_detectors_names()
        physical_pos.append(self.polar.position)
        if axis==1:
            return BL29MaresReflectivity.compute_pseudo(BL29MaresReflectivity.SPECULAR, physical_pos, current_pseudo, self.tolerance, self.detectors_offsets[self.detector_used])
        elif axis in range(2,self.DETECTORS+2):
            return physical_pos[1] + self.detectors_offsets[axis-2]
        else:
            msg = '%d is not valid axis' % axis
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
        #since pseudomotors are not available during __init__ this must be filled on first call to any method
        if len(self.detectors_user_names) == 0:
            self.retrieve_detectors_names()
        if name == 'tolerance':
            return self.tolerance
        elif name == 'detector_in_use':
            return self.detectors_user_names[self.detector_used]
        elif name == 'offset':
            if not axis in range(2,self.DETECTORS+2):
                msg = 'Axis %d does not have property offset' % axis
                self._log.error(msg)
                raise Exception(msg)
            return self.detectors_offsets[axis-2]

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
        if len(self.detectors_user_names) == 0:
            self.retrieve_detectors_names()
        if name == 'tolerance':
            self.tolerance = value
        elif name == 'detector_in_use':
            #we asume that it is not possible to have repeated user motor names
            try:
                self.detector_used = self.detectors_user_names.index(value.lower())
            except ValueError:
                msg = '%s is not valid detector name' % value
                self._log.error(msg)
                raise Exception(msg)
        elif name == 'offset':
            if not axis in range(2,self.DETECTORS+2):
                msg = 'Axis %d does not have property offset' % axis
                self._log.error(msg)
                raise Exception(msg)
            self.detectors_offsets[axis-2] = value
