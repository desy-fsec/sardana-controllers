import math
import taurus

#from pool import PseudoMotorController
#from pool import PoolUtil
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController

class VFMBenderBackPMController(PseudoMotorController):

    pseudo_motor_roles = ('vfmbenfb_N',)
    motor_roles = ('vfmbenb_hstp',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        vfmbenfb_N, = pseudos
        vfmbenb_hstp = self.vfmbenb_conversion('hs', vfmbenfb_N)
        return vfmbenb_hstp

    def CalcPseudo(self, index, physicals, curr_pseudos):
        vfmbenb_hstp, = physicals
        vfmbenfb_N = self.vfmbenb_conversion('N', vfmbenb_hstp)
        return vfmbenfb_N

    ###################################################################################
    # Code developed by jjuanhuix                                                     #
    ###################################################################################
    def vfmbenb_conversion(self, request, force):                                     #
        """vfmbenb_conversion(request, force)                                         #
        Gives Conversion between force and half steps for vfm bender BACK             #
        mode = 'N' Converts hs->N                                                     #
        mode = 'hs' Converts N->hs                                                    #
        CURRENTLY 31.1.2012: vfmbenb(hs): 6305 - vfmstrnb.value: 153.5                #
        """                                                                           #
        slope = 121.765		 	# hsteps/N - JNicolas                         #
        offset = 6305-slope*153.5 	#hs                                           #
                                                                                      #
        if request == 'hs':                                                           #
            force_max = 300		# lim max in N                                #
            force_min = 0		# lim min in N                                #
            force_hs = slope*force + offset                                           #
            if force<force_min or force>force_max:                                    #
                #return(-1)                                                           #
                raise Exception('Force out of range')                                 #
            return(force_hs)                                                          #
                                                                                      #
        elif request == 'N':                                                          #
            force_max = 1E6	        # lim max in hs                               #
            force_min = -1E6	        # lim min in hs                               #
            force_N = (force-offset)/slope                                            #
            if force<force_min or force>force_max:                                    #
                #return(-1)                                                           #
                raise Exception('Force out of range')                                 #
            return(force_N)                                                           #
                                                                                      #
        else:                                                                         #
            raise Exception('Invalid request')                                        #
    ###################################################################################


class VFMBenderFrontPMController(PseudoMotorController):

    pseudo_motor_roles = ('vfmbenff_N',)
    motor_roles = ('vfmbenf_hstp',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        vfmbenff_N, = pseudos
        vfmbenf_hstp = self.vfmbenf_conversion('hs', vfmbenff_N)
        return vfmbenf_hstp

    def CalcPseudo(self, index, physicals, curr_pseudos):
        vfmbenf_hstp, = physicals
        vfmbenff_N = self.vfmbenf_conversion('N', vfmbenf_hstp)
        return vfmbenff_N

    ###################################################################################
    # Code developed by jjuanhuix                                                     #
    ###################################################################################
    def vfmbenf_conversion(self, request, force):                                     #
        """vfmbenf_conversion(request, force)                                         #
        Gives Conversion between force and half steps for vfm bender FRONT            #
        mode = 'N' Converts hs->N                                                     #
        mode = 'hs' Converts N->hs                                                    #
        CURRENTLY 31.1.2012: vfmbenf(hs): -2518 - vfmstrnf.value: 154.7               #
        """                                                                           #
        slope = 158.203		 	# hsteps/N - JNicolas                         #
        offset = -2518-slope*154.7 		#hs                                   #
                                                                                      #
        if request == 'hs':                                                           #
            force_max = 300		# lim max in N                                #
            force_min = 0		# lim min in N                                #
            force_hs = slope*force + offset                                           #
            if force<force_min or force>force_max:                                    #
                #return(-1)                                                           #
                raise Exception('Force out of range')                                 #
            return(force_hs)                                                          #
                                                                                      #
        elif request == 'N':                                                          #
            force_max = 1E6	# lim max in hs                                       #
            force_min = -1E6	# lim min in hs                                       #
            force_N = (force-offset)/slope                                            #
            if force<force_min or force>force_max:                                    #
                #return(-1)                                                           #
                raise Exception('Force out of range')                                 #
            return(force_N)                                                           #
                                                                                      #
        else:                                                                         #
            raise Exception('Invalid request')                                        #
    ###################################################################################



class VFMBenderEllipsePMController(PseudoMotorController):
    """ Pseudomotor controller to allow bending the mirror with q and DE3"""

    pseudo_motor_roles = ('q', 'DE3',)
    motor_roles = ('vfmbenfb_N', 'vfmbenff_N',)

    axis_attributes = {'vfm_ellipse_p': {'Type':'PyTango.DevDouble',
                                         'R/W Type':'PyTango.READ_WRITE',
                                         'DefaultValue':22.8},
                       'vfm_ellipse_pit_offset': {'Type':'PyTango.DevDouble',
                                                  'R/W Type':'PyTango.READ_WRITE',
                                                  'DefaultValue':0}
                       }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.vfm_ellipse_p = 22.8
        self.vfm_ellipse_pit_offset = 0

    def CalcPhysical(self, index, pseudos, curr_physicals):
        return self.CalcAllPhysical(pseudos, curr_physicals)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physicals):
        q, DE3 = pseudos
        incidenceangle = taurus.Attribute('vfmpit/Position').read().value + self.vfm_ellipse_pit_offset
        E2, E3 = self.vfmoptic_conversion('Elipse', q, DE3, incidenceangle, self.vfm_ellipse_p)
        FU, FD = self.vfmelipse_conversion('Force', E2, E3)
        vfmbenfb_N, vfmbenff_N = FU, FD
        return vfmbenfb_N, vfmbenff_N

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return self.CalcAllPseudo(physicals, curr_pseudos)[index - 1]

    def CalcAllPseudo(self, physicals, curr_pseudos):
        vfmbenfb_N, vfmbenff_N = physicals
        FU, FD = vfmbenfb_N, vfmbenff_N
        E2, E3 = self.vfmelipse_conversion('Elipse', FU, FD)
        incidenceangle = taurus.Attribute('vfmpit/Position').read().value + self.vfm_ellipse_pit_offset
        q, DE3 = self.vfmoptic_conversion('Optics', E2, E3, incidenceangle, self.vfm_ellipse_p)
        return q, DE3

    def SetAxisExtraPar(self, axis, name, value):
        if name.lower() == 'vfm_ellipse_p':
            self.vfm_ellipse_p = value
        if name.lower() == 'vfm_ellipse_pit_offset':
            self.vfm_ellipse_pit_offset = value

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == 'vfm_ellipse_p':
            return self.vfm_ellipse_p
        if name.lower() == 'vfm_ellipse_pit_offset':
            return self.vfm_ellipse_pit_offset


    #########################################################################################
    # Code developed by jjuanhuix                                                           #
    #########################################################################################
    def vfmelipse_conversion(self, request, parb, parf):                                    #
        """vfmelipse_conversion(request, parb, parf)                                        #
        Gives Conversion between forces in N and elipse paramters for vfm                   #
        request = 'Force' Converts Elipse parameters E2, E3 -> Forces [N]                   #
        request = 'Elipse' Converts Forces [N] -> Elipse parameters E2, E3                  #
        parb = FU OR E2                                                                     #
        parf = FD OR E3                                                                     #
        Elipse is described by h(x) = E2 x**2 + E3 x**3                                     #
        """                                                                                 #
        # U = Upstream   = Back (parb)                                                      #
        # D = Downstream = Front (parf)                                                     #
        E20 = 1.9817931531E-5                                                               #
        E2U = 5.3352884441E-7                                                               #
        E2D = 6.8795635423E-7                                                               #
        E30 = -1.0720120935E-5                                                              #
        E3U = -9.5879551897E-7                                                              #
        E3D = 1.2533444067E-6                                                               #
        FU_NOM = 170.558                                                                    #
        FD_NOM = 130.277                                                                    #
                                                                                            #
        if request == 'Elipse':                                                             #
            FU = parb                                                                       #
            FD = parf                                                                       #
            E2 = E20 + E2U*FU + E2D*FD                                                      #
            E3 = E30 + E3U*FU + E3D*FD                                                      #
            return(E2, E3)                                                                  #
                                                                                            #
        elif request == 'Force':                                                            #
            E2 = parb                                                                       #
            E3 = parf                                                                       #
            FU = (E3-E30-E3D*E2/E2D+E3D*E20/E2D)/(E3U-E2U*E3D/E2D)                          #
            FD = (E2-E20-E2U*FU)/E2D                                                        #
            return(FU, FD)                                                                  #
                                                                                            #
    def vfmoptic_conversion(self, request, par1, par2, incidenceangle, p):                  #
        """vfmoptic_conversion(request, parb, parf)                                         #
        Gives Conversion between elipse parameters and optical paramters for vfm            #
        request = 'Optics' Converts Elipse parameters E2, E3 -> Optical parameters q, DE3   #
        request = 'Elipse' Converts Optical parameters q, DE3 -> Elipse parameters E2, E3   #
        par1 = q OR E2                                                                      #
        par2 = DE3 OR E3                                                                    #
        incidenceangle = incidence angle angle to vfm in mrad with respect to surface       #
        p = distance source to mirror in m                                                  #
        Elipse is described by h(x) = E2 x**2 + E3 x**3                                     #
        """                                                                                 #
        # U = Upstream   = Back (parb)                                                      #
        # D = Downstream = Front (parf)                                                     #
        import math as m                                                                    #
        alpha = m.pi/2. - incidenceangle/1000                                               #
                                                                                            #
        if request == 'Elipse':                                                             #
            q   = par1                                                                      #
            DE3 = par2                                                                      #
            E2 = (1./p + 1./q)*m.cos(alpha)/4.                                              #
            E3 = (1.+DE3)*(1./p/p - 1./q/q)*m.sin(2.*alpha)/16.                             #
            return(E2, E3)                                                                  #
                                                                                            #
        elif request == 'Optics':                                                           #
            E2 = par1                                                                       #
            E3 = par2                                                                       #
            q = 1./(4.*E2/m.cos(alpha) - 1./p)                                              #
            DE3 = 16.*E3/m.sin(2*alpha)/(1./p/p-1./q/q) - 1.                                #
            return(q, DE3)                                                                  #
    #########################################################################################


class HFMBenderBackPMController(PseudoMotorController):

    pseudo_motor_roles = ('hfmbenfb_N',)
    motor_roles = ('hfmbenb_hstp',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        hfmbenfb_N, = pseudos
        hfmbenb_hstp = self.hfmbenb_conversion('hs', hfmbenfb_N)
        return hfmbenb_hstp

    def CalcPseudo(self, index, physicals, curr_pseudos):
        hfmbenb_hstp, = physicals
        hfmbenfb_N = self.hfmbenb_conversion('N', hfmbenb_hstp)
        return hfmbenfb_N

    ###################################################################################
    # Code developed by jjuanhuix                                                     #
    ###################################################################################
    def hfmbenb_conversion(self, request, force):                                     #
        """hfmbenb_conversion(request, force)                                         #
        Gives Conversion between force and half steps for vfm bender BACK             #
        mode = 'N' Converts hs->N                                                     #
        mode = 'hs' Converts N->hs                                                    #
        CURRENTLY 13.2.2012: hfmbenb(hs): 40426 - hfmstrnb.value: 201.95              #
        """                                                                           #
        slope = 405.500		 	# hsteps/N - JNicolas                         #
        offset = 40426-slope*201.95 		#hs                                   #
                                                                                      #
        if request == 'hs':                                                           #
            force_max = 300	               	# lim max in N                        #
            force_min = 0		        # lim min in N                        #
            force_hs = slope*force + offset                                           #
            if force<force_min or force>force_max:                                    #
                #return(-1)                                                           #
                raise Exception('Force out of range')                                 #
            return(force_hs)                                                          #
                                                                                      #
        elif request == 'N':                                                          #
            force_max = 1E6		        # lim max in hs                       #
            force_min = -1E6	        # lim min in hs                               #
            force_N = (force-offset)/slope                                            #
            if force<force_min or force>force_max:                                    #
                #return(-1)                                                           #
                raise Exception('Force out of range')                                 #
            return(force_N)                                                           #
        else:                                                                         #
            raise Exception('Invalid request')                                        #
    ###################################################################################


class HFMBenderFrontPMController(PseudoMotorController):

    pseudo_motor_roles = ('hfmbenff_N',)
    motor_roles = ('hfmbenf_hstp',)

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        hfmbenff_N, = pseudos
        hfmbenf_hstp = self.hfmbenf_conversion('hs', hfmbenff_N)
        return hfmbenf_hstp

    def CalcPseudo(self, index, physicals, curr_pseudos):
        hfmbenf_hstp, = physicals
        hfmbenff_N = self.hfmbenf_conversion('N', hfmbenf_hstp)
        return hfmbenff_N

    ###################################################################################
    # Code developed by jjuanhuix                                                     #
    ###################################################################################
    def hfmbenf_conversion(self, request, force):                                     #
        """hfmbenf_conversion(request, force)                                         #
        Gives Conversion between force and half steps for vfm bender FRONT            #
        mode = 'N' Converts hs->N                                                     #
        mode = 'hs' Converts N->hs                                                    #
        CURRENTLY 13.2.2012: vfmbenf(hs): 42999 - vfmstrnf.value: 201.52              #
        """                                                                           #
        slope = 801.498		 	# hsteps/N - JNicolas                         #
        offset = 42999-slope*201.52 		#hs                                   #
                                                                                      #
        if request == 'hs':                                                           #
            force_max = 300		        # lim max in N                        #
            force_min = 0		        # lim min in N                        #
            force_hs = slope*force + offset                                           #
            if force<force_min or force>force_max:                                    #
                return(-1)                                                            #
            return(force_hs)                                                          #
                                                                                      #
        elif request == 'N':                                                          #
            force_max = 1E6		        # lim max in hs                       #
            force_min = -1E6	        # lim min in hs                               #
            force_N = (force-offset)/slope                                            #
            if force<force_min or force>force_max:                                    #
                return(-1)                                                            #
            return(force_N)                                                           #
        else:                                                                         #
            raise Exception('Invalid request')                                        #
    ###################################################################################



class HFMBenderEllipsePMController(PseudoMotorController):

    pseudo_motor_roles = ('q', 'DE3')
    motor_roles = ('hfmbenfb_N', 'hfmbenff_N')

    axis_attributes = {'hfm_ellipse_p':
                           {'Type':'PyTango.DevDouble',
                            'R/W Type':'PyTango.READ_WRITE',
                            'DefaultValue':24.78},
                       'hfm_ellipse_pit_offset':
                           {'Type':'PyTango.DevDouble',
                            'R/W Type':'PyTango.READ_WRITE',
                            'DefaultValue':0}}

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self.hfm_ellipse_p = 24.78
        self.hfm_ellipse_pit_offset = 0.0

    def CalcPhysical(self, index, pseudos, curr_physicals):
        return self.CalcAllPhysical(pseudos, curr_physicals)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physicals):
        q, DE3 = pseudos
        incidenceangle = taurus.Attribute('hfmpit/Position').read().value + self.hfm_ellipse_pit_offset
        E2, E3 = self.hfmoptic_conversion('Elipse', q, DE3, incidenceangle, self.hfm_ellipse_p)
        FU, FD = self.hfmelipse_conversion('Force', E2, E3)
        hfmbenfb_N, hfmbenff_N = FU, FD
        return hfmbenfb_N, hfmbenff_N

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return self.CalcAllPseudo(physicals, curr_pseudos)[index - 1]

    def CalcAllPseudo(self, physicals, curr_pseudos):
        hfmbenfb_N, hfmbenff_N = physicals
        FU, FD = hfmbenfb_N, hfmbenff_N
        E2, E3 = self.hfmelipse_conversion('Elipse', FU, FD)
        incidenceangle = taurus.Attribute('hfmpit/Position').read().value + self.hfm_ellipse_pit_offset
        q, DE3 = self.hfmoptic_conversion('Optics', E2, E3, incidenceangle, self.hfm_ellipse_p)
        return q, DE3

    def SetAxisExtraPar(self, axis, name, value):
        if name.lower() == 'hfm_ellipse_p':
            self.hfm_ellipse_p = value
        if name.lower() == 'hfm_ellipse_pit_offset':
            self.hfm_ellipse_pit_offset = value

    def GetAxisExtraPar(self, axis, name):
        if name.lower() == 'hfm_ellipse_p':
            return self.hfm_ellipse_p
        if name.lower() == 'hfm_ellipse_pit_offset':
            return self.hfm_ellipse_pit_offset


    #########################################################################################
    # Code developed by jjuanhuix                                                           #
    #########################################################################################
    def hfmelipse_conversion(self, request, parb, parf):                                    #
        """hfmelipse_conversion(request, parb, parf)                                        #
        Gives Conversion between forces in N and elipse paramters for hfm                   #
        request = 'Force' Converts Elipse parameters E2, E3 -> Forces [N]                   #
        request = 'Elipse' Converts Forces [N] -> Elipse parameters E2, E3                  #
        parb = FU OR E2                                                                     #
        parf = FD OR E3                                                                     #
        Elipse is described by h(x) = E2 x**2 + E3 x**3                                     #
        """                                                                                 #
        # U = Upstream   = Back (parb)                                                      #
        # D = Downstream = Front (parf)                                                     #
        E20 = -2.383657E-5                                                                  #
        E2U = 5.378920E-7                                                                   #
        E2D = 5.984089E-7                                                                   #
        E30 = -1.120740E-6                                                                  #
        E3U = -5.877415E-7                                                                  #
        E3D = 6.094811E-7                                                                   #
        FU_NOM = 278.4522                                                                   #
        FD_NOM = 231.8139                                                                   #
                                                                                            #
        if request == 'Elipse':                                                             #
            FU = parb                                                                       #
            FD = parf                                                                       #
            E2 = E20 + E2U*FU + E2D*FD                                                      #
            E3 = E30 + E3U*FU + E3D*FD                                                      #
            return(E2, E3)                                                                  #
                                                                                            #
        elif request == 'Force':                                                            #
            E2 = parb                                                                       #
            E3 = parf                                                                       #
            FU = (E3-E30-E3D*E2/E2D+E3D*E20/E2D)/(E3U-E2U*E3D/E2D)                          #
            FD = (E2-E20-E2U*FU)/E2D                                                        #
            return(FU, FD)                                                                  #
                                                                                            #
    def hfmoptic_conversion(self, request, par1, par2, incidenceangle, p):                  #
        """hfmoptic_conversion(request, parb, parf)                                         #
        Gives Conversion between elipse parameters and optical paramters for hfm            #
        request = 'Optics' Converts Elipse parameters E2, E3 -> Optical parameters q, DE3   #
        request = 'Elipse' Converts Optical parameters q, DE3 -> Elipse parameters E2, E3   #
        par1 = q OR E2                                                                      #
        par2 = DE3 OR E3                                                                    #
        incidenceangle = incidence angle angle to hfm in mrad with respect to surface       #
        p = distance source to mirror in m                                                  #
        Elipse is described by h(x) = E2 x**2 + E3 x**3                                     #
        """                                                                                 #
        # U = Upstream   = Back (parb)                                                      #
        # D = Downstream = Front (parf)                                                     #
        import math as m                                                                    #
        alpha = m.pi/2. - incidenceangle/1000                                               #
                                                                                            #
        if request == 'Elipse':                                                             #
            q   = par1                                                                      #
            DE3 = par2                                                                      #
            E2 = (1./p + 1./q)*m.cos(alpha)/4.                                              #
            E3 = (1.+DE3)*(1./p/p - 1./q/q)*m.sin(2.*alpha)/16.                             #
            return(E2, E3)                                                                  #
                                                                                            #
        elif request == 'Optics':                                                           #
            E2 = par1                                                                       #
            E3 = par2                                                                       #
            q = 1./(4.*E2/m.cos(alpha) - 1./p)                                              #
            DE3 = 16.*E3/m.sin(2*alpha)/(1./p/p-1./q/q) - 1.                                #
            return(q, DE3)                                                                  #
    #########################################################################################



if __name__ == '__main__':

    pass
    ### # CODE MIGRATED TO NEW PYPOOL AND MAIN NOT UPDATED
    ### print '\n\nVFMBENB tests'
    ### vfmbenb_ctrl = VFMBenderBackPMController('a_name', {})
    ### vfmbenb_tests = [(6305, 153.5), (1234, 111.8542), (-8765.43, 29.7334)]
    ### for test in vfmbenb_tests:
    ###     physical, pseudo = test
    ### 
    ###     calc_pseudo = vfmbenb_ctrl.calc_pseudo(1, [physical])
    ###     calc_physical = vfmbenb_ctrl.calc_physical(1, [pseudo])
    ### 
    ###     print '\n',test,'->',physical,',',calc_pseudo,',',pseudo,',',calc_physical
    ### 
    ### print '\n\nVFMBENF tests'
    ### vfmbenf_ctrl = VFMBenderFrontPMController('a_name', {})
    ### vfmbenf_tests = [(-2518, 154.7), (1234, 178.4163), (-8765.43, 115.2100)]
    ### for test in vfmbenf_tests:
    ###     physical, pseudo = test
    ### 
    ###     calc_pseudo = vfmbenf_ctrl.calc_pseudo(1, [physical])
    ###     calc_physical = vfmbenf_ctrl.calc_physical(1, [pseudo])
    ### 
    ###     print '\n',test,'->',physical,',',calc_pseudo,',',pseudo,',',calc_physical
    ### 
    ### print '\n\nVFM-ELLIPSE tests'
    ### vfmellipse_ctrl = VFMBenderEllipsePMController('a_name', {})
    ### physicals = 170.558, 130.277
    ### pseudos = vfmellipse_ctrl.calc_all_pseudos(physicals)
    ### calculated_physicals = vfmellipse_ctrl.calc_all_physicals(pseudos)
    ### print physicals
    ### print pseudos
    ### print calculated_physicals
