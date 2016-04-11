##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## Author: Marc Rosanes 
##
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

"""This module contains the definition of a linear to rotation pseudo motor 
controller for the Sardana Device Pool"""


__all__ = ["clear"]

__docformat__ = 'restructuredtext'

from sardana import DataAccess
from sardana.pool.controller import PseudoMotorController
from sardana.pool.controller import DefaultValue, Description, Access, Type

import PyTango
import math
   


class EnergyOutController(PseudoMotorController):
    """An EnergyOut pseudomotorController (taking as physical motor the 
       bragg pseudoMotor) for handling Clear Eout pseudomotor."""

    gender = "Eout"
    model  = "Default Eout"
    organization = "Sardana team"

    # theta = bragg
    pseudo_motor_roles = ["Eout"]
    motor_roles = ["bragg"]
    
    # Introduce properties here.
    ctrl_properties = { 'crystalIOR' : { Type : str,
                                     Description  : 'CrystalIOR from which ' + 
                                    'the Eout pseudomotor must infer H,K,L ' + 
                                    'and the lattice spacing a' }, } 
                              #'DefaultValue' : 'ioregister/clearhome_iorctrl/2' 
    
    # Introduce attributes here.
    axis_attributes = {  'n' : { Type : int,
                                 Access : DataAccess.ReadWrite,
                                 Description : 'Order: Energy harmonic.' }, }



    """ Limit angles between 50 and 80 degrees because for smaller angles we
        lose a lot of resolution. At the moment bigger angles of 76 degrees are
        not allowed by the hardware limits of Detector Rotation motor.
        Smaller angles than 43 degrees can occasionate a collision 
        between analyzer and detector.""" 
    
    """d for 25CelsiusDegrees and for a Silicon crystal with 
       miller indices (1,1,1) -> 3.13 nm = 0.5430710/math.sqrt(3)"""
    def __init__(self, inst, props, *args, **kwargs):
       
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("Created CLEAR Eout %s", inst)

        self.hc = 0.00123984193 #[eV*mm]
        self.crystal = PyTango.DeviceProxy(self.crystalIOR)

    # Calculation of input motors values.
    def CalcPhysical(self, index, pseudo_pos, curr_physical_pos):
        """Bragg angle"""

        """ hkl is specific for the crystal. We extract them from the 
            number of ioregister managing the crystal."""
        """ 'a' is specific of the crystal: I have to extract it from 
            the position of the IORegister managing the change of crystal. 
            0.5430710nm is specific for the Silicon and 0.56579nm is specific
            for the Germanium."""
        # if self.crystal.Position == 0: #Silicon crystal
#             self.a = 0.0000005430710 
#             self.h = 1.0
#             self.k = 1.0
#             self.l = 1.0
#         elif self.crystal.Position == 1: #Silicon crystal
#             self.a = 0.0000005430710 
#             self.h = 2.0
#             self.k = 2.0
#             self.l = 0.0
#         elif self.crystal.Position == 2: #Silicon crystal
#             self.a = 0.0000005430710 
#             self.h = 4.0
#             self.k = 0.0
#             self.l = 0.0
#         elif self.crystal.Position == 3: #Germanium crystal
#             self.a = 0.000000565791 
#             self.h = 1.0
#             self.k = 1.0
#             self.l = 1.0

        
        # TODO : Use the real crystal, we use only the Si111 for the moment
        self.a = 0.0000005430710 
        self.h = 1.0
        self.k = 1.0
        self.l = 1.0


        energy = pseudo_pos[0]
        lambdas = self.hc / energy 
        
        sq = (self.h)**2 + (self.k)**2 + (self.l)**2
        sqrt = math.sqrt(sq)
        value = (lambdas * self.n * sqrt)/ (2.0 * self.a)
        if value > 1 or value < -1:
            msg = 'It is not possible to set this energy: %6.2f eV' % energy
            raise Exception(msg)
        theta_rad= math.asin(value) 
        theta = theta_rad * 180.0 / math.pi
        
        bragg = theta
        
        #self._log.debug("CalcPhysical is being executed")
        ret = bragg
        return ret

    # Calculation of output PseudoMotor values.
    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):
        
        """Bragg = Theta: They are given in degrees."""
        """We have: n*lambda=2*d*sin(theta). 
           Where 'd' is the distance between atomic planes.
           We also have: d=a/sqrt(h^2+k^2+l^2) for a cubic crystal. 
           Then: lambda= a*2*sin(theta)/(n*sqrt(h^2+k^2+l^2)).
           'a' is the lattice spacing (of 0.5430710nm in the case of Silicon). 
           'd' is the distance between planes of crystalline structure."""


 #        if self.crystal.Position == 0: #Silicon crystal
#             self.a = 0.0000005430710 
#             self.h = 1
#             self.k = 1
#             self.l = 1
#         elif self.crystal.Position == 1: #Silicon crystal
#             self.a = 0.0000005430710 
#             self.h = 2
#             self.k = 2
#             self.l = 0
#         elif self.crystal.Position == 2: #Silicon crystal
#             self.a = 0.0000005430710 
#             self.h = 4
#             self.k = 0
#             self.l = 0 
#         elif self.crystal.Position == 3: #Germanium crystal
#             self.a = 0.000000565791 
#             self.h = 1
#             self.k = 1
#             self.l = 1

        self.a = 0.0000005430710 
        self.h = 1.0
        self.k = 1.0
        self.l = 1.0

        bragg = physical_pos[0]
        theta = bragg #theta is in degrees here.

        theta_rad = theta*math.pi/180.0 #theta_rad is theta in radians.
        denominator = self.n*math.sqrt((self.h)**2 + (self.k)**2 + (self.l)**2)
        lambdas = 2 * self.a * math.sin(theta_rad) / denominator
        ener_out = self.hc/lambdas

        #self._log.debug("CalcPseudo is being executed")
        ret = ener_out
        return ret

    # Introduce here attribute setter.
    def SetAxisExtraPar(self, axis, parameter, value):
        if (parameter == 'n'):
            self.n = value

    # Introduce here attribute getter.
    def GetAxisExtraPar(self, axis, parameter):
        if (parameter == 'n'):
            return self.n
        else:
            return 1







 
class LinearRotController(PseudoMotorController):
    """A LinearRotController pseudoMotorController for handling the 'atheta' 
       rotation pseudomotor. The system uses the real motor 'azlin' , which is
       the linear motor of the Clear Analyzer allowing the rotation."""

    gender = "Linear2RotController"
    model  = "Default Linear2RotController"
    organization = "Sardana team"
    
    pseudo_motor_roles = "atheta",
    motor_roles = "azlin",


    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("Created LinearRotController %s", inst)


    def CalcPhysical(self, index, pseudo_pos, curr_physical_pos):
         
        #angular offsets deduced with Jon help: 57.5902 and 72.22. 
        value_for_tangent = ((pseudo_pos[0]-57.5902) * math.pi / 180.0)
        azlin = 155.0 * math.tan(value_for_tangent) - 72.22 
        ret = azlin
        
        #self._log.debug("LinearRot.CalcPhysical")
        return ret
    

    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):

        """ atheta = Psi_center + 180.0/math.pi * math.atan(value)
            with:
            value: (delta + physical_pos[0])/155.0) """

        """ 155.0: distance (in mm) between center of analyzer platform and the 
            pivot of the arm that allows the platform rotation: Given by 
            Llibert.     
  
            Psi_center = 57.5902 (given by Jon: angle of analyzer when arm 
            giving rotation of analyzer is in the Y axis).

            delta = 72.22 (given by Jon: linear offset in Z direction in mm 
            between Y axis and arm). """
         
        value = ((72.22 + physical_pos[0])/155.0)
        atheta = 57.5902 + 180.0/math.pi * math.atan(value) 
        ret = atheta

        #self._log.debug("LinearRot.CalcPseudo")
        return ret




class BenderController(PseudoMotorController):
    """
    The bender controller is the reposible to conver from the RC to angle. 
    """
    
    gender = "bender"
    model  = "Default bragg"
    organization = "Sardana team"
    
    # theta = bragg
    pseudo_motor_roles = ["bender"]
    motor_roles = ["motor_up", "motor_down"]
    
    # Introduce controller properties here.
    ctrl_properties = {}
                                                                            
    # Introduce attributes in here.
    axis_attributes = {}

    dm = 80.0 # Distance between motor in mm
    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        rs = pseudo_pos[0]
        #angle = (math.asin(40/rc)) * 180/math.pi
 
        #Angle of the motor in degree
        angle = (math.atan(self.dm/(2*rs))) * 180/math.pi
        return [angle, angle]

       
        
    # Calculation of output PseudoMotor values.
    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):
        # use bender up as reference for the calculation
        angle = physical_pos[0]
        #rc = 40/math.sin((angle * math.pi/180))
        #Sagital Radius in mm
        rs = self.dm/(2*math.tan((max(angle, 0.0001) * math.pi / 180)))
        return rs 


    
class BraggController(PseudoMotorController):
    """A bragg pseudo motor controller for handling Clear theta pseudomotor."""
    """bragg=theta """

    gender = "bragg"
    model  = "Default bragg"
    organization = "Sardana team"
    
    # theta = bragg
    pseudo_motor_roles = ["theta"]
    motor_roles = ["rota", "rots", "rotd", "ya", "yd", "zd", "bender"]
    
    # Introduce controller properties here.
    ctrl_properties = { 'bragg_tolerance' : {'Type':'PyTango.DevFloat', 
                                    'Description':'Tolerance given to ' + 
                                    'Bragg angle taken into account in the' + 
                                    'small movement validation, to approach ' +
                                    'as much as possible the trajectory ' +
                                    'given by the pseudomotor equations'
                                    }, } 
                                                                            
    # Introduce attributes in here.
    axis_attributes = { 'offset_sample_clear' : { Type : float,
                                     Access : DataAccess.ReadWrite,
                                     Description : 'Offset from sample to ' + 
                                     'external wall of Clear in Y direction' },

                        'my' : { Type : float,
                                 Access : DataAccess.ReadWrite,  
                                 Description : 'y slope coefficient for ' +
                                                    'detector correction' 
                                 }, 

                        'oy' : { Type : float,
                                 Access : DataAccess.ReadWrite,
                                 Description : 'z slope coefficient for ' +
                                                    'detector correction'
                                 },

                        'mz' : { Type : float,
                                 Access : DataAccess.ReadWrite,
                                 Description : 'x offset coefficient ' +
                                                    'for detector correction'
                                 },

                        'oz' : { Type : float,
                                 Access : DataAccess.ReadWrite,
                                 Description : 'z offset coefficient ' +
                                                  'for detector correction'
                                 },

                        'lastPos' : {Type : float, 
                                 Access : DataAccess.ReadWrite,
                                 Description : 'last position set ' 
                                 },
                        'bender_on': {Type: bool,
                                      Access: DataAccess.ReadWrite,
                                      Description:'Use bender on the movement'},}


    """ Konstantin said: Limit angles: from 35 to 80 degrees. 
        From papers: the most interesting is from 55 and 80 degrees because for
        smaller angles we lose a lot of Energy resolution. 
        At this moment, physically only a range between 43 and 76 degrees is 
        possible if we want to avoid collisions. """
    """Currently, everything is done by considering that p=q=ya 
       (ya: y analyzer: being the distance between the sample and 
       the analyzer). """

    def __init__(self, inst, props, *args, **kwargs):

        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("Created CLEAR %s", inst)

        # R is the radius of the Rowland circle in meters.        
        self.R = 500
         
        """ Initialize attributes here.
         Correction coefficients introduced by scientist for the detector
         position correction : my, mz, oy, oz. Used as attributes. """
        
        self.bender_index = [7]
        if not hasattr(self, 'my'):
            self.my = 0.0
        if not hasattr(self, 'oy'):
            self.oy = 0.0
        if not hasattr(self, 'mz'):
            self.mz = 0.0 
        if not hasattr(self, 'oz'):
            self.oz = 0.0 
        if not hasattr(self, 'offset_sample_clear'):
            self.offset_sample_clear = 350.0
            

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
            
        """ STEP 1: Validation of small movements in order to approach the
        trajectory defined by the equations:"""
        motor =self.GetPseudoMotor("theta")
        pseudo_current_pos = motor.get_position().value
        motor_proxy = PyTango.DeviceProxy(motor.full_name)
        inc = pseudo_pos[0] - pseudo_current_pos
        increment_pseudo_position = abs(inc)
        

        print("\n")
        print("Sending the pseudo to {0} position".format(pseudo_pos[0]))
        print("Pseudo is at {0}".format(pseudo_current_pos))
        print("\n")
        
        if (increment_pseudo_position) > self.bragg_tolerance: 
            raise Exception('Bigger movements than {0} degrees for Bragg angle pseudomotor will be rejected.'.format(self.bragg_tolerance))     
        """ End of STEP 1 Validation """
    
    
        """ STEP 2: Validation of physical positions according to last set
        pseudo positon """
        print self.lastPos
        print pseudo_pos
        print("\n")
        print("Calculating if the motors are in correct position")
        print("\n")
        position_tolerance = 0.03
        #print self.motor_roles
        print curr_physical_pos
        msg = ''
        revise = []
                
        for i in range(len(self.motor_roles)):
            if (i+1 in self.bender_index) and (self.bender_on is False):
                continue
            virtualPos = self.CalcPhysical(i+1, [self.lastPos], curr_physical_pos, True)
            #revise.append(pos)
            #name= self.motor_roles[i]
            name= self.GetMotor(self.motor_roles[i])
            current = curr_physical_pos[i]
            print "%s, current %f, should be %f, last position of bragg pseudo %f" %(name,current,virtualPos,self.lastPos)
            if (abs(virtualPos - current) > position_tolerance):
                msg +='The physical motor for the role %s is in a wrong position, current : %f, should be: %f\n' %(name, current, virtualPos)
        if msg != '':          
            print msg
            raise Exception(msg)   
        """ End of STEP 2 Validation """

        ret = []
        for i in range(len(self.motor_roles)):
            if (i+1 in self.bender_index) and (self.bender_on is False): 
                pos = curr_physical_pos[i]
            else:
                pos = self.CalcPhysical(i+1, pseudo_pos, curr_physical_pos)
            ret.append(pos)
            
        self.lastPos = pseudo_pos[0]
        motor_proxy.write_attribute('lastPos',self.lastPos)
        return ret

       
        
    # Calculation of input motors values.
    def CalcPhysical(self, index, pseudo_pos, curr_physical_pos, comprove = False):	
        """Bragg angle"""

        theta = pseudo_pos[0]
        theta_rad = theta*math.pi/180.0

        alpha_rad = math.pi/2.0 - theta_rad
        alpha = alpha_rad*180.0/math.pi

        """ Info: Xtal.Y = p = q - XES.y -y 
        In this pseudo we will work On Rowland, so 'p = q = Xtal.Y'. 
        XES.y will be always set to 0 because the distance between the sample 
        and the WholeClear will be fixed. 
        'y' is the inside-Rowland done by the translation of detector and 
        analyzer (set to 0 for this pseudo)."""

        ya= 2*self.R*math.sin(theta_rad)

        # rota: Rotation Analyzer
        if index==1:
            ret = theta #In degrees

        # rots: Rotation Slits
        elif index == 2:
            ret = theta #In degrees

        # rotd: Rotation Detector
        elif index == 3:
            ret = 2*theta - 90.0 #In degrees 

        # ya: Y analyzer
        elif index == 4:
            """ self.offset_sample_clear is subtracted in order to take into 
                account the variation of the distance between the sample and 
                the external wall of clear (default 350mm). """  
            ret = ya - (self.offset_sample_clear)

        # yd: Y detector
        elif index == 5:
            """  self.offset_sample_clear has been subtracted in order to take 
                 into account the variation of the distance between the sample 
                 and the external wall of clear (default 350mm). """
            f_theta = ya + ya*math.cos(2*theta_rad) - (self.offset_sample_clear)
            ret = f_theta + self.my*(f_theta)*math.sin(2*alpha_rad) + self.oy
            #self._log.debug('my {0}.'.format(self.my))
            #self._log.debug('oy {0}.'.format(self.oy))           

        # zd: Z detector
        elif index == 6:
            g_theta = ya*math.sin(2*theta_rad)
            ret = g_theta + self.mz*(g_theta)*math.cos(2*alpha_rad) + self.oz
            #self._log.debug('mz: {0}.'.format(self.mz))
            #self._log.debug('oz: {0}.'.format(self.oz))

        

        #Calc new bender:
        elif index in self.bender_index:

            #Sagital Radius 
            rs = 2 * self.R *((math.sin(theta_rad))**2)
            ret = rs 
            # devide the bender in two parts
            #ret = (math.asin(40/rc)) * 180/math.pi 
        
        else:
            pass

        self._log.debug("CalcPhysical is being executed")
        return ret

    # Calculation of output PseudoMotor values.
    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):
        """ This pseudomotor returns the Bragg angle in function of the 
        physical motors position (taking as reference the Analyzer rotation).
        The Bragg angle is the angle between the Y axis (beam direction) 
        and the analyzer pitch.
        It is the same angle that exists between the Y axis and the 
        Slits pitch"""
        """bragg = theta; they are given in degrees."""

        theta = physical_pos[0] 
        ret = theta
        #self._log.debug("CalcPseudo is being executed")	
        return ret 
    
    # Introduce here attribute setter.
    def SetAxisExtraPar(self, axis, parameter, value):
        if (parameter == 'my'):
            self.my = value
        elif (parameter == 'oy'):
            self.oy = value
        elif (parameter == 'mz'):
            self.mz = value
        elif (parameter == 'oz'):
            self.oz = value
        elif (parameter == 'offset_sample_clear'):
            self.offset_sample_clear = value
        elif (parameter == 'lastPos'):
            self.lastPos = value
        elif (parameter == 'bender_on'):
            self.bender_on = value
      
    # Introduce here attribute getter.
    def GetAxisExtraPar(self, axis, parameter):
        if (parameter == 'my'):
            return self.my
        elif (parameter == 'oy'):
            return self.oy
        elif (parameter == 'mz'):
            return self.mz
        elif (parameter == 'oz'):
            return self.oz
        elif (parameter == 'offset_sample_clear'):
            return self.offset_sample_clear
        elif (parameter == 'lastPos'):
            return self.lastPos
        elif (parameter == 'bender_on'):
            return self.bender_on
        else:
            return 1






