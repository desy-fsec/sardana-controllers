class Energy(PseudoMotorController):
    """Energy pseudo motor controller for handling XMCD energy calculation given the positions
    of all the physical motor involved (and viceversa)."""

    gender = "Energy"
    model  = "BL29(XMCD) energy calculation"
    organization = "CELLS - ALBA"
    image = "energy.png"
    logo = "ALBA_logo.png"

    pseudo_motor_roles = ("Energy",)
    motor_roles = ("sm2", "sm1", "pgm", "pgm-pitch")

    constant = 1240 #units in mm*eV
    include_angles = [  177*math.pi/180, 175*math.pi/180, ] #angles in radians (sm2 - sm1 respectively)
    energy_ranges = [ [ (250, 500), (80,300) ],
                      [ (1300,3000), (350,1500) ],
                      [ (2000,4000), (600,1200) ]
                    ] #energy in eV (electron volts)
    line_spacing = [ 200.0/1000000.0, 800.0/1000000.0, 1200.0/1000000.0 ] #line spacing in lines/mm

    def calc_physical(self,index,pseudo_pos):
        """Given the motor number (sm2, sm1, pgm, pgm-pitch) and the desired energy it
        returns the correct motor position for that motor and energy.
        @param[in] motor number and desired energy
        @return the correct motor position
        @throws exception
        """
        #lookup energy in table and select corresponding sm and pgm index
        energy = pseudo_pos[0]
        range_found = False
        for i in range(3):
            for j in range(2):
                if (energy >= Energy.energy_ranges[i][j][0] and energy <= Energy.energy_ranges[i][j][1]):
                    sm = j
                    pgm = i
                    range_found = True
                    break
            if range_found:
                break
        else:
            raise RuntimeError("Energy %s out of range calc_physical()" % str(energy))
        if index == 1:
            return ((sm+1) % 2) * 100
        elif index == 2:
            return 100
        elif index == 3:
            return pgm * 100
        elif index == 4:
            wave_length = Energy.constant / energy
            theta = Energy.include_angles[sm]
            tg_alpha = math.sin(theta) / ( 1.0 + math.cos(theta) - (Energy.line_spacing[i] * 1.0 * wave_length) )
            return ( math.pi/2 - math.atan(tg_alpha) )
        else:
            raise RuntimeError("Invalid energy %s calc_physical()" % str(energy))

    def calc_pseudo(self,index,physical_pos):
        """Given the physical motor positions, it computes the energy pseudomotor.
        @param[in] index (expected always 1, since only 1 pseudo motor)
        @return the energy pseudo motor value
        @throws exception
        """
        #find out which spherical mirror is selected
        print 40*"/"
        print "physical_pos:", physical_pos
        if (physical_pos[0] >= 100): 
            sm = 0
        else:
            sm = 1
        #find out which plane grating mirror is selected
        pgm_pos = physical_pos[2]
        if (pgm_pos >= 0 and pgm_pos<100):
            pgm = 0
        elif (pgm_pos >= 100 and pgm_pos<200):
            pgm = 1
        else:
            pgm = 2
        #compute energy
        pgm_pitch = physical_pos[3]
        alpha = math.pi/2 - pgm_pitch
        beta = Energy.include_angles[sm] - alpha
        print "( math.sin(alpha) - math.sin(beta) ):", ( math.sin(alpha) - math.sin(beta) )
        print "Energy.line_spacing[pgm]:", Energy.line_spacing[pgm]
        wave_length =  ( math.sin(alpha) + math.sin(-1.0*beta) ) / Energy.line_spacing[pgm]
        print "alpha:", (alpha * 180.0 / math.pi) , "beta:", (beta * 180.0 /math.pi)
        print "alpha:", alpha, "beta:", beta, "wave_length:", wave_length
        energy = Energy.constant / wave_length #throw exception if wave_length = 0
        print "energy:", energy
        return energy

    def calc_all_physical(self, pseudo_pos):
        """Calculates the positions of all motors that belong to the pseudo 
           motor system given the positions of the pseudo motor.
        @param[in] pseudo_pos. Array of only 1 value (the desired energy)
        @return the correct position for the physical motors that will give the desired energy
        @throws exception
        """
        #lookup energy in table and select corresponding sm and pgm index
        energy = pseudo_pos[0]
        range_found = False
        for i in range(3):
            for j in range(2):
                if (energy >= Energy.energy_ranges[i][j][0] and energy <= Energy.energy_ranges[i][j][1]):
                    sm = j
                    pgm = i
                    range_found = True
                    break
            if range_found:
                break
        else:
            raise RuntimeError("Energy %s out of range calc_all_physical()" % str(energy))
        print 40 * "*"
        wave_length = Energy.constant / energy
        print "energy:", energy
        print "wave_length:", wave_length
        theta = Energy.include_angles[sm]
        print "theta", theta, theta*180.0 / math.pi
        tg_alpha = math.sin(theta) / ( 1.0 + math.cos(theta) - (Energy.line_spacing[i] * 1.0 * wave_length) )
        print "tg_alpha", tg_alpha
        print "alpha", math.atan(tg_alpha), math.atan(tg_alpha) * 180 / math.pi 
        return ( ((sm+1) % 2) * 100, 100, pgm * 100, (math.pi/2 - math.atan(tg_alpha)) )
