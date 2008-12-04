import pool
from pool import MotorController

class Motor:
    def __init__(self,axis):
        self.axis = axis
        self.pos = None
        self.mv = None
        self.state = None
        self.switchstate = None

class SimuMotorController(MotorController):
    """This class represents a motor controller that connects to a Tango
       Device of class SimuMotorCtrl"""
       
    ctrl_features = ['Home_speed','Home_acceleration']

    class_prop = {'DevName':{'Type':'PyTango.DevString','Description':'The ctrl simulator Tango device name'}}

    gender = "Simulation"
    model  = "Best"
    organization = "CELLS - ALBA"
    image = "motor_simulator.png"
    icon = "motor_simulator_icon.png"
    logo = "ALBA_logo.png"

    MaxDevice = 1024
    
    def _getMotorCtrl(self):
        if not self._dp:
            self._dp = pool.PoolUtil().get_device(self.inst_name, self.DevName)
        return self._dp
    
    def __init__(self, inst, props):
        MotorController.__init__(self, inst, props)
        self.m = {}
        self._dp = None
        self._mvBuff = None

    def AddDevice(self,axis):
        if axis > self.MaxDevice:
            raise Exception("Invalid axis %d" % axis)
        self.m[axis] = Motor(axis)
            
    def DeleteDevice(self,axis):
        m = self.m.get(axis)
        if not m:
            raise Exception("Invalid axis %d" % axis)
        del self.m[axis]
    
    def PreStateAll(self):
        for m in self.m.values():
            m.state, m.switchstate = None, None
            
    def StateAll(self):
        for m in self.m.values():
            m.state, m.switchstate = self._getMotorCtrl().command_inout("GetAxeStatus",m.axis)
            
    def StateOne(self,axis):
        m = self.m[axis]
        return (int(m.state), m.switchstate)

    def PreReadAll(self):
        pass

    def PreReadOne(self,axis):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self,axis):
        res = self._getMotorCtrl().command_inout("GetAxePosition", axis)
        return res
    
    def PreStartAll(self):
        self._mvBuff = []

    def PreStartOne(self,axis,pos):
        return True

    def StartOne(self,axis,pos):
        self._mvBuff.append((axis,pos))
        
    def StartAll(self):
        #indexes = [ str(x) for x,y in self._mvBuff ]
        #positions = [ y for x,y in self._mvBuff ]
        #self._getMotorCtrl().command_inout("SetAxePosition", [positions, indexes])
        for axis,pos in self._mvBuff:
            self._getMotorCtrl().command_inout("SetAxePosition", [[pos], [axis]])
        
    def SetPar(self, axis, par_name, value):
        d_in = [[value],[str(axis)]]
        if par_name == "Acceleration":
            self._getMotorCtrl().command_inout("SetAxeAcceleration", d_in)
        elif par_name == "Velocity":
            self._getMotorCtrl().command_inout("SetAxeVelocity", d_in)
        elif par_name == "Base_rate":
            self._getMotorCtrl().command_inout("SetAxeBase_rate", d_in)
        elif par_name == "Deceleration":
            self._getMotorCtrl().command_inout("SetAxeDeceleration", d_in)
        elif par_name == "Step_per_unit":
            pass
        elif par_name == "Backlash":
            pass
            
    def GetPar(self, axis, par_name):
        if par_name == "Acceleration":
            return self._getMotorCtrl().command_inout("GetAxeAcceleration", axis)
        elif par_name == "Velocity":
            return self._getMotorCtrl().command_inout("GetAxeVelocity", axis)
        elif par_name == "Base_rate":
            return self._getMotorCtrl().command_inout("GetAxeBase_rate", axis)
        elif par_name == "Deceleration":
            return self._getMotorCtrl().command_inout("GetAxeDeceleration", axis)
        elif par_name == "Backlash":
            return 11.111
        

    def GetExtraAttributePar(self,axis,name):
        pass
    
    def SetExtraAttributePar(self,axis,name,value):
        pass

    def AbortOne(self,axis):
        self._getMotorCtrl().command_inout("Abort", axis);
        
    def StopOne(self,axis):
        pass

    def DefinePosition(self, axis, position):
        self._getMotorCtrl().command_inout("LoadAxePosition",[[position],[str(axis)]])

