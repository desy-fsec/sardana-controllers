#!/usr/bin/env python
#############################################################################
##
## file :    AlbaB1KbPseudomotors.py
##
## description : 
##
## project :    Sardana/Pool/ctrls/PseudoMotors
##
## developers history: sblanch
##
## copyleft :    Cells / Alba Synchrotron
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Sardana.
##
## This is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This software is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################
import logging, math
import PyTango

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController
from taurus.core.util import SafeEvaluator

class KbPseudoMotorController(PseudoMotorController):
    """Kb motor 
    """
    class_prop = {'wedge' : {'Type' : 'PyTango.DevDouble', 'Description' : 'Wedge of the mirror (mrad)'},
                  'L' : {'Type' : 'PyTango.DevDouble', 'Description' : 'L (mm)'},
                  'alpha' : {'Type' : 'PyTango.DevDouble', 'Description' : 'Alpha (mrad)'}}

    pseudo_motor_roles = ("kb_trans", "kb_pitch")
    motor_roles = ("kb_t","kb_r")
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        #self._log.setLevel(logging.DEBUG)

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        kb_trans,kb_pitch = pseudos #mm,mrad
        alpha_rad = self.alpha/1000
        kb_t = math.acos(kb_trans/self.L + math.cos(alpha_rad)) * 1000 - self.alpha
        kb_r = kb_pitch - self.wedge - kb_t
        #self._log.error('***********kb_t: %f' % kb_t)
        #self._log.error('***********kb_r: %f' % kb_r)
        return (kb_t,kb_r)

    def calc_all_pseudo(self, physicals):
        kb_t, kb_r = physicals #mrad,mrad
        kb_pitch = kb_r + kb_t + self.wedge
        alpha_rad = self.alpha/1000
        kb_t_rad = kb_t/1000
        kb_trans = self.L * (math.cos(alpha_rad + kb_t_rad) - math.cos(alpha_rad))        
        #self._log.error('***********kb_trans: %f' % kb_trans)
        #self._log.error('***********kb_pitch: %f' % kb_pitch)
        return (kb_trans,kb_pitch)


class KbBendPseudoMotorController(PseudoMotorController):
    """Pseudomotor controller class to calculate focus distance(q) and aberration(dE3) of the KB mirror bending.
       It is based on two physical motors: downstream bending actuator (kb_b1) and upstream bending actuator (kb_b2).

       Mirror specific parameters for MSPD benders
       M1 p=29900 L=240  alpha is kbm1_pitch ! make sure alpha is positive
       [mUo,Bud,Buu,mDo,Bdd,Bdu] = [39260.1616,-4.343398,35.979069,68697.2575,56.643268,-12.051995]
       [aUo,Aud,Auu,aDo,Add,Adu] = [-1269.8084,0.002191,0.028513,-1482.6348,0.018117,0.006065]
       M2 p=30300 L=240   alpha is kbm1_yaw make sure alpha is positive
       [mUo,Bud,Buu,mDo,Bdd,Bdu] = [48473.8176,-2.192377,30.329456,53145.6088,31.212753,-7.234167]
       [aUo,Aud,Auu,aDo,Add,Adu] = [-1750.5182,0.002347,0.033540,-2109.3250,0.032341,0.008058]
    """
    ctrl_properties = {'p' : {'Type' : float, 'Description' : 'p (mm) source distance'},
                       'L' : {'Type' : float, 'Description' : 'L (mm)'},
                       'kb_pseudorot_motor' : {'Type' : str, 'Description' : 'Incident angle (mrad)'},
                       'bender_parameters' : {'Type' : list, 'Description' : 'Bender parameters in format: [mUo,Bud,Buu,mDo,Bdd,Bdu]'},
                       'bender_parameters_reversed' : {'Type' : list, 'Description' : 'Bender parameters reversed in format: [aUo,Aud,Auu,aDo,Add,Adu]'} }

    pseudo_motor_roles = ("q", "dE3")
    motor_roles = ("kb_b1","kb_b2")
 
    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("p = %f" % self.p)
        self._log.debug("L = %f" % self.L)
        self._log.debug("kb_rot_motor = %s" % self.kb_pseudorot_motor)
        self._log.debug("bender_parameters = %s" % repr(self.bender_parameters))
        self._log.debug("bender_parameters_reverse = %s" % repr(self.bender_parameters_reversed))
        self.kb_rot = PoolUtil.get_device(inst, self.kb_pseudorot_motor)
        #I think it is a bug in sardana, since we explicitly define list type for this ctrl_property
        self.bender_parameters = SafeEvaluator().eval(self.bender_parameters)
        self._log.debug("Length of bender_parameters = %d" % len(self.bender_parameters))
        if len(self.bender_parameters) != 6:
            raise Exception("Controller property bender_parameters list must contains 6 elements.")
        self.mUo,self.Bud,self.Buu,self.mDo,self.Bdd,self.Bdu = self.bender_parameters
        #I think it is a bug in sardana, since we explicitly define list type for this ctrl_property
        self.bender_parameters_reversed = SafeEvaluator().eval(self.bender_parameters_reversed)
        if len(self.bender_parameters_reversed) != 6:
            raise Exception("Controller property bender_parameters_reversed list must contains 6 elements.")
        self.aUo,self.Aud,self.Auu,self.aDo,self.Add,self.Adu = self.bender_parameters_reversed
  
    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        q,dE3 = pseudos
        kb_rot_position = self.kb_rot.position / 1000 #conversion to rad
        self._log.debug("calc_all_physical(): kb_rot_position = %f" % kb_rot_position)
        al = math.pi/2-abs(kb_rot_position)
        E3=(1+dE3)*(1/self.p/self.p-1/q/q)*math.sin(2*al)/16
        E2=(1/self.p+1/q)*math.cos(al)/4
        al1=E2*self.L
        al2=3*E3*self.L*self.L/4
        al_D=al1+al2
        al_U=al1-al2 
        kb_bend_U=self.mUo+self.Bud*1e6*al_D+self.Buu*1e6*al_U
        kb_bend_D=self.mDo+self.Bdd*1e6*al_D+self.Bdu*1e6*al_U

        self._log.debug('calc_all_physical(): kb_bend_U = %f' % kb_bend_U)
        self._log.debug('calc_all_physical(): kb_bend_D = %f' % kb_bend_D)
        return (kb_bend_D,kb_bend_U)

    def calc_all_pseudo(self, physicals):
        kb_bend_D,kb_bend_U = physicals #fstep,fstep
        kb_rot_position = self.kb_rot.position / 1000 #conversion to rad
        self._log.debug("calc_all_physical(): kb_rot_position = %f" % kb_rot_position)
        al = math.pi/2-abs(kb_rot_position)
        aU=self.aUo+self.Aud*kb_bend_D+self.Auu*kb_bend_U
        aD=self.aDo+self.Add*kb_bend_D+self.Adu*kb_bend_U
        E2=1e-6*(aD+aU)/2/self.L
        self._log.debug("calc_all_physical(): E2 = %e" % E2)
        E3=1e-6*2*(aD-aU)/3/self.L/self.L
        self._log.debug("calc_all_physical(): E3 = %e" % E3)
        q=self.p*math.cos(al)/(4*E2*self.p-math.cos(al))
        cot_al = 1/math.tan(al)
        self._log.debug("calc_all_physical(): cot_al = %e" % cot_al)
        dE3=E3*self.p*cot_al/E2/(math.cos(al)-2*E2*self.p)-1

        return (q,dE3)
