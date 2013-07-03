#!/usr/bin/env python

import math

from sardana import DataAccess
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import Type, Access, Description


class Energy(object):
    """
    Energy pseudo motor controller for handling BL29-Boreas energy calculation given the positions
    of all the motors involved (and viceversa).
    """

    SM_VALID = range(2)
    GR_VALID = range(3)

    SM2, SM1 = SM_VALID #spherical mirrors 2 and 1
    HEG, MEG, LEG = GR_VALID #High, Medium and Low energy gratings

    #In case the source of the grating pitch is the encoder, we need to use these
    #values to convert that encoder value into grating pitch units (initialized
    #with default values, but will be modified by the BL29EnergyPCCtrl pseudo
    #counter controller)
    offset0 = 31005.9 #Offset in micro radiands to apply to the gr_pitch value got from the gr_pitch_source in order to get 0 reading at horizontal position
    step_per_unit = -41.249700939668187405641309100509

    h = 4.1357e-15  # eV*s
    c = 2.997925e17 # nm/s
    constant = h * c
    include_angles = [ 177*math.pi/180, 175*math.pi/180 ] # spherical mirrors include angles in radians (sm2 - sm1 respectively)
    offset = [0, 2.0*math.pi/180] #used to set the correct origin of the grating pitch axis (sm2 - sm1 respectively)
    energy_ranges = [ [ (1900,4500), (600,2100) ],
                      [ (950,3000),  (380,1700) ],
                      [ (250, 1500), (80, 1500) ] #Original values were[ (250, 600), (80,500) ]: changed on user request since MEG and HEG gratings are incorrectly installed
                    ] #working energy ranges in eV (electron volts), i is grating selected (he, me, le), j is sm selected (sm2, sm1)

    line_spacing = [ 1200, 800, 200 ] #line spacing in lines/mm (high, medium and low energy, respectively)

    #initialization of mirrors_offsets; this is just so the variables exist,
    #since their memorized values should be written in SetAxisExtraPar method of
    #the BL29EnergyMono class pseudomotor definition.
    #These are offset in grating pitch micro radians to sum to the grating
    #pitch read from the motor before computing the value of the energy.
    #This is due to the fact that the 3 gratings are no perfectly aligned in
    #exactly the same plane
    #Furthermore, users want to apply a different pitch offset depending
    #also of the sm selected, and hence this offsets become an array of: 
    #i is grating selected (he, me, le)
    #j is sm selected (sm2, sm1)
    mirrors_offsets = [[0.0 for i in SM_VALID] for j in GR_VALID]

    #energy ranges to be displayed for user comfort
    ranges = \
        'HEG + SM2: %s\n' % str(energy_ranges[HEG][SM2]) + \
        'HEG + SM1: %s\n' % str(energy_ranges[HEG][SM1]) + \
        'MEG + SM2: %s\n' % str(energy_ranges[MEG][SM2]) + \
        'MEG + SM1: %s\n' % str(energy_ranges[MEG][SM1]) + \
        'LEG + SM2: %s\n' % str(energy_ranges[LEG][SM2]) + \
        'LEG + SM1: %s\n' % str(energy_ranges[LEG][SM1])

    @staticmethod
    def get_energy(sm_selected, gr_selected, gr_pitch, gr_source_is_encoder=False):
        """
        Given the physical motor positions, it computes the energy pseudomotor.
        @param[in] sm_selected: the Spherical Mirror selected (0=SM2, 1=SM1)
        @param[in] gr_selected: the grating selected (0=HEG, 1=MEG, 2=LEG)
        @param[in] gr_pitch: grating pitch in micro radians or encoder counts
        @param[in] gr_source_is_encoder: specifies if the gr_pitch value is in micro radians or encoder counts
        @return the energy value corresponding to that combination of mirrors and grating pitch
        @throws exception
        """

        if not (sm_selected in Energy.SM_VALID) or not (gr_selected in Energy.GR_VALID) or (gr_pitch is None):
            msg = 'Spherical mirrors and/or grating mirror and/or grating pitch are not correctly set in get_energy()'
            raise Exception(msg)

        if gr_source_is_encoder:
            #transform the value of gr_pitch from encoder count to microradians
            gr_pitch = (gr_pitch / Energy.step_per_unit)
            print 'gr_pitch after step per unit (urad): %f' % gr_pitch
            #apply offset to get correct readings from 0 position
            gr_pitch = gr_pitch + Energy.offset0
            print 'gr_pitch + offset0 (urad): %f' % gr_pitch

        #convert from micro radians to radians
        gr_pitch = gr_pitch * 1.0e-6

        #get spherical mirror offset
        offset = Energy.offset[sm_selected]

        #line spacing
        D0 = Energy.line_spacing[gr_selected] * 1.0e-6

        #apply the user supplied mirrors combination offset depending on the GR
        #and SM selected and convert it from micro radians to radians
        gr_pitch += (Energy.mirrors_offsets[gr_selected][sm_selected] * 1e-6)

        #alpha, theta, beta and wave length
        alpha = math.pi/2 - offset - gr_pitch
        theta = Energy.include_angles[sm_selected]
        beta = alpha - theta
        wave_length =  ( math.sin(alpha) + math.sin(beta) ) / D0

        #finally we can compute energy
        energy = Energy.constant / wave_length #will throw exception if wave_length == 0

        return energy

    @staticmethod
    def check_mirrors(target_energy, sm, gr):
        """
        Given a target energy and the current SM and GR selected, it will check
        if this target energy is possible to be reached with that combination of
        mirrors. In case it isn't, it will return the correct combination of 
        SM and GR that would make it possible.
        If it's completely impossible to reach that energy with any mirrors
        combination, an exception will be thrown.
        @param[in] target_energy: the target energy to check
        @param[in] sm: the Spherical Mirror selected (0=SM2, 1=SM1)
        @param[in] gr: the grating selected (0=HEG, 1=MEG, 2=LEG)

        @return tuple containing:
        - True/False depending if passed energy is or not reachable with the
        passed position of SM and GR
        - SM that would do possible that energy (same as passed if returned True) 
        - GR that would do possible that energy (same as passed if returned True)

        @throws exception if absolutely impossible to reach the target energy or
        passed sm and/or gr position are invalid
        """

        #check that target energy is possible with current mirrors combination
        range_found = False
        if (sm in Energy.SM_VALID) and (gr in Energy.GR_VALID):
            current_min_energy = Energy.energy_ranges[gr][sm][0]
            current_max_energy = Energy.energy_ranges[gr][sm][1]
            if (target_energy >= current_min_energy) and (target_energy <= current_max_energy):
                range_found = True
                sm_target = sm
                gr_target = gr
        else:
            raise Exception('The GR and/or SM positions received are invalid')

        #If target energy not possible with current combination, find which
        #grating and spherical mirrors can give me that energy. If not possible,
        #then raise exception

        if range_found:
            possible=True
        else:
            possible=False
            mirrors_changed=False
            for i in range(len(Energy.line_spacing)):
                for j in range(len(Energy.include_angles)):
                    if (target_energy >= Energy.energy_ranges[i][j][0] and target_energy <= Energy.energy_ranges[i][j][1]):
                        sm_target = j
                        gr_target = i
                        mirrors_changed = True
                        break
                if mirrors_changed:
                    break
            else:
                msg = 'Energy %s out of any possible range' % str(target_energy)
                raise Exception(msg)

        return possible, sm_target, gr_target
