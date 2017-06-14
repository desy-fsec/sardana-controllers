""" The standard pseudo motor controller library for the device pool """

from sardana.pool.controller import PseudoMotorController

from math import *

class PseudoMpw(PseudoMotorController):
    """ """
    
    gender = "Mpw"
    model  = "Standard"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    axis_attributes = {'Offset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'} }
    
    pseudo_motor_roles = ("Gap", "Taper")
    motor_roles = ("AL1", "AL2")
    
    def __init__(self,inst,props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props, *args, **kwargs)
        self.offsets = {}

    def calc_physical(self,index,pseudo_pos):
        
        gap = pseudo_pos[0]
        taper = pseudo_pos[1]
        
        AL10 = self.offsets[1]
        #print 'Al10 = %s'%AL10
        AL20 = self.offsets[2]
        #print 'Al20 = %s'%AL20
        AL1 = AL10 + gap 
        b6 = +1.374752477070950 *pow(10,-29)
        b5 = -7.980673786756850 *pow(10,-24)
        b4 = +1.070651244119470 *pow(10,-18)
        b3 = +1.655276625324590 *pow(10,-14)
        b2 = +1.561018238568040 *pow(10,-8)
        b1 = -4.415419125372270 *pow(10,-3)
        b0 = +166.5866942989250
        AL20 = AL20 +b6*pow(AL1,6)+b5*pow(AL1,5)+b4*pow(AL1,4)+b3*pow(AL1,3)+b2*pow(AL1,2)+b1*AL1+ b0
        AL2 = AL20 + gap + taper
        #print "AL20", AL20
        #print "gap", gap
        #print "taper", taper
        #print "AL2", AL2
        #print "calc_physical", AL1, AL2
        
        if index == 1:# AL1
            return AL1
        if index == 2:# AL2
            return AL2
            
    def calc_pseudo(self,index,physical_pos):
        AL10 = self.offsets[1]
        AL20 = self.offsets[2]
        AL1 = physical_pos[0] - AL10
        b6 = +1.374752477070950 *pow(10,-29)
        b5 = -7.980673786756850 *pow(10,-24)
        b4 = +1.070651244119470 *pow(10,-18)
        b3 = +1.655276625324590 *pow(10,-14)
        b2 = +1.561018238568040 *pow(10,-8)
        b1 = -4.415419125372270 *pow(10,-3)
        b0 = +166.5866942989250
        AL20 = AL20 +b6*pow(AL1,6)+b5*pow(AL1,5)+b4*pow(AL1,4)+b3*pow(AL1,3)+b2*pow(AL1,2)+b1*AL1+ b0
        #print ''
        AL2 = physical_pos[1] - AL20
        #print "In calc_pseudo(",index,physical_pos,self.offsets,'), AL10,AL20,AL1 = ',AL10,AL20,AL1,AL2
        gap = AL1
        taper = AL2 - AL1
        
        #print "calc_pseudo(",index,physical_pos,'), gap,taper = ',gap,taper
        
        if index == 1:# GAP
            return gap
        if index == 2:# TAPER
            return taper
        
    def GetExtraAttributePar(self,ind,name):
        if name == "Offset":
            return self.offsets[ind]

    def SetExtraAttributePar(self,ind,name,value):
        try:
            if name == "Offset":
                self.offsets[ind] = value
            print "Set Offset ",ind,"=",value
        except Exception,e:
            print "PseudoMpw Exception"



