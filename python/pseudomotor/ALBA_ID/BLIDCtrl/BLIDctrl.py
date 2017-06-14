# -*- coding: utf-8 -*-
import PyTango
from sardana import pool
from sardana.pool.controller import MotorController
import array
import sys

TANGO_DEV = 'TangoDevice'

class Motor:
    def __init__(self,axis):
        self.axis = axis
        self.state = None
        self.position = None
        self.switchstate = 0
        #self.mv = None
        #self.step_per_unit = 1
        #self.backlash = 0
        

class BLIDControllerM(MotorController):

    axis_attributes = { TANGO_DEV:{'Type':'PyTango.DevString',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'Description':'Tango-ds name.'}}

    gender = "BLID"
    model = "Simulator"
    organization = "CELLS - ALBA"
    devList = None

    MaxDevice = 1024

 
    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.extra_attributes = {}
        self.m = {}
        self._dp = None

    def _getMotorCtrl(self, axis):
        #if not self._dp:
        devName = self.extra_attributes[axis][TANGO_DEV]
        if devName is not None:
            self._dp = pool.PoolUtil().get_device(self.inst_name, devName)
            return self._dp

    def AddDevice(self,axis):
        self.extra_attributes[axis] = {}
        self.extra_attributes[axis][TANGO_DEV] = None
        if axis > self.MaxDevice:
            raise Exception("Invalid axis %d" % axis)
        self.m[axis] = Motor(axis)

    def DeleteDevice(self,axis):
        m = self.m.get(axis)
        if not m:
            raise Exception("Invalid axis %d" % axis)
        del self.m[axis]
        if self.extra_attributes.has_key(axis):
            del self.extra_attributes[axis]

    def StateOne(self,axis):
        try:
            state = self._getMotorCtrl(axis).read_attribute('State').value
            status = self._getMotorCtrl(axis).read_attribute('Status').value
            ls = self._getMotorCtrl(axis).read_attribute('Limit_Switches').value
            ret_ls = int(ls[0])+2*int(ls[1])+4*int(ls[2])
            return state, status, ret_ls
        except Exception:
            return PyTango.DevState.ON, str("FB"), 0

    def ReadOne(self,axis):
        position = self._getMotorCtrl(axis).read_attribute('Position').value
        self.m[axis].position = position
        return position

    def StartAll(self):
        # PYPOOL NEEDS THIS DEFINED....
        pass

    def StartOne(self,axis,pos):
        self._getMotorCtrl(axis).write_attribute('Position', pos)
       
    def SetAxisPar(self, axis, par_name, value):
        pass
        #if par_name in ['Acceleration','Deceleration','Base_rate','Backlash','DialPosition','Limit_switches',
            #'Offset','Sign','Step_per_unit',]:
            #try:
                #self._getMotorCtrl(axis).write_attribute(par_name, value)
            #except Exception:
                #pass
        #else:
            #pass
        
    def GetAxisPar(self, axis, par_name):
        try:
            return self._getMotorCtrl(axis).read_attribute(par_name).value
        except Exception:
            pass
        #if par_name in ['Acceleration','Deceleration','Base_rate','Backlash','DialPosition','Limit_switches',
            #'Offset','Sign','Step_per_unit',]:
            #return self._getMotorCtrl(axis).read_attribute(par_name).value
        #else:
            #return -1

    def GetAxisExtraPar(self, axis, name):
        if name in [TANGO_DEV,]:
            return self.extra_attributes[axis][name]
        else:
            return -1

    def SetAxisExtraPar(self, axis, name, value):
        if name in [TANGO_DEV,]:
            self.extra_attributes[axis][name] = value

    def AbortOne(self,axis):
        try:
            self._getMotorCtrl(axis).Abort()
        except Exception:
            pass
    

    def StopOne(self, axis):
        try:
            self._getMotorCtrl(axis).Stop()
        except Exception:
            pass

    def DefinePosition(self, axis, current):
        pass
    
class BLIDControllerPM(MotorController):

    axis_attributes = { TANGO_DEV:{'Type':'PyTango.DevString',
                                   'R/W Type':'PyTango.READ_WRITE',
                                   'Description':'Tango-ds name.'}}

    gender = "BLID"
    model = "Simulator"
    organization = "CELLS - ALBA"
    devList = None

    MaxDevice = 1024

 
    def __init__(self, inst, props, *args, **kwargs):
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.extra_attributes = {}
        self.m = {}
        self._dp = None

    def _getMotorCtrl(self, axis):
        #if not self._dp:
        devName = self.extra_attributes[axis][TANGO_DEV]
        if devName is not None:
            self._dp = pool.PoolUtil().get_device(self.inst_name, devName)
            return self._dp

    def AddDevice(self,axis):
        self.extra_attributes[axis] = {}
        self.extra_attributes[axis][TANGO_DEV] = None
        if axis > self.MaxDevice:
            raise Exception("Invalid axis %d" % axis)
        self.m[axis] = Motor(axis)

    def DeleteDevice(self,axis):
        m = self.m.get(axis)
        if not m:
            raise Exception("Invalid axis %d" % axis)
        del self.m[axis]
        if self.extra_attributes.has_key(axis):
            del self.extra_attributes[axis]

    def StateOne(self,axis):
        try:
            state = self._getMotorCtrl(axis).read_attribute('State').value
            status = self._getMotorCtrl(axis).read_attribute('Status').value
            return state, status, 0
        except Exception:
            return PyTango.DevState.ON, str("FB"), 0

    def ReadOne(self,axis):
        position = self._getMotorCtrl(axis).read_attribute('Position').value
        self.m[axis].position = position
        return position

    def StartAll(self):
        # PYPOOL NEEDS THIS DEFINED....
        pass

    def StartOne(self,axis,pos):
        self._getMotorCtrl(axis).write_attribute('Position', pos)
       
    def SetAxisPar(self, axis, par_name, value):
        if par_name in ['Acceleration','Deceleration','Base_rate','Backlash','DialPosition','Limit_switches',
            'Offset','Sign','Step_per_unit',]:
            try:
                self._getMotorCtrl(axis).write_attribute(par_name, value)
            except Exception:
                pass
        else:
            pass
        
    def GetAxisPar(self, axis, par_name):
        if par_name in ['Offset','Instrument',]:
            return self._getMotorCtrl(axis).read_attribute(par_name).value
        else:
            pass
            #return -1

    def GetAxisExtraPar(self, axis, name):
        if name in [TANGO_DEV,]:
            return self.extra_attributes[axis][name]
        else:
            return -1

    def SetAxisExtraPar(self, axis, name, value):
        if name in [TANGO_DEV,]:
            self.extra_attributes[axis][name] = value


    def AbortOne(self,axis):
        try:
            self._getMotorCtrl(axis).Abort()
        except Exception:
            pass
    

    def StopOne(self, axis):
        try:
            self._getMotorCtrl(axis).Stop()
        except Exception:
            pass

    def DefinePosition(self, axis, current):
        pass
