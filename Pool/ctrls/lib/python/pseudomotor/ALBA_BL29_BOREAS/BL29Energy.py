#!/usr/bin/env python

import math
import PyTango
from pool import PseudoMotorController


class Energy(PseudoMotorController):
    """Energy pseudo motor controller for handling BL29-Boreas energy calculation given the positions
    of all the motors involved (and viceversa)."""

    gender = "Energy"
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
    offset = [0, 2.0*math.pi/180] #used to set the correct origin of the grating pitch axis (sm2 - sm1 respectively)
    energy_ranges = [ [ (1900,4500), (600,2100) ],
                      [ (950,3000), (380,1700) ],
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
        'R/W Type':'PyTango.READ_WRITE'}
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
        self.debug = False


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
                raise RuntimeError("Energy %s not possible with current mirrors combination. Valid values with"
                                   "current combination is: %s..%s. Unlock mirrors if you want to automatically change them"
                                   % (str(energy), min_value, max_value) )
        else:
        #I'm allowed to change mirrors, so look for the combination of mirrors
        #that can provide that energy (grating and spherical mirrors) and move
        #those motors to that position
            #find which grating and spherical mirrors can give me that energy. If
            #not possible, then raise exception
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

        offset = Energy.offset[sm_selected]

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

            gr_pitch = (math.pi/2 - alpha - offset) #radians

            if self.debug:
                print "<------------------------------------------------------- calc_physical"
                print "offset", offset
                print "lambda", wave_length
                print "theta", theta * 180 / math.pi
                print "beta", beta * 180 / math.pi
                print "alpha", alpha * 180 / math.pi
                print "(sm_selected, gr_selected, gr-pitch (rad),gr-pitch (deg), gr_pitch (microrad)", sm_selected, gr_selected, gr_pitch, gr_pitch * 180 / math.pi, gr_pitch * 1.0e6
                print "-------------------------------------------------------> calc_physical"

            gr_pitch = gr_pitch * 1.0e6 #rads -> microrads

            return gr_pitch
        else:
            raise RuntimeError("Invalid index %s to compute energy %s calc_physical()" % (str(index), str(index)))


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

        offset = Energy.offset[sm_selected]

        #compute energy
        D0 = Energy.line_spacing[gr_selected] * 1.0e-6
        gr_pitch = gr_pitch * 1e-6  #convert from micro radians to radians

        alpha = math.pi/2 - offset - gr_pitch
        theta = Energy.include_angles[sm_selected]
        beta = alpha - theta

        wave_length =  ( math.sin(alpha) + math.sin(beta) ) / D0

        energy = Energy.constant / wave_length #will throw exception if wave_length == 0

        if self.debug:
            print "<------------------------------------------------------- calc_pseudo"
            print "offset", offset
            print "physical_pos:", physical_pos
            print "sm_selected, gr_selected", sm_selected, gr_selected
            print "alpha (deg)", alpha * 180 / math.pi
            print "theta (deg)", theta * 180 / math.pi
            print "beta (deg)", beta * 180 / math.pi
            print "lambda", wave_length
            print "energy", energy
            print "-------------------------------------------------------> calc_pseudo"

        return energy


    def GetExtraAttributePar(self,axis,name):
        """ Get extra attribute parameters.
        @param axis to get the parameter
        @param name of the parameter to retrieve
        @return the value of the parameter
        """
        return self.lock_mirrors


    def SetExtraAttributePar(self,axis,name,value):
        """ Set extra attribute parameters.
        @param axis to set the parameter
        @param name of the parameter to set
        @param value to be set
        """
        self.lock_mirrors = value
