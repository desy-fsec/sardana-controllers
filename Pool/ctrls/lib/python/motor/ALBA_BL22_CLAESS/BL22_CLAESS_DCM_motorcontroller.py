#!/usr/bin/env python2.5

#############################################################################
##
## file :    PmacCtrl.py
##
## description : 
##
## project :    miscellaneous/PoolControllers/MotorControllers
##
## developers history: zreszela
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
from pool import PoolUtil
from PmacCtrl import PmacController

class CLAESS_DCM_PmacController(PmacController):
    """This class is a Sardana motor controller for DCM of CLAESS beamline at ALBA.
        DCM comprises many motors, and two of them: Bragg and 2ndXtalPerpendicular are controlled
        from TurboPmac Motor Controller"""
        
    MaxDevice = 2
    class_prop = {'VCMPitchName':{'Type' : 'PyTango.DevBoolean', 'Description' : 'VCM pitch pseudomotor'}}
    class_prop.update(PmacController.class_prop)
    
    ctrl_extra_attributes = {"EnergyMotion":{ "Type":"PyTango.DevBool", "R/W Type": "PyTango.READ_WRITE"}}
    ctrl_extra_attributes.update(PmacController.ctrl_extra_attributes) 
    
    def __init__(self,inst,props):
        PmacController.__init__(self,inst,props)
        self.pmacEth = PyTango.DeviceProxy(self.DevName)
        self.vcm_pitch  = PoolUtil.get_motor(self, self.VCMPitchName)
        self.superklass = PmacController 
        
    def AddDevice(self, axis):
        self.superklass.AddDevice(self, axis)
        if axis == 1:
            self.attributes[axis]["EnergyMotion"]= bool(0)
            self.energyMotion = False

    def DeleteDevice(self, axis):
        pass
    
    def SetExtraAttributePar(self, axis, name, value):
        """ Set Pmac axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        
        if name == "EnergyMotion":
            if axis == 1:
                self.attributes[axis][name]=value
                self.energyMotion = value
            else:
                PyTango.Except.throw_exception("CLAESS_DCM_PmacController.SetExtraAttributePar()", "Error setting " + name + ", this attribute is foreseen only for Bragg motor", "SetExtraAttributePar()")
        else:
            self.superklass.SetExtraAttributePar(self, axis, name, value)
         
    
    def StartAll():
        if len(self.startMultiple) > 1:
            PyTango.Except.throw_exception("CLAESS_DCM_PmacController.StartAll()", 
                                           "Error trying to start motion, this controller doesn't allow to use motors by Sardana pseudomotors composed from more than one motor",
                                            "StartAll()")
        if self.energyMotion:
            vcm_pitch_mrad = self.vcm_pitch.read_attribute("Position")
            #@todo: replace formula for exitOffset
            exitOffset = 2,5 * vcm_pitch_mrad
            bragg = self.startMultiple[1]
            self.pmacEth.command_inout("SetPVariable", [100,bragg])
            self.pmacEth.command_inout("SetPVariable", [101,exitOffset])
            self.pmacEth.command_inout("RunMotionProgram", 1)
        else:
            self.superklass.StartAll()
            
    
    
    
        

class CLAESS_DCMEnergyController(MotorController):
    """This class is the Tango Sardana motor controller for the energy pseudo motor which requires controlling of 
    two motors comprised by DCM: bragg and 2ndXtalPerpendicular.
    Silicon property has to be choosen between si111 or si311"""
    
    MaxDevice = 1
    class_prop = {'DevName':{'Type' : 'PyTango.DevString', 'Description' : 'Device name of the PmacEth DS'},
                  'Silicon':{'Type' : 'PyTango.DevString', 'Description' : 'Device name of the PmacEth DS'}}
    
    hc = 12398.419 #eV *Angstroms
    si111 = 3.1354161 #Angstroms            
    si311 =  1.637418 #Angstroms
    
    def __init__(self,inst,props):
        MotorController.__init__(self,inst,props)
        self.pmacEth = PyTango.DeviceProxy(self.DevName)
        silicon = self.Silicon.lower() 
        if silicon == "si111":
            self.d = self.si111       
        elif silicon == "si311":
            self.d = self.si311
        else:
            PyTango.Except.throw_exception("Cannot create controller, Silicon property has to be either Si111 or Si311.")
        self.exitHeight = 10
        
        
    def AddDevice(self, axis):
        pass

    def DeleteDevice(self, axis):
        pass
    
    def StateOne(self, axis):
        switchstate = 0
        inPosition = self.pmacEth.command_inout("GetPVariable", 197)
        if inPosition == 0.0:
            state = PyTango.DevState.MOVING
            status = "DCM is doing an energy movement."
        elif inPosition == 1.0:
            state = PyTango.DevState.ON
            status = "DCM in position."
        else:
            state = PyTango.DevState.UNKNOWN
            status = "DCM state could not be resolved."
        return (state, status, switchstate)
            
    def ReadOne(self, axis):
        
        
        

    def StartOne(self, axis, position):
        energy = position #eV
        try:
            bragg = math.asin(self.hc/2/self.d/energy)
            perp = self.exitHeight/2/math.cos(bragg)
        except ValueError:
            PyTango.Except.throw_exception("Desired energy position is out of bounds.")
        # CMDPosInDEG - P100
        self.pmacEth.command_inout("SetPVariable", [100, bragg])
        #FixedExitOffset - P101
        self.pmacEth.command_inout("SetPVariable", [101, perp])
        #DmdPosOutOfBounds - P107
        outOfBounds = self.pmacEth.command_inout("GetPVariable", 107)
        if outOfBounds == 1.0:
            PyTango.Except.throw_exception("Desired energy position is out of bounds.")
        self.pmacEth.command_inout("OnlineCmd", "&1a")
        self.pmacEth.command_inout("RunMotionProgram", 1)
        
    def SetPar(self, axis, name, value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        pass
    
    def GetPar(self, axis, name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        pass 
    
    def AbortOne(self, axis):
        pass
    
    def DefinePosition(self,powerConverter, current):
        pass
    
    def GetExtraAttributePar(self, axis, name):
        """ Get Pmac axis particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        pass
    
    def SetExtraAttributePar(self, axis, name, value):
        """ Set Pmac axis particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        pass
        
    def SendToCtrl(self,cmd):
        """ Send custom native commands.
        @param string representing the command
        @return the result received
        """
        cmd_splitted = cmd.split()
        if len(cmd_splitted) == 1: 
            self.pmacEth.command_inout(cmd)
        else:
            if len(cmd_splitted) == 2:
                if cmd_splitted[0].lower() == "enableplc":
                    self.pmacEth.command_inout("enableplc",int(cmd_splitted[1]))
                if cmd_splitted[0].lower() =="getmvariable":
                    return str(self.pmacEth.command_inout("getmvariable",int(cmd_splitted[1])))
            elif len(cmd_splitted) > 2:
                if cmd_splitted[0].lower() == "setpvariable":
                    array = [float(cmd_splitted[i]) for i in range(1, len(cmd_splitted))]
                    self.pmacEth.command_inout("setpvariable", array)

