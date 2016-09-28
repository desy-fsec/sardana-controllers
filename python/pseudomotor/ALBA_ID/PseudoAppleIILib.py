""" The standard pseudo motor controller library for the device pool """

from sardana.pool.controller import PseudoMotorController
#from pool import PseudoMotorController, PoolUtil

from math import *
import traceback
import numpy

class PseudoAppleII(PseudoMotorController):
    """ """
    
    gender = "AppleII"
    model  = "Standard"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    ctrl_extra_attributes = {'Offset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'Acceleration':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'Deceleration':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'Velocity':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE', 'memorized' : 'false' },
                             'Base_rate':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'AlwaysZero':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'}}
    
    pseudo_motor_roles = ("GapLeft", "GapRight", "Offset", "Taper")
    motor_roles = ("Z1", "Z2", "Z3", "Z4")
    
   
    def __init__(self,inst,props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props, *args, **kwargs)
        self.offsets = {}
        self.AlwaysZero = {}

        self.Acceleration = {}
        self.Deceleration = {}
        self.Velocity = {}
        self.Base_rate = {}

        
    #def calc_physical(self,index,pseudo_pos):
    def CalcPhysical(self,index,pseudo_pos,  curr_physical_pos):
	#print 'CALCPHYSICAL',index,pseudo_pos,  curr_physical_pos
        return self.CalcAllPhysical(pseudo_pos, curr_physical_pos)[index-1]

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
	#print 'CALCALLPHYSICALL',pseudo_pos, curr_physical_pos
        
        gap = pseudo_pos[0]
        symmetry = pseudo_pos[1]
        offset = pseudo_pos[2]
        taper = pseudo_pos[3]
        print "PM:",gap, symmetry, offset, taper
        
        Z10 = self.offsets[1]
        Z20 = self.offsets[2]
        Z30 = self.offsets[3]
        Z40 = self.offsets[4]

        #FB for exit of a sw stop
        if self.AlwaysZero[2] == True:
            symmetry = 0.0
        if self.AlwaysZero[3] == True:
            offset = 0.0
        if self.AlwaysZero[4] == True:
            taper = 0.0
        z1 = Z10 + gap/2.0 + offset - taper/4.0 - symmetry/4.0
        z2 = Z20 + gap/2.0 + offset + taper/4.0 + symmetry/4.0
        z3 = Z30 - gap/2.0 + offset - taper/4.0 + symmetry/4.0
        z4 = Z40 - gap/2.0 + offset + taper/4.0 - symmetry/4.0


	return (z1, z2, z3, z4)


    #def calc_pseudo(self,index,physical_pos):
    def CalcPseudo(self,index,physical_pos, curr_pseudo_pos):
	#print 'CALCPSEUDO', index,physical_pos, curr_pseudo_pos
	return self.CalcAllPseudo(physical_pos, curr_pseudo_pos)[index-1]

    def CalcAllPseudo(self, physical_pos, curr_pseudo_pos):
	#print 'CALCALLPSEUDO', map(int,physical_pos), curr_pseudo_pos
        Z10 = self.offsets[1]
        Z20 = self.offsets[2]
        Z30 = self.offsets[3]
        Z40 = self.offsets[4]
        z1 = physical_pos[0] - Z10
        z2 = physical_pos[1] - Z20
        z3 = physical_pos[2] - Z30
        z4 = physical_pos[3] - Z40

        
        gap = (z1+z2)/2.0 - (z3+z4)/2.0
        symmetry = (z2-z1)+(z3-z4)
        offset = (z1+z2)/4.0 + (z3+z4)/4.0
        taper = (z2-z1)-(z3-z4)

	return (gap, symmetry, offset, taper)

        #if offset in [500,-500, -250,-125]:
            #print "\nIndex:",index
            #print "Physical:",physical_pos[0],physical_pos[1],physical_pos[2],physical_pos[3]
            #print "Z:",z1,z2,z3,z4
            #print "PM:",gap, symmetry, offset, taper
        #if taper in [500,-500, -250,-125]:
            #print "\nZ:",z1,z2,z3,z4
            #print "PM:",gap, symmetry, offset, taper
        
        if index == 1:# GAP
            return gap
        if index == 2:# SYMMETRY
            return symmetry
        if index == 3:# OFFSET
            return offset
        if index == 4:# TAPER
            return taper
        

    def read_all_motors(self,name):
        try:
            m1 = self.GetMotor(0)
            m2 = self.GetMotor(1)
            m3 = self.GetMotor(2)
            m4 = self.GetMotor(3)
            a1 = m1.get_par(name)
            a2 = m2.get_par(name)
            a3 = m3.get_par(name)
            a4 = m4.get_par(name)
            a = numpy.average([a1,a2,a3,a4])
            print "The attr ", name, " is ", a
            return a
        except Exception,e:
            print "Err in read ", name, str(e)
            traceback.print_exc()

    def GetExtraAttributePar(self,ind,name):
        if name == "Offset":
            return self.offsets[ind]
        elif name == "AlwaysZero":
            return self.AlwaysZero[ind]
        elif name == "Acceleration":
            self.Acceleration[ind] = self.read_all_motors(name)
            return self.Acceleration[ind]
        elif name == "Deceleration":
            self.Deceleration[ind] = self.read_all_motors(name)
            return self.Deceleration[ind]
        elif name == "Velocity":
            vel = self.read_all_motors(name)
            if ind==1:
                self.Velocity[ind] = 2*vel
            if ind==2:
                self.Velocity[ind] = 0.0
            if ind==3:
                self.Velocity[ind] = vel
            if ind==4:
                self.Velocity[ind] = 4*vel
            return self.Velocity[ind]
        elif name == "Base_rate":
            self.Base_rate[ind] = self.read_all_motors(name)
            return self.Base_rate[ind]


    def SetExtraAttributePar(self,ind,name,value):
        try:
            print "Set Gaps",ind,name,value
            if name == "Offset":
                self.offsets[ind] = value
            elif name == "AlwaysZero":
                self.AlwaysZero[ind] = value
            elif name == "Acceleration":
                self.Acceleration[ind] = value
            elif name == "Deceleration":
                self.Deceleration[ind] = value
            elif name == "Velocity":
                self.Velocity[ind] = value
                #self.GetMotor(ind-1).set_par(name, value)
            elif name == "Base_rate":
                self.Base_rate[ind] = value
        except Exception,e:
            print "PseudoAppleII Exception"

class PseudoPhaseAppleII(PseudoMotorController):
    """ """
    
    gender = "AppleII"
    model  = "Phase"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"
    
    ctrl_extra_attributes = {'Offset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'Acceleration':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'Deceleration':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'Velocity':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             'Base_rate':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'} }

    pseudo_motor_roles = ("Phase", "AntiPhase")
    motor_roles = ("Y1", "Y2")
    
     
    def __init__(self,inst,props, *args, **kwargs):
        PseudoMotorController.__init__(self,inst,props, *args, **kwargs)
        self.offsets = {}

        self.Acceleration = {}
        self.Deceleration = {}
        self.Velocity = {}
        self.Base_rate = {}

    def calc_physical(self,index,pseudo_pos):
        phase = pseudo_pos[0]
        antiphase = pseudo_pos[1]
        
        #y10 = -700000
        #y20 = 700000
        y10 = self.offsets[1]
        y20 = self.offsets[2]
        y1 = y10 + (phase + antiphase)
        y2 = y20 + (phase - antiphase)
        
        if index == 1:# y1
            return y1
        if index == 2:# y2
            return y2
      
    def calc_pseudo(self,index,physical_pos):
        y10 = self.offsets[1]
        y20 = self.offsets[2]
        y1 = physical_pos[0] - y10
        y2 = physical_pos[1] - y20
        
        phase = (y1+y2)/2.0
        antiphase = (y1-y2)/2.0
        
        if index == 1:# phase
            return phase
        if index == 2:# antiphase
            return antiphase

    def read_all_motors(self,name):
        try:
            m1 = self.GetMotor(0)
            m2 = self.GetMotor(1)
            a1 = m1.get_par(name)
            a2 = m2.get_par(name)
            a = numpy.average([a1,a2])
            print "The attr ", name, " is = ", a
            return a
        except Exception,e:
            print "Err in read ", name, str(e)
            traceback.print_exc()
        
    def GetExtraAttributePar(self,ind,name):
        if name == "Offset":
            return self.offsets[ind]
        elif name == "Acceleration":
            self.Acceleration[ind] = self.read_all_motors(name)
            return self.Acceleration[ind]
        elif name == "Deceleration":
            self.Deceleration[ind] = self.read_all_motors(name)
            return self.Deceleration[ind]
        elif name == "Velocity":
            vel = self.read_all_motors(name)
            if ind==1:
                self.Velocity[ind] = 2*vel
            if ind==2:
                self.Velocity[ind] = vel
            return self.Velocity[ind]
        elif name == "Base_rate":
            self.Base_rate[ind] = self.read_all_motors(name)
            return self.Base_rate[ind]
           


    def SetExtraAttributePar(self,ind,name,value):
        try:
            print "Set Phases",ind,name,value
            if name == "Offset":
                self.offsets[ind] = value
            elif name == "Acceleration":
                self.Acceleration[ind] = value
            elif name == "Deceleration":
                self.Deceleration[ind] = value
            elif name == "Velocity":
                self.Velocity[ind] = value
            elif name == "Base_rate":
                self.Base_rate[ind] = value
        except Exception,e:
            print "PseudoPhaseAppleII Exception"
