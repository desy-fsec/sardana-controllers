import logging, math
import taurus
import PyTango
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController, Memorized

NaN = float("nan")

class Mad26Energy(PseudoMotorController):
    """Energy pseudo motor controller for BL04-MSPD energy calculation
    """
    class_prop = { }

    axis_attributes = {"dSpacing":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE", "memorized":Memorized}}

    pseudo_motor_roles = ("energy",)
    motor_roles = ("theta", "2theta", "trans")

    OA = 541.12
    SO = 550
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)        
        self.inst = inst
        self.attributes = {1:{"dspacing":3.145}}


    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        raise Exception("This motor is not foreseen for motion. It is used only for position readout")
        #energy, = pseudos #[keV]
     
        #try:
            #d = self.attributes[1]['dspacing']
        #except KeyError, e:
            #raise PyTango.DevFailed("dSpacing attribute is not set for energy motor")
        #try:
            #theta_rad = math.asin(12.3984/(2*d*energy))
            #theta2_rad = 2 * theta_rad
            #Ro=550/(2*math.cos(theta_rad/2))
            #self._log.debug("Ro %f" % Ro)
            #trans = 750 - 2 * Ro * math.cos(3*theta_rad/2)
            #theta = math.degrees(theta_rad)
            #theta2 = math.degrees(theta2_rad)
            #self._log.debug("theta %f" , theta)
            #self._log.debug("2theta %f" , theta2)
            #self._log.debug("trans %f" , trans)
            
            ##setting up correct velocities
            ##todo: whenever possible change to getMotorProxy(id_or_role)
            #theta_m = PoolUtil().get_device(self.inst, "pd_madth")
            #theta2_m = PoolUtil().get_device(self.inst, "pd_mad2th")
            #trans_m = PoolUtil().get_device(self.inst, "pd_madtrans")
            
            ##theta configuration: velocity (half of 2theta) and acceleration time (the same as 2theta)
            #theta2_vel = theta2_m.read_attribute("velocity").value
            #theta2_acc = theta2_m.read_attribute("acceleration").value
            #theta_vel = theta2_vel/2
            #theta_acc = theta2_acc
            #theta_m.write_attribute("velocity", theta_vel)
            #theta_m.write_attribute("acceleration", theta_acc)

            ##setting up velocity of trans (depends of theta direction)
            #theta_pos = theta_m.read_attribute("position").value
            #if (theta_pos - theta) < 0:
                #trans_vel = 5 * theta_vel
            #else:
                #trans_vel = 0.5 * theta_vel
            #trans_m.write_attribute("velocity", trans_vel)

            #self._log.debug("theta_vel = %f" % theta_vel)
            #self._log.debug("2theta_vel = %f" % theta2_vel)
            #self._log.debug("trans_vel = %f" % trans_vel)
            #return (theta, theta2, trans)
        #except Exception,e:
            #self._log.error('calc_all_physical(): Exception %s'%(e))
            #theta = NaN
            #theta2 = NaN
            #trans = NaN
        #return (theta, theta2, trans)
        

    def calc_all_pseudo(self, physicals):
        theta, theta2, trans = physicals
        try:
            d = self.attributes[1]['dspacing']
        except KeyError, e:
            raise PyTango.DevFailed("dSpacing attribute is not set for energy motor")
        try:       
            theta_rad = math.radians(theta)
            theta2_rad = math.radians(theta2)
            self._log.debug("theta_rad %f",theta_rad)
            self._log.debug("theta2_rad %f",theta2_rad)            
            energy = 12.3984/(2*d*math.sin(theta_rad))    
            self._log.debug("energy %f",energy)
        except Exception,e:
            self._log.error('calc_all_pseudo(): Exception %s'%(e))
            energy = NaN
        return (energy,)

    def GetExtraAttributePar(self, axis, name):
        """Get Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to get an extra attribute
        :param name: (string) attribute name to retrieve

        :return: value of the attribute
        """
        return self.attributes[axis][name.lower()]

    def SetExtraAttributePar(self, axis, name, value):
        """Set Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to set an extra attribute
        :param name: (string) attribute name to retrieve
        :param value: an extra attribute value to be set

        """
        self.attributes[axis][name.lower()] = value


class Mad26_2thetaAngular(PseudoMotorController):
    """Angular pseudomotor for 2theta of Mad26 BL04-MSPD
    """
    class_prop = { }

    axis_attributes = {"Velocity":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE"},
                       "Acceleration":{ "Type":"PyTango.DevDouble", "R/W Type": "PyTango.READ_WRITE"}}

    pseudo_motor_roles = ("mad26ang",)
    motor_roles = ("mad26sinx",)

   
    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index-1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index-1]

    def calc_all_physical(self, pseudos):
        ang, = pseudos #[deg]
        sinx = math.tan((ang - 15) * math.pi/180) * 242.447 + 64.9634 
        return (sinx,)
        

    def calc_all_pseudo(self, physicals):
        sinx, = physicals #mm
        ang = 15-180*(math.atan((64.9634-sinx)/242.447))/math.pi
        return (ang,)

    def GetExtraAttributePar(self, axis, name):
        """Get Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to get an extra attribute
        :param name: (string) attribute name to retrieve

        :return: value of the attribute
        """
        if name.lower() == "velocity":
            sinx = taurus.Device("pd_madsinx")
            return 0.22 * sinx.read_attribute("velocity").value
        elif name.lower() == "acceleration":
            sinx = taurus.Device("pd_madsinx")
            return sinx.read_attribute("acceleration").value

    def SetExtraAttributePar(self, axis, name, value):
        """Set Energy pseudomotor extra attribute.

        :param axis: (int) axis nr to set an extra attribute
        :param name: (string) attribute name to retrieve
        :param value: an extra attribute value to be set

        """
        if name.lower() == "velocity":
            sinx = taurus.Device("pd_madsinx")
            sinx.write_attribute("velocity", value/0.23)
        elif name.lower() == "acceleration":
            sinx = taurus.Device("pd_madsinx")
            sinx.write_attribute("acceleration", value)
