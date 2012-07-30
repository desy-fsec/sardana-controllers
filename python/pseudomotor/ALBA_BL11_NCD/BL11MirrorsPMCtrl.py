#!/usr/bin/env python
#############################################################################
##
## file :    BL11_NCD_mirrorCurvature.py
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

import math
import PyTango
from pool import PseudoMotorController

NaN = float('nan')

#FIXMEs: image of the controllers

class Bl11MirrorCurvature(PseudoMotorController):
    """Radius pseudo for mirror benders."""
    gender = "Curvature"
    model  = "BL11-NCD mirror curvature pseudomotor"
    organization = "CELLS - ALBA"
    image = "energy.png"#FIXME
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ("Radius",)
    motor_roles = ("UpStreamBender","DownStreamBender",)
    
    def __init__(self,inst,props):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        PseudoMotorController.__init__(self,inst,props)
        self.debug = False

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        return (0.0,0.0,)

    def calc_all_pseudo(self, physicals):
        return (0.0,)

class Bl11MirrorAngle(PseudoMotorController):
    """Pseudo to convine two motors who have the same direction
       into two pseudos with this direction and the angle.
       In the case of the ncd mirrors is Z and pitch movements,
       and for the ncd vessel is X and roll movements.
       
       UpperMotor position = (x1,y1)
       DownerMotor position = (x2,y2)
       ?Translation position = (xr,yr)
       
       equation: y(x) = mx+n
       
       m = (y1-y2)/(x1-x2)
       n = y1-mx1
       alpha = atan(m)
       yr = mxr+y1-mx1
       
       assuming x1 = 0 (is the reference axis)
       => distance between axis = x2
       => tranlation position (x2/2,yr)
       
       m = (y1-y2)/(-x2)
       alpha = atan(m)
       yr = m(x2/2)+y1
    """
    gender = "Angle"
    model  = "BL11-NCD mirror angle pseudomotor"
    organization = "CELLS - ALBA"
    image = "energy.png"#FIXME
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ("Translation","Angle",)
    motor_roles = ("UpperMotor","DownerMotor",)
    
    class_prop = { 'distance':{'Type':'PyTango.DevDouble',
                               'Description':'Distance between the two movable axis',
                               'DefaultValue':1.0
                        },
                    }
    
    def __init__(self,inst,props):
        """ Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        """
        PseudoMotorController.__init__(self,inst,props)
        self.debug = False
        #?!
        if props.has_key('distance'):
            self.distance = props['distance']
        else:
            self.distance = self.class_prop['distance']['DefaultValue']

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        yr,alpha = pseudos
        try:
            m = math.tan(math.radians(alpha))
            n = yr-m*(self.distance/2)
            #print("y = %6.3fx+%6.3f"%(m,n))
            y1 = yr-(m*self.distance)/2
            y2 = m*self.distance+yr-(m*self.distance/2)
            return (y1,y2,)
        except Exception,e:
            self._log.error('calc_all_physical(): Exception %s'%(e))
            return (NaN,NaN,)


    def calc_all_pseudo(self, physicals):
        y1,y2 = physicals
        try:
            m = (y1-y2)/(-self.distance)
            #n = y1
            #print("y = %6.3fx+%6.3f"%(m,n))
            yr = (m * self.distance/2)+y1
            alpha = math.degrees(math.atan(m))
            return (yr,alpha,)
        except Exception,e:
            self._log.error('calc_all_pseudo(): Exception %s'%(e))
            return (NaN,NaN,)


if __name__ == '__main__':
  # Just some unit tests of the computation
#  curvatureCtrl = Bl11MirrorCurvature('curvature_test',{})
#  curvatureCtrl.name = 'curvature_test'
#  curvatures2Test = [(0.0,0.0)]
#  for test in curvatures2Test:
#      radius = curvatureCtrl.calc_all_pseudo(test)
#      b1,b2 = curvatureCtrl.calc_all_physical(radius)
#      print("test= %6.3f,%6.3f\tradius= %6.3f\tb1=%6.3f\tb2=%6.3f"\
#            %(test[0],test[1],radius[0],b1,b2))
  
  angleCtrl = Bl11MirrorAngle('angle_test',{'distance':1.0})
  angleCtrl.name = 'angle_test'
  y = [0.0,1.0,math.sqrt(2.0),math.sqrt(2.0)+1]
  angles2Test = [(i,j) for i in y for j in y]
  for test in angles2Test:
      translation,angle = angleCtrl.calc_all_pseudo(test)
      up,down = angleCtrl.calc_all_physical([translation,angle])
      print("test= %6.3f,%6.3f\ttranslation= %6.3f\tangle= %6.3f\tup= %6.3f\tdown= %6.3f"\
            %(test[0],test[1],translation,angle,up,down))
