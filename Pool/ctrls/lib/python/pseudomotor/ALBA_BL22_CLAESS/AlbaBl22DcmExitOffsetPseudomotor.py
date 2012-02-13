import math, logging
from sardana import pool 
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController 

class DCM_ExitOffset_Controller(PseudoMotorController):
    """This pseudomotor controller does the calculation of Bragg
    and 2nd Xtal perpendicular position according to desired energy in eV.
    It works only with ClaesDcmTurboPmacCtrl motors"""
    
    pseudo_motor_roles = ('exitOffset',)
    motor_roles = ('perp',)
                             
    class_prop = { 'DCMBraggName':{'Type' : 'PyTango.DevString', 'Description' : 'DCM bragg motor name'},
                   'EnergyName':{'Type' : 'PyTango.DevString', 'Description' : 'Energy motor name'}}

    def __init__(self, inst, props, *args, **kwargs):    
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        try:
            self.dcm_bragg = PoolUtil().get_motor(self.inst_name, self.DCMBraggName)
        except Exception, e:
            self._log.error("Couldn't create DeviceProxy for %s motor." % self.DCMBraggName)
            raise e
        
    def calc_physical(self, index, pseudos):
        self._log.debug("Entering calc_physical")
        ret = self.calc_all_physical(pseudos)[index - 1]
        self._log.debug("Leaving calc_physical")
        return ret
    
    def calc_pseudo(self, index, physicals):
        self._log.debug("Entering calc_pseudo")
        ret = self.calc_all_pseudo(physicals)[index - 1]
        self._log.debug("Leaving calc_pseudo")
        return ret
    
    def calc_all_physical(self, pseudos):
        self._log.debug("Entering calc_all_physical")
        exitOffset, = pseudos
        bragg_deg = self.dcm_bragg.position
        bragg_rad = math.radians(bragg_deg)
        perp =exitOffset/2/math.cos(bragg_rad)
        self._log.debug("Leaving calc_all_physical")
        return (perp,)
        
    def calc_all_pseudo(self, physicals):
        self._log.debug("Entering calc_all_pseudo")
        perp_mm, = physicals
        bragg_deg = self.dcm_bragg.position
        bragg_rad = math.radians(bragg_deg)
        exitOffset = 2 * perp_mm * math.cos(bragg_rad)
        self._log.debug("Leaving calc_all_pseudo")
        return (exitOffset,)
