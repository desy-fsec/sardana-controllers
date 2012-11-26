##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
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

#import time
#import threading
#import traceback
#from math import pow, sqrt

from sardana import State  #sustituye a   import PyTango
from sardana.pool.controller import MotorController

from SpecClient import SpecConnectionsManager
from SpecClient import SpecMotor
from SpecClient.Spec import Spec
from time import sleep


class Motor():
    def __init__(self):
        self.name = None
        self.motor = None
        self.session = None


class SpecMotorController(MotorController):
    """This class represents a basic, Spec motor controller."""
    gender = "Simulation"
    model  = "Basic"
    organization = "CELLS - ALBA && ESRF"
#    image = "dummy_motor_ctrl.png"
    logo = "ALBA_logo.png"


    ctrl_properties= { 'spec' : { 'Type' : 'DevString', 'Description' : 'Spec session to connect to (host:port_or_session_name string)' } }
    axis_attributes = { 'specmotorname' : { 'type' : str, 'Description' : 'Spec motor name' },
                        'session' : { 'type' : str, 'Description' : 'Spec session' } } 


    MaxDevice = 1024
# --------------------------------------------------------------------------
# Init() 
# --------------------------------------------------------------------------  
    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.m = self.MaxDevice*[Motor,]
        # connect to spec ;
        # need to use a thread to process socket events, because there is no way to
        # interface with an existing loop AFAIK
        self.specConman = SpecConnectionsManager.SpecConnectionsManager(pollingThread = True, also_dispatch_events = True)
        # establish connection with spec
        self.specCon = self.specConman.getConnection(self.spec)
        self.specM = Spec(self.spec)
        #self._lowerLS = float("-inf")
        #self._upperLS = float("+inf")

# --------------------------------------------------------------------------
# AddDevice/DelDevice() 
# --------------------------------------------------------------------------    
    def AddDevice(self,axis):
        if len(self.m) < axis:
            self._log.error("Invalid axis %d" % axis)
            raise Exception("Invalid axis %d" % axis)

    def DeleteDevice(self, axis):
#        if len(self.m) < axis or not self.m[axis]:
#            self._log.error("Invalid axis %d" % axis)
#            raise Exception("Invalid axis %d" % axis)
        self.m[axis].name = None
        self.m[axis].motor = None
        self.m[axis].session = None
# --------------------------------------------------------------------------
# StateOne()
# --------------------------------------------------------------------------    
    def StateOne(self, axis):
        state = State.On
        status = "Undefined"
        switchstate = 0
        if not self.specCon.isSpecConnected():
            state = State.Disable
            status = "Disable"
        else:
            s =  self.m[axis].motor.getState()
            if (SpecMotor.MOVING == s):
                state =  State.Moving
                status = "Motor is moving"
            elif (SpecMotor.UNUSABLE == s):
                state =  State.Fault
                status = "Motor is powered" 
            elif (SpecMotor.READY == s):
                state =  State.On
                status = "Motor is on" 
            elif (SpecMotor.MOVESTARTED == s):
                state =  State.Moving
                status = "Motor is ready" 
            elif (SpecMotor.ONLIMIT == s):
                state =  State.Alarm
                status = "Motor HW is in alarm" 
                #self.HomeLimitSwitch (not exists) | self.LowerLimitSwitch (2) | self.UpperLimitSwitch (4)
                limit_switches =  self.m[axis].motor.limit
                if (limit_switches==2):
                    switchstate |= MotorController.LowerLimitSwitch
                else:
                    switchstate |= MotorController.UpperLimitSwitch
            elif (SpecMotor.NOTINITIALIZED == s):
                state =  State.Disable
                status = "Motor is disable" 
        return state, status, switchstate

# --------------------------------------------------------------------------
# ReadOne() 
# -------------------------------------------------------------------------- 
    def ReadOne(self,axis):
#        if len(self.m) < axis or not self.m[axis]:
#            self._log.error("Invalid axis %d" % axis)
#            raise Exception("Invalid axis %d" % axis)
        return self.m[axis].motor.getPosition()

# --------------------------------------------------------------------------
# StartOne/StopOne() 
# --------------------------------------------------------------------------     
    def PreStartOne(self, axis, pos):
        #Motor[axis].has_power()
        return True

    def StartOne(self, axis, pos):
#        if len(self.m) < axis or not self.m[axis]:
#            self._log.error("Invalid axis %d" % axis)
#            raise Exception("Invalid axis %d" % axis)
        self.m[axis].motor.move(pos)
#        while (SpecMotor.MOVESTARTED == self.m[axis].getState()):
#            self.StateOne(axis)
#            self.ReadOne(axis)
          
    def AbortOne(self, axis):
#        if len(self.m) < axis or not self.m[axis]:
#            self._log.error("Invalid axis %d" % axis)
#            raise Exception("Invalid axis %d" % axis)
        self.m[axis].motor.stop()   


    def StopOne(self, axis):
        self.AbortOne(axis)

    def PreStartAll(self):
        pass

    def StartAll(self): 
        pass

    def AbortAll(self):
        pass

# --------------------------------------------------------------------------
# SetAxisPar/GetAxisPar() 
# --------------------------------------------------------------------------    
#    def SetAxisPar(self, axis, name, *args):
#        name = name.lower()
#        if len(self.m) < axis or not self.m[axis]:
#            self._log.error("Invalid axis %d" % axis)
#            return
#        if name == "velocity" and len(args)>0:
#            self.spec_motor.setParameter("slew_rate", args[0])
#        elif name in ("acceleration", "deceleration")  and len(args)>0:
#            return self.spec_motor.setParameter("acceleration", args[0]) 
#        elif name == "base_rate" and len(args)>0:
#            return self.spec_motor.setParameter("base_rate", args[0])   
#        elif name == "backlash":
#            return self.spec_motor.setParameter("backlash", args[0])
#        elif name == "offset" and len(args)>0:
#            self.spec_motor.setParameter("offset",args[0])
#        elif name == "limits" and len(args)>1:
#            self.spec.chg_offset(self.spec_motor, args[0], args[1])
#        else:
#            self._log.error("Invalid parameter")     
    def SetAxisPar(self, axis, name, value):
        name = name.lower()
#        if  name in ("acceleration", "deceleration"):
#            self.m[axis].motor.setParameter("acceleration", value)
        if name == "acceleration":
            self.m[axis].motor.setParameter("acceleration", value)
        elif name == "deacceleration":
            self.m[axis].motor.setParameter("deacceleration", value)           
        elif name == "base_rate":
            self.m[axis].motor.setParameter("base_rate", value)
        elif name == "velocity":
            self.m[axis].motor.setParameter("slew_rate", value)
        elif name == "step_per_unit":
            self.m[axis].motor.setParameter("step_size", value)
        elif name == "offset":
            self.m[axis].motor.setParameter("offset", value)
        else:
            self._log.error("Invalid parameter")

    def GetAxisPar(self, axis, name):
        name = name.lower()
        if name == "velocity":         
           return self.m[axis].motor.getParameter("slew_rate")
        elif name == "acceleration":
            self.m[axis].motor.getParameter("acceleration")
        elif name == "deacceleration":
            self.m[axis].motor.getParameter("deacceleration")
        elif name == "base_rate":
            return self.m[axis].motor.getParameter("base_rate")   
        elif name == "backlash":
            return self.m[axis].motor.getParameter("backlash")
        elif name == "dial_position":
            return self.m[axis].motor.getDialPosition()
        elif name == "offset":
            return self.m[axis].motor.getOffset()
        elif name == "step_per_unit":
            return self.m[axis].motor.getParameter("step_size")
        elif name == "limits":
            return self.m[axis].motor.getLimits()
        elif name == "sign":
            return self.m[axis].motor.getSign()
        elif name == "position":
            return self.m[axis].motor.getPosition()
        elif name == "state":
            return self.m[axis].motor.getState()
        else:
            self._log.error("Invalid parameter")

# --------------------------------------------------------------------------
# SetAxisExtraPar/GetAxisExtraPar() 
# --------------------------------------------------------------------------    
    def SetAxisExtraPar(self,axis,name,value):
        if name == "specmotorname":
#            self.m[axis] = SpecMotor.SpecMotorA(value, self.spec)
            exists = 0
            nm = self.specCon.getChannel('var/MOTORS').read()
            #check motor name
            for i in range(nm):
                if self.specM.motor_mne(i)==value:
                    self.m[axis].motor = SpecMotor.SpecMotorA(value, self.spec)
                    self.m[axis].name = value
                    #self.m[axis].session = self.ctrl_properties['spec']
                    exists = 1
                    break
            if not exists:
                self.m[axis].motor = None
        if name == "session":
            self.m[axis].session = value
        #else:
        #    self.m[axis].motor = None
                    

    def GetAxisExtraPar(self, axis, name):
#        if len(self.m) < axis or not self.m[axis].motor:
#            self._log.error("Invalid axis %d" % axis)
#            raise Exception("Invalid axis %d" % axis)
        if name == "specmotorname":
            return self.m[axis].name
        if name == "session":
            if self.m[axis].session is None:
                return "Unknow"
            else:
                return self.m[axis].session



