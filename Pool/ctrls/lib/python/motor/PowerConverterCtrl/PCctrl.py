# -*- coding: utf-8 -*-
import PyTango
import pool
from pool import MotorController
import array
import sys

# ????: What does setPar do?


class PowerConverterController(MotorController):
    """This class is the Tango Sardana motor controller for the Tango Power Converter device. The common 'axis' in a classical motor, here is the current in the PowerConverter"""

    # The controller have common for all the axis
    class_prop = {'device_list':{'Description' : 'List of the PowerConverters Tango device names','Type' : 'PyTango.DevVarStringArray'}}

    #Each 'axis' ('PowerConverter') have a particular 'ctrl_extra_attributes'
    #ctrl_extra_attributes = { 'TangoDevice':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE','Description':'Tango-ds name.'}}

    gender = "PowerConverter"
    model = "Simulator"
    organization = "CELLS - ALBA"
    devList = None

    MaxDevice = 10**87

    def __init__(self,inst,props):
        MotorController.__init__(self, inst, props)
        self.powerConverterProxys = {}

    def getPowerConverter(self, axis, raiseOnConnError=True):
        proxy = self.powerConverterProxys.get(axis)
        devName = self.devList[axis-1]
        if not proxy:
            proxy = pool.PoolUtil().get_device(self.inst_name, devName)
            self.powerConverterProxys[axis] = proxy

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
        pass #< nothing to be done :-)

    def DeleteDevice(self, axis):
        del self.powerConverterProxys[axis]

    def StateOne(self,powerConverter):
        pc = self.getPowerConverter(powerConverter)
        state = int(pc.read_attribute("state").value)
        switchstate = 0
        return (state, switchstate)

    def ReadOne(self, axis):
        #Read the specific current that the PowerConverter supplies related to this axis corresponds.
        return self.getPowerConverter(axis).read_attribute('Current').value

    def StartOne(self,powerConverter,current):
        self.getPowerConverter(powerConverter).write_attribute('CurrentSetpoint',current)

  
    def SetPar(self,powerConverter,name,value):
        print "[PowerConverterController]",self.inst_name,": In SetPar method for powerConverter",powerConverter-1," name=",name," value=",value
        #nothing to do	

    def GetPar(self, axis, name):
        print "[PowerConverterController]",self.inst_name,": In GetPar method for powerConverter",powerConverter-1," name=",name
        #nothing to do
	if name.lower()=='velocity':
	  return self.getPowerConverter(axis).read_attribute('CurrentRamp').value

    def GetExtraAttributePar(self, powerConverter, name):
        return 0

    def SetExtraAttributePar(self, powerConverter, name, value):
        pass

    def AbortOne(self, pc_idx):
        pc = self.getPowerConverter(pc_idx)
        current = pc.read_attribute('Current')
        pc.write_attribute('CurrentSetpoint', current)

    def StopOne(self,powerConverter):
        print "[PowerConverterController]",self.inst_name,": In StopOne for powerConverter",powerConverter-1
        #nothing to do

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

    
