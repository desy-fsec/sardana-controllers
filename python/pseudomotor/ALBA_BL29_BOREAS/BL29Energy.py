#!/usr/bin/env python

import math
import PyTango
import logging
from pool import PseudoMotorController


class Energy(PseudoMotorController):
    """Energy pseudo motor controller for handling BL29-Boreas energy calculation given the positions
    of all the motors involved (and viceversa)."""

    gender = "PseudoMotor"
    model  = "BL29-Boreas energy calculation"
    organization = "CELLS - ALBA"
    image = "energy.png"
    logo = "ALBA_logo.png"

    pseudo_motor_roles = ("Energy",)
    motor_roles = ("gr_pitch",)

    h = 4.1357e-15  # eV*s
    c = 2.997925e17 # nm/s
    constant = h * c
    include_angles = [ 177*math.pi/180, 175*math.pi/180 ] # spherical mirrors include angles in radians (sm2 - sm1 respectively)
    sm_offset = [0, 2.0*math.pi/180] #used to set the correct origin of the grating pitch axis (sm2 - sm1 respectively)
    energy_ranges = [ [ (1900,4500), (600,2100) ],
                      [ (950,3000),  (380,1700) ],
                      [ (250, 600), (80,500) ]
                    ] #working energy ranges in eV (electron volts), i is grating selected (he, me, le), j is sm selected (sm2, sm1)

    line_spacing = [ 1200, 800, 200 ] #line spacing in lines/mm (high, medium and low energy, respectively)

    class_prop = {
        'sm_selected_ior':{'Type':'PyTango.DevString','Description':'The name of the IORegister to read/select which SM to use'},
        'gr_selected_ior':{'Type':'PyTango.DevString','Description':'The name of the IORegister to read/select which grating to use'}
    }

    #extra attributes
    ctrl_extra_attributes = {
        'lock_mirrors':
        {'Type':'PyTango.DevBoolean',
        'Description':'Whether or not allow me to change spherical mirror and/or gratings when asked to go to a given energy',
        'R/W Type':'PyTango.READ_WRITE'},
        'heg_sm2_offset':
        {'Type':'PyTango.DevDouble',
        'Description':'Offset to apply to the computed energy when HEG grating and SM2 are selected',
        'R/W Type':'PyTango.READ_WRITE'},
        'heg_sm1_offset':
        {'Type':'PyTango.DevDouble',
        'Description':'Offset to apply to the computed energy when HEG grating and SM1 are selected',
        'R/W Type':'PyTango.READ_WRITE'},
        'meg_sm2_offset':
        {'Type':'PyTango.DevDouble',
        'Description':'Offset to apply to the computed energy when MEG grating and SM2 are selected',
        'R/W Type':'PyTango.READ_WRITE'},
        'meg_sm1_offset':
        {'Type':'PyTango.DevDouble',
        'Description':'Offset to apply to the computed energy when MEG grating and SM1 are selected',
        'R/W Type':'PyTango.READ_WRITE'},
        'leg_sm2_offset':
        {'Type':'PyTango.DevDouble',
        'Description':'Offset to apply to the computed energy when LEG grating and SM2 are selected',
        'R/W Type':'PyTango.READ_WRITE'},
        'leg_sm1_offset':
        {'Type':'PyTango.DevDouble',
        'Description':'Offset to apply to the computed energy when LEG grating and SM1 are selected',
        'R/W Type':'PyTango.READ_WRITE'},
        'ranges':
        {'Type':'PyTango.DevString',
        'Description':'Energy ranges for each combination of SM and GR',
        'R/W Type':'PyTango.READ'},
        'debug':
        {'Type':'PyTango.DevBoolean',
        'Description':'If set to true, it will output verbose information on the Pool console',
        'R/W Type':'PyTango.READ_WRITE'},
    }


    def __init__(self,inst,props):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        PseudoMotorController.__init__(self,inst,props)
        self.sm_selected_ior_dev = PyTango.DeviceProxy(self.sm_selected_ior)
        self.gr_selected_ior_dev = PyTango.DeviceProxy(self.gr_selected_ior)
        self.lock_mirrors = True

        #Initialization of grating_offsets; this is just so the variables exist,
        #since their memorized values will be written in SetExtraAttributePar
        #These are offsets in grating pitch units to be summed to the read pitch
        #before computing the energy (since the 3 gratings are no perfectly aligned)
        #i is grating selected (he, me, le), j is sm selected (sm2, sm1)
        #This is different to sm_offset, which also causes an offset depending on the SM selected
        #Also note that sm_offset units are radians, while the grating offsets are expressed in
        #gr_pitch units (current user units are micro radians)
        self.heg_sm2_offset = 0.0
        self.heg_sm1_offset = 0.0
        self.meg_sm2_offset = 0.0
        self.meg_sm1_offset = 0.0
        self.leg_sm2_offset = 0.0
        self.leg_sm1_offset = 0.0
        self.grating_offsets = [[ self.heg_sm2_offset, self.heg_sm1_offset ],
                                [ self.meg_sm2_offset, self.meg_sm1_offset ],
                                [ self.leg_sm2_offset, self.leg_sm1_offset ]]

        #energy ranges to be displayed for user comfort
        self.ranges = 'HEG + SM2: %s\n' % str(self.energy_ranges[0][0]) + \
                      'HEG + SM1: %s\n' % str(self.energy_ranges[0][1]) + \
                      'MEG + SM2: %s\n' % str(self.energy_ranges[1][0]) + \
                      'MEG + SM1: %s\n' % str(self.energy_ranges[1][1]) + \
                      'LEG + SM2: %s\n' % str(self.energy_ranges[2][0]) + \
                      'LEG + SM1: %s\n' % str(self.energy_ranges[2][1])

        #debug disabled by default
        self.debug = False
        #save logger original level (we may need to restore it) 
        self.log_level_original = self._log.level


    def calc_physical(self,index,pseudo_pos):
        """Given the motor number (gr-pitch) and the desired energy it
        returns the correct motor position for that motor and energy.
        @param[in] motor number and desired energy
        @return the correct motor position
        @throws exception
        """

        energy = pseudo_pos[0]

        #determine SM and GR selected
        try:
            sm_selected = self.sm_selected_ior_dev.read_attribute("Value").value
            gr_selected = self.gr_selected_ior_dev.read_attribute("Value").value
        except Exception, e:
            raise RuntimeError("Unable to get SM and/or GR positions: %s" % repr(e))

        #If I'm not allowed to change mirrors, then check that we can go to the
        #requested energy without changing any mirror. If not possible, then raise exception
        if self.lock_mirrors:
            min_value = Energy.energy_ranges[gr_selected][sm_selected][0]
            max_value = Energy.energy_ranges[gr_selected][sm_selected][1]
            if (energy < min_value) or (energy > max_value):
                raise RuntimeError("Energy %s not possible with current mirrors combination. Valid range with "
                                   "current combination is %s..%s. Unlock mirrors if you want to automatically change them"
                                   % (str(energy), min_value, max_value) )
        else:
        #I'm allowed to change mirrors, so look for the combination of mirrors
        #that can provide that energy (grating and spherical mirrors) and move
        #those motors to that position
            #find which grating and spherical mirrors can give me that energy. If
            #not possible, then raise exception
            range_found = False
            for i in range(len(Energy.line_spacing)):
                for j in range(len(Energy.include_angles)):
                    if (energy >= Energy.energy_ranges[i][j][0] and energy <= Energy.energy_ranges[i][j][1]):
                        sm_selected = j
                        gr_selected = i
                        range_found = True
                        break
                if range_found:
                    break
            else:
                raise RuntimeError("Energy %s out of range calc_physical()" % str(energy))
            #finally, move the mirrors
            try:
                self.sm_selected_ior_dev.write_attribute("value", sm_selected)
                self.gr_selected_ior_dev.write_attribute("value", gr_selected)
            except Exception, e:
                raise RuntimeError("Error while trying to position mirrors in %s::calc_physical: %s" % (self.__class__.__name__, str(e)) )

        sm_offset = Energy.sm_offset[sm_selected]

        if index == 1:
            #compute gr_pitch
            wave_length = Energy.constant / energy
            theta = Energy.include_angles[sm_selected]
            D0 = Energy.line_spacing[gr_selected]

            #Assuming m will always be 1.0 and doing basic simplification, the computation:
            #beta = -acos((m*lambbda*1.e-9*D0*1.e3/2) * tan(theta/2) + 
            #              sqrt(cos(theta/2)**2 - (m*lambbda*1.e-9*D0*1.e3/2)**2)
            #            )
            #Can be expressed as:
            beta = -1.0 * math.acos(
                             (wave_length*D0*5e-7) * math.tan(theta/2) + math.sqrt(math.cos(theta/2)**2 - (wave_length*D0*5e-7)**2 )
                            )

            alpha = theta + beta

            gr_pitch = (math.pi/2 - alpha - sm_offset) #radians

            self._log.debug("<------------------------------------------------------- calc_physical")
            self._log.debug("sm_offset %f" % sm_offset)
            self._log.debug("lambda: %f" % wave_length)
            self._log.debug("theta: %f" % (theta * 180 / math.pi))
            self._log.debug("beta: %f" % (beta * 180 / math.pi))
            self._log.debug("alpha: %f" % (alpha * 180 / math.pi))
            self._log.debug("(sm_selected, gr_selected, gr-pitch (rad),gr-pitch (deg), gr_pitch (microrad): %d %d %f %f %f" % (sm_selected, gr_selected, gr_pitch, gr_pitch * 180 / math.pi, gr_pitch * 1.0e6))
            self._log.debug("-------------------------------------------------------> calc_physical")

            gr_pitch = gr_pitch * 1.0e6 #rads -> microrads

            #apply the corresponding grating offset
            return (gr_pitch - self.grating_offsets[gr_selected][sm_selected])
        else:
            raise RuntimeError("Invalid index %s to compute energy %s calc_physical()" % (str(index), str(pseudo_pos)))


    def calc_pseudo(self,index,physical_pos):
        """Given the physical motor positions, it computes the energy pseudomotor.
        @param[in] index: (expected always 1, since we provide only 1 pseudo motor)
        @param[in] physical_pos: physical positions of all the motors involved in the computation
        @return the energy pseudo motor value
        @throws exception
        """

        try:
            sm_selected = self.sm_selected_ior_dev.read_attribute("value").value
            gr_selected = self.gr_selected_ior_dev.read_attribute("value").value
            gr_pitch = physical_pos[0]
        except Exception, e:
            raise RuntimeError("Spherical mirror and/or grating positions are invalid: %s" % repr(e))

        sm_offset = Energy.sm_offset[sm_selected]

        #compute energy
        D0 = Energy.line_spacing[gr_selected] * 1.0e-6
        #apply the user supplied grating offset depending on the GR and SM
        #selected and convert it from micro radians to radians
        gr_pitch += self.grating_offsets[gr_selected][sm_selected]
        gr_pitch = gr_pitch * 1e-6

        alpha = math.pi/2 - sm_offset - gr_pitch
        theta = Energy.include_angles[sm_selected]
        beta = alpha - theta

        wave_length =  ( math.sin(alpha) + math.sin(beta) ) / D0

        energy = Energy.constant / wave_length #will throw exception if wave_length == 0

        self._log.debug("<------------------------------------------------------- calc_pseudo")
        self._log.debug("sm_offset %f" % sm_offset)
        self._log.debug("physical_pos: %f" % physical_pos)
        self._log.debug("sm_selected, gr_selected: %d %d" % (sm_selected, gr_selected))
        self._log.debug("alpha (deg): %f" % (alpha * 180 / math.pi))
        self._log.debug("theta (deg): %f" % (theta * 180 / math.pi))
        self._log.debug("beta (deg): %f" % (beta * 180 / math.pi))
        self._log.debug("lambda: %f" % wave_length)
        self._log.debug("energy: %f" % energy)
        self._log.debug("-------------------------------------------------------> calc_pseudo")

        return energy


    def GetExtraAttributePar(self,axis,name):
        """ Get extra attribute parameters.
        @param axis to get the parameter
        @param name of the parameter to retrieve
        @return the value of the parameter
        """
        if name == 'lock_mirrors':
            return self.lock_mirrors
        elif name == 'heg_sm2_offset':
            return self.heg_sm2_offset
        elif name == 'heg_sm1_offset':
            return self.heg_sm1_offset
        elif name == 'meg_sm2_offset':
            return self.meg_sm2_offset
        elif name == 'meg_sm1_offset':
            return self.meg_sm1_offset
        elif name == 'leg_sm2_offset':
            return self.leg_sm2_offset
        elif name == 'leg_sm1_offset':
            return self.leg_sm1_offset
        elif name == 'ranges':
            return self.ranges
        elif name == 'debug':
            return self.debug


    def SetExtraAttributePar(self,axis,name,value):
        """ Set extra attribute parameters.
        @param axis to set the parameter
        @param name of the parameter to set
        @param value to be set
        """
        if name == 'lock_mirrors':
            self.lock_mirrors = value
        elif name == 'heg_sm2_offset':
            self.heg_sm2_offset = value
            self.grating_offsets[0][0] = value
        elif name == 'heg_sm1_offset':
            self.heg_sm1_offset = value
            self.grating_offsets[0][1] = value
        elif name == 'meg_sm2_offset':
            self.meg_sm2_offset = value
            self.grating_offsets[1][0] = value
        elif name == 'meg_sm1_offset':
            self.meg_sm1_offset = value
            self.grating_offsets[1][1] = value
        elif name == 'leg_sm2_offset':
            self.leg_sm2_offset = value
            self.grating_offsets[2][0] = value
        elif name == 'leg_sm1_offset':
            self.leg_sm1_offset = value
            self.grating_offsets[2][1] = value
        elif name == 'debug':
            self.debug = value
            if self.debug:
                #put logger in debug mode
                self._log.setLevel(logging.DEBUG)
            else:
                #restore original logger level
                self._log.setLevel(self.log_level_original)
