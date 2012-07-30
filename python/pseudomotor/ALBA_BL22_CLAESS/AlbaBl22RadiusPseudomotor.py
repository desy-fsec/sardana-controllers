import math, logging
from sardana import pool 
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController

class RadiusController(PseudoMotorController):
    """This pseudomotor controller does the calculation of radius 
       of VCM mirror"""
    
    pseudo_motor_roles = ('radius',)
    motor_roles = ('bender',)
                             
    class_prop = { 'conversion':{'Type' : 'PyTango.DevDouble', 'Description' : 'Conversion factor (half steps to 1/km)', 'DefaultValue':1.0}}

    ctrl_extra_attributes = {"PusherOffset":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE"}}

    def __init__(self, inst, props, *args, **kwargs):    
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        #Setting the default value for Pusher Offset
        self.pusherOffset = 0 
        
    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]
    
    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index - 1]
    
    def calc_all_physical(self, pseudos):
        radius, = pseudos
        bender = self.conversion/radius + self.pusherOffset 
        return (bender,)
        
    def calc_all_pseudo(self, physicals):
        bender, = physicals
        try:
            radius = self.conversion/(bender - self.pusherOffset)
        except ZeroDivisionError:
            radius = float('Infinity')
        return (radius,)

    def GetExtraAttributePar(self, axis, name):
        """Get Radius pseudomotor extra attribute.

        :param axis: (int) axis nr to get an extra attribute
        :param name: (string) attribute name to retrieve

        :return: value of the attribute
        """
        if name == "PusherOffset":
            return self.pusherOffset
        

    def SetExtraAttributePar(self, axis, name, value):
        """Set Radius pseudomotor extra attribute.

        :param axis: (int) axis nr to set an extra attribute
        :param name: (string) attribute name to retrieve
        :param value: an extra attribute value to be set

        """
        if name == "PusherOffset":
            self.pusherOffset = value
