#from pool import PseudoCounterController
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController

from diagnostics import bpm

class PseudoCurrentCalculation():
    def pseudo_current(self, first, second):
        return (first - second) / (first + second)


class BL13OHXBPMPCController(PseudoCounterController):

    counter_roles = ('ib_u', 'ib_d', 'ib_r', 'ib_l')
    pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_', 'b_x', 'b_z')
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)

    def Calc(self, index, counter_values):
        ib_u, ib_d, ib_r, ib_l = counter_values

        if 'ib_x' == self.pseudo_counter_roles[index-1]:
            ib_x = self.pseudo_current(ib_r, ib_l)
            return ib_x
        elif 'ib_z' == self.pseudo_counter_roles[index-1]:
            ib_z = self.pseudo_current(ib_u, ib_d)
            return ib_z
        elif 'ib_' == self.pseudo_counter_roles[index-1]:
            return ib_u + ib_d + ib_r + ib_l
        elif 'b_x' == self.pseudo_counter_roles[index-1]:
            b_x = 1234
            return b_x
        elif 'b_z' == self.pseudo_counter_roles[index-1]:
            b_z = 5678
            return b_z

    def pseudo_current(self, first, second):
        return (first - second) / (first + second)


### class BL13OHXBPM01PCController(PseudoCounterController, PseudoCurrentCalculation):
###     counter_roles = ('ib_u', 'ib_d', 'ib_r', 'ib_l')
###     pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_','b_x', 'b_z')
###     pass
### class BL13OHXBPM02PCController(PseudoCounterController, PseudoCurrentCalculation):
###     counter_roles = ('ib_u', 'ib_d', 'ib_r', 'ib_l')
###     pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_','b_x', 'b_z')
###     pass

class BL13OHXBPM03PCController(PseudoCounterController, PseudoCurrentCalculation):
    counter_roles = ('ib_u', 'ib_d', 'ib_r', 'ib_l')
    pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_','b_x', 'b_z')

    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)

    def Calc(self, index, counter_values):
        ib_u, ib_d, ib_r, ib_l = counter_values

        if 'ib_x' == self.pseudo_counter_roles[index-1]:
            ib_x = self.pseudo_current(ib_r, ib_l)
            return ib_x
        elif 'ib_z' == self.pseudo_counter_roles[index-1]:
            ib_z = self.pseudo_current(ib_u, ib_d)
            return ib_z
        elif 'ib_' == self.pseudo_counter_roles[index-1]:
            return ib_u + ib_d + ib_r + ib_l
        elif 'b_x' == self.pseudo_counter_roles[index-1]:
            ib_x = self.pseudo_current(ib_r, ib_l)
            b_x = bpm.b3x_calibration(ib_x)
            return b_x
        elif 'b_z' == self.pseudo_counter_roles[index-1]:
            ib_z = self.pseudo_current(ib_u, ib_d)
            b_z = bpm.b3z_calibration(ib_z)
            return b_z

class BL13OHXBPM04PCController(PseudoCounterController, PseudoCurrentCalculation):
    counter_roles = ('ib_u', 'ib_d', 'ib_r', 'ib_l')
    pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_','b_x', 'b_z')

    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)

    def Calc(self, index, counter_values):
        ib_u, ib_d, ib_r, ib_l = counter_values

        if 'ib_x' == self.pseudo_counter_roles[index-1]:
            ib_x = self.pseudo_current(ib_r, ib_l)
            return ib_x
        elif 'ib_z' == self.pseudo_counter_roles[index-1]:
            ib_z = self.pseudo_current(ib_u, ib_d)
            return ib_z
        elif 'ib_' == self.pseudo_counter_roles[index-1]:
            return ib_u + ib_d + ib_r + ib_l
        elif 'b_x' == self.pseudo_counter_roles[index-1]:
            ib_x = self.pseudo_current(ib_r, ib_l)
            b_x = bpm.b4x_calibration(ib_x)
            return b_x
        elif 'b_z' == self.pseudo_counter_roles[index-1]:
            ib_z = self.pseudo_current(ib_u, ib_d)
            b_z = bpm.b4z_calibration(ib_z)
            return b_z


### class BL13EHXBPM05PCController(PseudoCounterController, PseudoCurrentCalculation):
###     counter_roles = ('ib_lu', 'ib_ld', 'ib_ru', 'ib_rd')
###     pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_','b_x', 'b_z')
###     pass
### class BL13EHXBPM06PCController(PseudoCounterController, PseudoCurrentCalculation):
###     counter_roles = ('ib_lu', 'ib_ld', 'ib_ru', 'ib_rd')
###     pseudo_counter_roles = ('ib_x', 'ib_z', 'ib_','b_x', 'b_z')
###     pass




#### STILL PENDING COUNTERS TO PROVIDE:
#### 'b12xp', 'b12zp', 'b13xp', 'b13zp', 'b14xp', 'b14zp', 'b23xp', 'b23zp', 'b24xp', 'b24zp', 'b34xp', 'b34zp')


class BL13OHXBPMsPCController(PseudoCounterController):

    counter_roles = ('b1x', 'b1z', 'b2x', 'b2z', 'b3x', 'b3z', 'b4x', 'b4z')
    pseudo_counter_roles = ('b12xp', 'b12zp', 'b13xp', 'b13zp', 'b14xp', 'b14zp', 'b23xp', 'b23zp', 'b24xp', 'b24zp', 'b34xp', 'b34zp')
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        self.DISTANCE_12 = 1354.5
        self.DISTANCE_23 = 1831.5
        self.DISTANCE_34 = 1790.0
        self.DISTANCE_13 = self.DISTANCE_12 + self.DISTANCE_23
        self.DISTANCE_14 = self.DISTANCE_12 + self.DISTANCE_23 + self.DISTANCE_34
        self.DISTANCE_24 = self.DISTANCE_23 + self.DISTANCE_34


    def Calc(self, index, counter_values):
        b1x, b1z, b2x, b2z, b3x, b3z, b4x, b4z = counter_values

        if 'b12xp' == self.pseudo_counter_roles[index-1]:
            b12xp = self.pseudo_slope_between_xbpms(b1x, b2x, self.DISTANCE_12)
            return b12xp
	elif 'b12zp' == self.pseudo_counter_roles[index-1]:
            b12zp = self.pseudo_slope_between_xbpms(b1z, b2z, self.DISTANCE_12)
            return b12zp
	elif 'b13xp' == self.pseudo_counter_roles[index-1]:
            b13xp = self.pseudo_slope_between_xbpms(b1x, b3x, self.DISTANCE_13)
            return b13xp
	elif 'b13zp' == self.pseudo_counter_roles[index-1]:
            b13zp = self.pseudo_slope_between_xbpms(b1z, b3z, self.DISTANCE_13)
            return b13zp
	elif 'b14xp' == self.pseudo_counter_roles[index-1]:
            b14xp = self.pseudo_slope_between_xbpms(b1x, b4x, self.DISTANCE_14)
            return b14xp
        elif 'b14zp' == self.pseudo_counter_roles[index-1]:
            b14zp = self.pseudo_slope_between_xbpms(b1z, b4z, self.DISTANCE_14)
            return b14zp
        elif 'b23xp' == self.pseudo_counter_roles[index-1]:
            b23xp = self.pseudo_slope_between_xbpms(b2x, b3x, self.DISTANCE_23)
            return b23xp
        elif 'b23zp' == self.pseudo_counter_roles[index-1]:
            b23zp = self.pseudo_slope_between_xbpms(b2z, b3z, self.DISTANCE_23)
            return b23zp
        elif 'b24xp' == self.pseudo_counter_roles[index-1]:
            b24xp = self.pseudo_slope_between_xbpms(b2x, b4x, self.DISTANCE_24)
            return b24xp
        elif 'b24zp' == self.pseudo_counter_roles[index-1]:
            b24zp = self.pseudo_slope_between_xbpms(b2z, b4z, self.DISTANCE_24)
            return b24zp
        elif 'b34xp' == self.pseudo_counter_roles[index-1]:
            b34xp = self.pseudo_slope_between_xbpms(b3x, b4x, self.DISTANCE_34)
            return b34xp
        elif 'b34zp' == self.pseudo_counter_roles[index-1]:
            b34zp = self.pseudo_slope_between_xbpms(b3z, b4z, self.DISTANCE_34)
            return b34zp

    def pseudo_slope_between_xbpms(first, second, distance):
        return (second - first) / distance / 1e6


### class BL13OHXBPMsPCController(PseudoCounterController):
### 
###     counter_roles = ('ib1u', 'ib1d', 'ib1r', 'ib1l', 'ib2u', 'ib2d', 'ib2r', 'ib2l', 'ib3u', 'ib3d', 'ib3r', 'ib3l', 'ib4u', 'ib4d', 'ib4r', 'ib4l')
###     pseudo_counter_roles = ('ib1x', 'ib1z', 'ib1', 'b1x', 'b1z','ib2x', 'ib2z', 'ib2', 'b2x', 'b2z', 'ib3x', 'ib3z', 'ib3', 'b3x', 'b3z','ib4x', 'ib4z', 'ib4', 'b4x', 'b4z', 'b12xp', 'b12zp', 'b13xp', 'b13zp', 'b14xp', 'b14zp', 'b23xp', 'b23zp', 'b24xp', 'b24zp', 'b34xp', 'b34zp')
###     
###     def __init__(self, inst, props, *args, **kwargs):
###         PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
### 
###     def pseudo_current(self, first, second):
###         return (first - second) / (first + second)
### 
###     def pseudo_slope_between_xbpms(self, first, second, distance):
###         return (second - first) / distance / 1e6
### 
###     def pseudo_sum_currents(self, first, second, third, forth):
###         return first + second + third + forth
### 
###     def Calc(self, index, counter_values):
###         ib1u, ib1d, ib1r, ib1l, ib2u, ib2d, ib2r, ib2l, ib3u, ib3d, ib3r, ib3l, ib4u, ib4d, ib4r, ib4l = counter_values
### 
###         if 'ib1x' == self.pseudo_counter_roles[index-1]:
###             ib1x = self.pseudo_current(ib1r, ib1l)
###             return ib1x
###         elif 'ib1z' == self.pseudo_counter_roles[index-1]:
###             ib1z = self.pseudo_current(ib1u, ib1d)
###             return ib1z
###         elif 'ib1' == self.pseudo_counter_roles[index-1]:
###             return ib1u + ib1d + ib1r + ib1l
###         elif 'b1x' == self.pseudo_counter_roles[index-1]:
###             b1x = 1000
###             return b1x
###         elif 'b1z' == self.pseudo_counter_roles[index-1]:
###             b1z = 1000
###             return b1z
### 
###         elif 'ib2x' == self.pseudo_counter_roles[index-1]:
###             ib2x = self.pseudo_current(ib2r, ib2l)
###             return ib2x
###         elif 'ib2z' == self.pseudo_counter_roles[index-1]:
###             ib2z = self.pseudo_current(ib2u, ib2d)
###             return ib2z
###         elif 'ib2' == self.pseudo_counter_roles[index-1]:
###             return ib2u + ib2d + ib2r + ib2l
###         elif 'b2x' == self.pseudo_counter_roles[index-1]:
###             b2x = 2000
###             return b2x
###         elif 'b2z' == self.pseudo_counter_roles[index-1]:
###             b2z = 2000
###             return b2z
### 
###         elif 'ib3x' == self.pseudo_counter_roles[index-1]:
###             ib3x = self.pseudo_current(ib3r, ib3l)
###             return ib3x
###         elif 'ib3z' == self.pseudo_counter_roles[index-1]:
###             ib3z = self.pseudo_current(ib3d, ib3u)
###             return ib3z
###         elif 'ib3' == self.pseudo_counter_roles[index-1]:
###             return ib3u + ib3d + ib3r + ib3l
###         elif 'b3x' == self.pseudo_counter_roles[index-1]:
###             b3x = 1234 
###             return b3x
###         elif 'b3z' == self.pseudo_counter_roles[index-1]:
###             b3z = 4321
###             return b3z
### 
###         elif 'ib4x' == self.pseudo_counter_roles[index-1]:
###             ib4x = self.pseudo_current(ib4r, ib4l)
###             return ib4x
###         elif 'ib4z' == self.pseudo_counter_roles[index-1]:
###             ib4z = self.pseudo_current(ib4u, ib4d)
###             return ib4z
###         elif 'ib4' == self.pseudo_counter_roles[index-1]:
###             return ib4u + ib4d + ib4r + ib4l
###         elif 'b4x' == self.pseudo_counter_roles[index-1]:
###             b4x = 4000
###             return b4x
###         elif 'b4z' == self.pseudo_counter_roles[index-1]:
###             b4z = 4000
###             return b4z
### 
### 	elif 'b12xp' == self.pseudo_counter_roles[index-1]:
###             b1x = 1000
###             b2x = 2000
###             distance = 1354.5
###             b12xp = self.pseudo_slope_between_xbpms(b1x, b2x, distance)
###             return b12xp
### 	elif 'b12zp' == self.pseudo_counter_roles[index-1]:
###             b1z = 1000
###             b2z = 2000
###             distance = 1354.5
###             b12zp = self.pseudo_slope_between_xbpms(b1z, b2z, distance)
###             return b12zp
### 	elif 'b13xp' == self.pseudo_counter_roles[index-1]:
###             b1x = 1000
###             b3x = 3000
###             distance = 3186.0
###             b13xp = self.pseudo_slope_between_xbpms(b1x, b3x, distance)
###             return b13xp
### 	elif 'b13zp' == self.pseudo_counter_roles[index-1]:
###             b1z = 1000
###             b3z = 3000
###             distance = 3186.0
###             b13zp = self.pseudo_slope_between_xbpms(b1z, b3z, distance)
###             return b13zp
### 	elif 'b14xp' == self.pseudo_counter_roles[index-1]:
###             b1x = 1000
###             b4x = 2000
###             distance = 4973.0
###             b14xp = self.pseudo_slope_between_xbpms(b1x, b4x, distance)
###             return b14xp
###         elif 'b14zp' == self.pseudo_counter_roles[index-1]:
###             b1z = 1000
###             b4z = 4000
###             distance = 4976.0
###             b14zp = self.pseudo_slope_between_xbpms(b1z, b4z, distance)
###             return b14zp
###         elif 'b23xp' == self.pseudo_counter_roles[index-1]:
###             b2x = 2000
###             b3x = 3000
###             distance = 1831.5
###             b23xp = self.pseudo_slope_between_xbpms(b2x, b3x, distance)
###             return b23xp
###         elif 'b23zp' == self.pseudo_counter_roles[index-1]:
###             b2z = 2000
###             b3z = 3000
###             distance = 1831.5
###             b23zp = self.pseudo_slope_between_xbpms(b2z, b3z, distance)
###             return b23zp
###         elif 'b24xp' == self.pseudo_counter_roles[index-1]:
###             b2x = 2000
###             b4x = 4000
###             distance = 3621.5
###             b24xp = self.pseudo_slope_between_xbpms(b2x, b4x, distance)
###             return b24xp
###         elif 'b24zp' == self.pseudo_counter_roles[index-1]:
###             b2z = 2000
###             b4z = 4000
###             distance = 3621.5
###             b24zp = self.pseudo_slope_between_xbpms(b2z, b4z, distance)
###             return b24zp
###         elif 'b34xp' == self.pseudo_counter_roles[index-1]:
###             b3x = 3000
###             b4x = 4000
###             distance = 1790.0
###             b34xp = self.pseudo_slope_between_xbpms(b3x, b4x, distance)
###             return b34xp
###         elif 'b34zp' == self.pseudo_counter_roles[index-1]:
###             b3z = 3000
###             b4z = 4000
###             distance = 1790.0
###             b34zp = self.pseudo_slope_between_xbpms(b3z, b4z, distance)
###             return b34zp
