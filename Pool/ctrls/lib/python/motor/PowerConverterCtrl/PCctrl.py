# -*- coding: utf-8 -*-
import PyTango
import pool
from pool import MotorController
import array
import sys

TANGO_DEV = 'TangoDevice'

class PowerConverterController(MotorController):
    """This class is the Tango Sardana motor controller for the 
       Tango Power Converter device. The common 'axis' in a classical motor, 
       here is the current in the PowerConverter"""

    
    #Each 'axis' ('PowerConverter') have a particular 'ctrl_extra_attributes'
    ctrl_extra_attributes = { TANGO_DEV:{'Type':'PyTango.DevString',
                                         'R/W Type':'PyTango.READ_WRITE',
                                         'Description':'Tango-ds name.'}}

    gender = "PowerConverter"
    model = "Simulator"
    organization = "CELLS - ALBA"
    devList = None

    MaxDevice = 1024

    def __init__(self,inst,props):
        MotorController.__init__(self, inst, props)
        self.extra_attributes = {}
        self.powerConverterProxys = {}
        self.MotionCmdFlag = {}

    def getPowerConverter(self, axis, raiseOnConnError=True):
        proxy = self.powerConverterProxys.get(axis)
        if not proxy:
            devName = self.extra_attributes[axis][TANGO_DEV]
            if devName is not None:
                proxy = pool.PoolUtil().get_device(self.inst_name, devName)
                self.powerConverterProxys[axis] = proxy
                if proxy is None and raiseOnConnError:
                    raise Exception("Proxy for '%s' could not be created" % devName)
        if False:
          try:
              proxy.ping()
          except Exception, e:
              if raiseOnConnError: 
                  raise e
              else:
                  msg = "PowerConverter '%s' is not available" % devName
                  self._log.error(msg)
        return proxy

    def AddDevice(self, axis):
        self.extra_attributes[axis] = {}
        self.extra_attributes[axis][TANGO_DEV] = None
        self.MotionCmdFlag[axis] = False

    def DeleteDevice(self, axis):
        if self.MotionCmdFlag.has_key(axis):
            del self.MotionCmdFlag[axis]
        if self.powerConverterProxys.has_key(axis):
            del self.powerConverterProxys[axis]
        if self.extra_attributes.has_key(axis):
            del self.extra_attributes[axis]

    def StateOne(self, axis):
        try:
            pc = self.getPowerConverter(axis)
            if self.MotionCmdFlag[axis]:
                curr,setp = pc.read_attributes(['Current','currentsetpoint'])
                if int(curr.value) == int(setp.value):
                    #it mean that this was moving and now is too close to the 
                    #final position, and can be assumed that the movement is done
                    self.MotionCmdFlag[axis] = False
                    state = PyTango.DevState.ON
                else:
                    state = PyTango.DevState.MOVING
            else:
                state = PyTango.DevState.ON
            return state, "OK", 0
        except Exception,e:
            return PyTango.DevState.ALARM, str(e), 0
        

    def ReadOne(self, axis):
        #Read the specific current that the PowerConverter supplies related to this axis corresponds.
        pc = self.getPowerConverter(axis)
        position = pc.read_attribute('Current').value
        return position
    def StartOne(self, axis, current):
        pc = self.getPowerConverter(axis)
        pc.write_attribute('CurrentSetpoint', current)
        #force to change to moving when this motion starts.
        self.MotionCmdFlag[axis] = True

    def SetPar(self, axis, name, value):
        #print "[PowerConverterController]",self.inst_name,": In SetPar method for powerConverter",axis," name=",name," value=",value
        pass

    def GetPar(self, axis, name):
        #print "[PowerConverterController]",self.inst_name,": In GetPar method for powerConverter",axis," name=",name
        if name.lower()=='velocity':
            try:
                dp = self.getPowerConverter(axis)
                if not dp == None:
                    return dp.read_attribute('CurrentRamp').value
            except Exception,e:
                self._log.error("Exception on attr %s of magnet %s: %s"%(name,dp.name(),e))
                return float('nan')

    def GetExtraAttributePar(self, axis, name):
        if name in [TANGO_DEV,]:
            return self.extra_attributes[axis][name]

    def SetExtraAttributePar(self, axis, name, value):
        if name in [TANGO_DEV,]:
            self.extra_attributes[axis][name] = value

    def AbortOne(self, axis):
        pc = self.getPowerConverter(axis)
        self.MotionCmdFlag[axis] = False
        current = pc.read_attribute('Current')
        pc.write_attribute('CurrentSetpoint', current.value)

    def StopOne(self, axis):
        #print "[PowerConverterController]",self.inst_name,": In StopOne for powerConverter",axis
        pass

    def DefinePosition(self, axis, current):
        raise Exception('not implemented')
        pc = self.getPowerConverter(axis)
        # assumes that the power converter has reached its setpoint        
        setp = pc.read_attribute('CurrentSetpoint')
        # the calculation depends on wether the CurrentOffset
        # enters 
        # in particular for setp=0.0 offset = current
        # for setp=0.0 and current=2.0 
        off = pc.read_attribute('CurrentOffset')
        off += setp-0.0
        pc.write_attribute('CurrentOffset', current-setp)

    
