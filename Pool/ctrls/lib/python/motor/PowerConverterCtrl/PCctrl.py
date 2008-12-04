import PyTango
import pool
from pool import MotorController
import array
import sys

class PowerConverterController(MotorController):
    """This class is the Tango Sardana motor controller for the Tango Power Converter device. The common 'axis' in a classical motor, here is the current in the PowerConverter"""

    #The controller have common for all the axis
    class_prop = {'devList':{'Description' : 'List of the PowerConverters Tango device names','Type' : 'PyTango.DevVarStringArray'}}

    #Each 'axis' ('PowerConverter') have a particular 'ctrl_extra_attributes'
    #ctrl_extra_attributes = { 'TangoDevice':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE','Description':'Tango-ds name.'}}

    gender = "PowerConverter"
    model = "Simulator"
    organization = "CELLS - ALBA"

    MaxDevice = 3

    def __init__(self,inst,props):
        MotorController.__init__(self,inst,props)
        print "[PowerConverterController]",self.inst_name,": In __init__ method for instance",inst," with the properties",props
        #print "[PowerConverterController]",self.inst_name,": class_prop:",self.class_prop
        #print "[PowerConverterController]",self.inst_name,": Extra attrs:",self.ctrl_extra_attributes
        self.powerConverterProxys = {}

    def getPowerConverter(self, axis, raiseOnConnError=True):
        proxy = None
        devName = self.devList[axis-1]
        try:
            proxy = self.powerConverterProxys.get(axis)
            if not proxy:
                proxy = pool.PoolUtil().get_device(self.inst_name, devName)
                self.powerConverterProxys[axis] = proxy
        except:
            raise
        
        try:
            proxy.ping()
        except Exception, e:
            if raiseOnConnError: 
                raise e
            else:
                print "[PowerConverterController]",self.inst_name,": PowerConverter '%s' is not available" % devName
        return proxy

    def removePowerConverter(self, axis):
        del self.powerConverterProxys[axis]

    def AddDevice(self,powerConverter):
        print "[PowerConverterController]",self.inst_name,": In AddDevice method for powerConverter",powerConverter-1
        #print "[PowerConverterController] powerConverter",powerConverter,"responds to the Tango device:",self.devList[powerConverter],"."
        if powerConverter <= len(self.devList):
            raise Exception("Axis out of range")
        
        
        index = powerConverter-1
        devName = self.devList[index]
        
        if devName:
            proxy = self.getPowerConverter(powerConverter, raiseOnConnError = False)
            print "[PowerConverterController]",self.inst_name,": In AddDevice method added",self.powerConverterProxys[axis].dev_name()
        else:
            print "[PowerConverterController]",self.inst_name,": In AddDevice method, no element in class_prop"
            raise Exception("Axis name not valid in devList property")

    def DeleteDevice(self,powerConverter):
        print "[PowerConverterController]",self.inst_name,": In DeleteDevice method for powerConverter",powerConverter-1
        self.removePowerConverter(powerConverter)

    def StateOne(self,powerConverter):
        #print "[PowerConverterController]",self.inst_name,": In StateOne method for powerConverter",powerConverter-1
        #TODO: ask the PowerConverter, that this axis corresponds, the device status
        pc = self.getPowerConverter(powerConverter)
        state = pc.read_attribute("state").value
        switchstate = 0
        return (int(state), switchstate)

    def PreReadAll(self):
        print "[PowerConverterController]",self.inst_name,": In PreReadAll method"
        #nothing to do

    def PreReadOne(self,powerConverter):
        print "[PowerConverterController]",self.inst_name,": In PreReadOne method for powerConverter",powerConverter-1
        #nothing to do

    def ReadAll(self):
        print "[PowerConverterController]",self.inst_name,": In ReadAll method"
        #nothing to do

    def ReadOne(self,powerConverter):
        print "[PowerConverterController]",self.inst_name,": In ReadOne method for powerConverter",powerConverter-1
        #Read the specific current that the PowerConverter supplies related to this axis corresponds.
        attr = self.getPowerConverter(powerConverter).read_attribute('Current')
        return attr.value

    def PreStartAll(self):
        print "[PowerConverterController]",self.inst_name,": In PreStartAll method"
        #nothing to do

    def PreStartOne(self,powerConverter,current):
        print "[PowerConverterController]",self.inst_name,": In PreStartOne method for powerConverter",powerConverter-1," with current",current
        #nothing to do
        return True

    def StartOne(self,powerConverter,current):
        print "[PowerConverterController]",self.inst_name,": In StartOne method for powerConverter",powerConverter-1," with current",current
        #Set an specific current value to the Powerconverter that this axis represents.
        self.getPowerConverter(powerConverter).write_attribute('Current',current)

    def StartAll(self):
        print "[PowerConverterController]",self.inst_name,": In StartAll method"

    def SetPar(self,powerConverter,name,value):
        print "[PowerConverterController]",self.inst_name,": In SetPar method for powerConverter",powerConverter-1," name=",name," value=",value
        #nothing to do

    def GetPar(self,powerConverter,name):
        print "[PowerConverterController]",self.inst_name,": In GetPar method for powerConverter",powerConverter-1," name=",name
        #nothing to do
        return 0

    def GetExtraAttributePar(self,powerConverter,name):
        print "[PowerConverterController]",self.inst_name,": In GetExtraAttributePar method for powerConverter",powerConverter-1," name=",name
        return 0

    def SetExtraAttributePar(self,powerConverter,name,value):
        print "[PowerConverterController]",self.inst_name,": In SetExtraAttributePar method for powerConverter",powerConverter-1," name=",name," value=",value

    def AbortOne(self,powerConverter):
        print "[PowerConverterController]",self.inst_name,": In Abort for powerConverter",powerConverter-1

    def StopOne(self,powerConverter):
        print "[PowerConverterController]",self.inst_name,": In StopOne for powerConverter",powerConverter-1
        #nothing to do

    def DefinePosition(self,powerConverter, current):
        print "[PowerConverterController]",self.inst_name,": In DefinePosition for powerConverter",powerConverter-1," current=",current
        #TODO: Set an specific current value to the Powerconverter that this axis represends.

    def __del__(self):
        print "[PowerConverterController]",self.inst_name,": Exiting...",
        #nothing to do
        print "[DONE]"
