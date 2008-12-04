""" The standard pseudo motor controller library for the device pool """

from pool import PseudoMotorController, PoolUtil

from math import *

class PseudoMotorProxy(PseudoMotorController):
    """ The simplest pseudo motor you can have: It just forwards the physical 
        motor requests"""
    
    #pseudo_motor_roles = ("proxy",)
    motor_roles = ("motor",)

    def calc_physical(self,index,pseudo_pos):
        return pseudo_pos[0]
    
    def calc_pseudo(self,index,physical_pos):
        return physical_pos[0]
    
    
class Slit(PseudoMotorController):
    """A Slit pseudo motor controller for handling gap and offset pseudo 
       motors. The system uses to real motors sl2t (top slit) and sl2b (bottom
       slit)"""
    
    gender = "Slit"
    model  = "Default Slit"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    pseudo_motor_roles = ("Gap", "Offset")
    motor_roles = ("sl2t", "sl2b")
    
    class_prop = {'sign':{'Type':'PyTango.DevDouble','Description':'Gap = sign * calculated gap\nOffset = sign * calculated offet','DefaultValue':1},}
                           
    def calc_physical(self,index,pseudo_pos):
        half_gap = pseudo_pos[0]/2.0
        if index == 1:
            ret = self.sign * (pseudo_pos[1] + half_gap)
        else:
            ret = self.sign * (half_gap - pseudo_pos[1])
        return ret
    
    def calc_pseudo(self,index,physical_pos):
        gap = physical_pos[1] + physical_pos[0]
        if index == 1:
            ret = self.sign * gap
        else:
            ret = self.sign * (physical_pos[0] - gap/2.0)
        return ret
        
    def calc_all_pseudo(self, physical_pos):
        """Calculates the positions of all pseudo motors that belong to the 
           pseudo motor system from the positions of the physical motors."""
        gap = physical_pos[1] + physical_pos[0]
        return (self.sign * gap, 
                self.sign * (physical_pos[0] - gap/2.0))
    
    def calc_all_physical(self, pseudo_pos):
        """Calculates the positions of all motors that belong to the pseudo 
           motor system from the positions of the pseudo motors."""
        half_gap = pseudo_pos[0]/2.0
        return (self.sign * (pseudo_pos[1] + half_gap), 
                self.sign * (half_gap - pseudo_pos[1]))
            
class BasePower(PseudoMotorController):
    """A pseudo motor system for controlling base and power for 
       the \"real motor\"."""

    pseudo_motor_roles = ("Base", "Power")
    motor_roles = ("Real",)

    def calc_physical(self,index,pseudo_pos):
        return pseudo_pos[0] * (10 ** pseudo_pos[1])
    
    def calc_pseudo(self,index,physical_pos):
        base = physical_pos[0]
        power = 0
        if base >= 1:
            while base >= 10:
                base /= 10.0
                power += 1
        else :
            while base < 1:
                base *= 10.0
                power -= 1
        
        if index == 1:
            return base
        else:
            return power
            
            
class PseudoTheta(PseudoMotorController):
    """A pseudo motor for the theta and 2theta motors."""

    pseudo_motor_roles = ("pm_theta",)
    motor_roles = ("theta","2theta")

    def calc_physical(self,index,pseudo_pos):
        if index == 0:
            return pseudo_pos[0]
        elif index == 1:
            return 2 * pseudo_pos[0]
        return 0
        
    def calc_pseudo(self,index,physical_pos):
        print "calc_pseudo "+str(index)+" "+str(physical_pos)
        if index == 0:
            return physical_pos[0]
        elif index == 1:
            return physical_pos[1] / 2
        return 0
    

class PseudoMotorEncoderPosition(PseudoMotorController):
    """ A pseudo motor which connects with a simple motor. No changes
    when writing the position but for the read position, an external
    device server is used, reading the given property and evaluating the given formula."""
    
    # JUST ANOTHER MOTOR WHICH READS THE POSITION FROM THE GIVEN DEVICE SERVER ATTRIBUTE
    pseudo_motor_roles = ("motor_enc_pos",)
  
    # JUST THE MOTOR THAT NEEDS AN EXTERNAL "ENCODER"
    motor_roles = ("motor",)

    # THE EXTRA ATTRIBUTES EXTERNALATTRIBUTE AND FORMULA FOR EACH PSEUDO MOTOR
    ctrl_extra_attributes = {'ExternalAttribute':
                             {'Type':'PyTango.DevString'
                              ,'Description':'The Tango Attribute to read (e.g. my/tango/dev/attr)'
                              ,'R/W Type':'PyTango.READ_WRITE'}
                             ,'Formula':
                             {'Type':'PyTango.DevString'
                              ,'Description':'The Formula to get the encoder position from a RAW ENCODER VALUE.\ne.g. If encoder goes from 10 to 0 for the position values 0 to 10, the formula should be: "(-1 * VALUE) + 10"'
                              ,'R/W Type':'PyTango.READ_WRITE'}
                             }

    FORMULA = 'Formula'
    EXTERNALATTRIBUTE = 'ExternalAttribute'
    ATTRIBUTE = 'Attribute'
    
    
    def __init__(self,inst,props):
        
        PseudoMotorController.__init__(self,inst,props)
        self.axisExtraAttributes = {}
        self.axisExtraAttributes[1] = {self.FORMULA:"VALUE",self.EXTERNALATTRIBUTE:""
                                       ,self.ATTRIBUTE:""}
        self.device_proxy = None
        

    def calc_physical(self,index,pseudo_pos):
        """ The physical value is the same one."""
        return pseudo_pos[0]

    def calc_pseudo(self,index,physical_pos):
        """ Just ignore the physical position and return the read value of the external attribute. """
        try:
            attribute = self.axisExtraAttributes[index][self.ATTRIBUTE]
            VALUE = self.device_proxy.read_attribute(attribute).value
            return eval(self.axisExtraAttributes[index][self.FORMULA])
        except Exception,e:
            print "[PseudoMotorEncoderPosition]",self.inst_name,": Some exception found at calc_pseudo",e
        return physical_pos[0]
            
    def GetExtraAttributePar(self,axis,name):
        # IMPLEMENTED THE EXTRA ATTRIBUTE 'Formula','ExternalAttribute'
        return self.axisExtraAttributes[axis][name]

    def SetExtraAttributePar(self,axis,name,value):
        # IMPLEMENTED THE EXTRA ATTRIBUTE 'Formula','ExternalAttribute'
        self.axisExtraAttributes[axis][name] = value
        try:
            if name == self.EXTERNALATTRIBUTE:
                idx = value.rfind("/")
                device =  value[:idx]
                attribute = value[idx+1:]
                self.axisExtraAttributes[axis][self.ATTRIBUTE] = attribute
                self.device_proxy = PoolUtil().get_device(self.inst_name,device)
        except Exception,e:
            print "[PseudoMotorEncoderPosition]",self.inst_name,": Some exception found at SetExtraAttributePar",e