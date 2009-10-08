from PyTango import DevState, DevFailed
from pool import ZeroDController
import pool

class Channel0D:
    
    def __init__(self, axis):
        self.axis = axis
        self.state = None
        self.status = None
        self.dev_name = None
        self.attr_name = None
        self.dev = None
        self.value = None

class Simu0DController(ZeroDController):
    "A simulation 0D controller. It connects to a PySignalSimulator device."
    
    class_prop = { 
        'AttributeNames' : {'Type':'PyTango.DevVarStringArray','Description':'the attribute names (full tango names). One for each channel)'}}

    gender = "Simulation"
    model  = "Best"
    organization = "CELLS - ALBA"
    image = "motor_simulator.png"
    icon = "motor_simulator_icon.png"
    logo = "ALBA_logo.png"
    
    MaxDevice = 1024

    def __init__(self,inst,props):
        ZeroDController.__init__(self, inst, props)
        self.channels = {}
        
    def AddDevice(self, axis):
        if axis > self.MaxDevice:
            raise Exception("Invalid axis %d" % axis)
        if axis > len(self.AttributeNames):
            raise Exception("No attribute name for axis %d" % axis)
        attr_name = self.AttributeNames[axis-1]
        if attr_name.count('/') != 3:
            raise Exception("Invalid attribute name '%s' for axis %d" % (attr_name,axis))
        
        c = Channel0D(axis)
        c.name = attr_name
        c.dev_name, sep, c.attr_name = attr_name.rpartition('/')
        c.dev = pool.PoolUtil().get_device(self.inst_name, c.dev_name)

        self.channels[axis] = c
        
    def DeleteDevice(self, axis):
        c = self.channels.get(axis)
        if not c:
            self._log.error("Invalid axis %d" % axis)
            return
        del self.channels[axis]

    def PreStateAll(self):
        for c in self.channels.values():
            c.state = None
            
    def StateAll(self):
        for c in self.channels.values():
            try:
                c.dev.ping()
                c.state = c.dev.state()
                c.status = str(c.state)
            except DevFailed, df:
                c.state = DevState.FAULT
                c.status = df[0].desc
            except Exception,e:
                c.state = DevState.FAULT
                c.status = str(e)
            
    def StateOne(self, axis):
        c = self.channels[axis]
        return (c.state, c.status)

    def PreReadAll(self):
        pass

    def PreReadOne(self, axis):
        c = self.channels.get(axis)
        if not c:
            self._log.error("Invalid axis %d" % axis)
            return
        c.value = None

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        c = self.channels.get(axis)
        if not c:
            msg = "Invalid axis %d" % axis
            self._log.error(msg)
            raise Exception(msg)
        c.value = c.dev.read_attribute(c.attr_name).value
        return c.value

    def GetExtraAttributePar(self, axis, name):
        c = self.channels[axis]
        return getattr(c, name)

    def SetExtraAttributePar(self, axis, name, value):
        c = self.channels[axis]
        setattr(c, name, value)
        
    def SendToCtrl(self, in_data):
        return "Adios"

if __name__ == "__main__":
    obj = ZeroDController('test')

