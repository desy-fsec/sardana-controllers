# -*- coding: utf-8 -*-
import PyTango
import pool
from pool import MotorController
import array
import sys

TANGO_DEV = 'TangoDevice'

class PowerConverterController(MotorController):
    """This class is the Tango Sardana motor controller for the Tango Power Converter device. The common 'axis' in a classical motor, here is the current in the PowerConverter"""

    
    #Each 'axis' ('PowerConverter') have a particular 'ctrl_extra_attributes'
    ctrl_extra_attributes = { TANGO_DEV:{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE','Description':'Tango-ds name.'}}

    gender = "PowerConverter"
    model = "Simulator"
    organization = "CELLS - ALBA"
    devList = None

    MaxDevice = 1024

    def __init__(self,inst,props):
        MotorController.__init__(self, inst, props)
        self.extra_attributes = {}
        self.powerConverterProxys = {}

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

    def DeleteDevice(self, axis):
        if self.powerConverterProxys.has_key(axis):
            del self.powerConverterProxys[axis]
        if self.extra_attributes.has_key(axis):
            del self.extra_attributes[axis]

    def StateOne(self, axis):
        try:
            pc = self.getPowerConverter(axis)
            state = pc.read_attribute("State").value
            return state, "OK", 0
        except Exception,e:
            return PyTango.DevState.ALARM, str(e), 0
        

    def ReadOne(self, axis):
        #Read the specific current that the PowerConverter supplies related to this axis corresponds.
        return self.getPowerConverter(axis).read_attribute('Current').value

    def StartOne(self, axis, current):
        self.getPowerConverter(axis).write_attribute('CurrentSetpoint', current)

  
    def SetPar(self, axis, name, value):
        #print "[PowerConverterController]",self.inst_name,": In SetPar method for powerConverter",axis," name=",name," value=",value
        pass

    def GetPar(self, axis, name):
        #print "[PowerConverterController]",self.inst_name,": In GetPar method for powerConverter",axis," name=",name
        if name.lower()=='velocity':
            dp = self.getPowerConverter(axis)
            return dp.read_attribute('CurrentRamp').value

    def GetExtraAttributePar(self, axis, name):
        if name in [TANGO_DEV,]:
            return self.extra_attributes[axis][name]

    def SetExtraAttributePar(self, axis, name, value):
        if name in [TANGO_DEV,]:
            self.extra_attributes[axis][name] = value

    def AbortOne(self, axis):
        pc = self.getPowerConverter(axis)
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

    
