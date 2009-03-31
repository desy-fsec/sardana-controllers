from PyTango import DevState
from pool import IORegisterController
import pool

class IOR:
    def __init__(self, axis):
        self.axis = axis
        self.state = None
        self.status = None
        self.dev_name = None
        self.attr_name = None
        self.dev = None
        self.value = None

class SimuIOController(IORegisterController):
    "A simulation IO Register controller. It connects to a PySignalSimulator device."
    
    class_prop = { 
        'AttributeNames' : {'Type':'PyTango.DevVarStringArray','Description':'the attribute names (full tango names). One for each channel)'}}

    predefined_values = ( "0", "Online", "1" , "Offline", "2", "Standby" )

    gender = "Simulation"
    model  = "Best"
    organization = "CELLS - ALBA"
    image = "ior_simulator.png"
    icon = "ior_simulator_icon.png"
    logo = "ALBA_logo.png"
    
    MaxDevice = 1024

    def __init__(self,inst,props):
        IORegisterController.__init__(self, inst, props)
        self.iors = {}
        
    def AddDevice(self, axis):
        if axis > self.MaxDevice:
            raise Exception("Invalid axis %d" % axis)
        if axis > len(self.AttributeNames):
            raise Exception("No attribute name for axis %d" % axis)
        attr_name = self.AttributeNames[axis-1]
        if attr_name.count('/') != 3:
            raise Exception("Invalid attribute name '%s' for axis %d" % (attr_name,axis))
        
        ior = IOR(axis)
        ior.name = attr_name
        ior.dev_name, sep, ior.attr_name = attr_name.rpartition('/')
        ior.dev = pool.PoolUtil().get_device(self.inst_name, ior.dev_name)

        self.iors[axis] = ior
        
    def DeleteDevice(self, axis):
        ior = self.iors.get(axis)
        if not ior:
            self._log.error("Invalid axis %d" % axis)
            return
        del self.iors[axis]
    
    def StateOne(self, axis):
        ior = self.iors[axis]
        return (ior.dev.state(), ior.dev.status())

    def PreReadAll(self):
        pass

    def PreReadOne(self, axis):
        ior = self.iors.get(axis)
        if not ior:
            self._log.error("Invalid axis %d" % axis)
            return
        ior.value = None

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        ior = self.iors.get(axis)
        if ior is None:
            msg = "Invalid axis %d" % axis
            self._log.error(msg)
            raise Exception(msg)
        ior.value = ior.dev.read_attribute(ior.attr_name).value
        return ior.value

    def WriteOne(self, axis, value):
        ior = self.iors.get(axis)
        if not ior:
            msg = "Invalid axis %d" % axis
            self._log.error(msg)
            raise Exception(msg)
        ior.dev.write_attribute(ior.attr_name, value)
        return ior.value

    def GetExtraAttributePar(self, axis, name):
        ior = self.iors[axis]
        return getattr(ior, name)

    def SetExtraAttributePar(self, axis, name, value):
        ior = self.iors[axis]
        setattr(ior, name, value)
        
    def SendToCtrl(self, in_data):
        return "Adios"

if __name__ == "__main__":
    obj = SimuIOController('test')

