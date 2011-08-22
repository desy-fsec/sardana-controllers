import math, logging
from pool import PseudoMotorController, PoolUtil

class DCM_ExitOffset_Controller(PseudoMotorController):
    """This pseudomotor controller does the calculation of Bragg
    and 2nd Xtal perpendicular position according to desired energy in eV.
    It works only with ClaesDcmTurboPmacCtrl motors"""
    
    pseudo_motor_roles = ('exitOffset',)
    motor_roles = ('perp',)
                             
    class_prop = { 'DCMBraggName':{'Type' : 'PyTango.DevString', 'Description' : 'DCM bragg motor name'}}

    def __init__(self, inst, props):    
        PseudoMotorController.__init__(self, inst, props)
        #self._log.setLevel(logging.DEBUG)

        try:
            self.dcm_bragg = PoolUtil().get_motor(self.inst_name, self.DCMBraggName)
        except Exception, e:
            self._log.error("Couldn't create DeviceProxy for %s motor." % self.DCMBraggName)
            raise e
        
    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]
    
    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index - 1]
    
    def calc_all_physical(self, pseudos):
        exitOffset, = pseudos
        bragg_deg = self.dcm_bragg.position
        bragg_rad = math.radians(bragg_deg)
        perp =exitOffset/2/math.cos(bragg_rad)
        return (perp,)
        
    def calc_all_pseudo(self, physicals):
        perp_mm, = physicals
        bragg_deg = self.dcm_bragg.position
        bragg_rad = math.radians(bragg_deg)
        exitOffset = 2 * perp_mm * math.cos(bragg_rad)
        return (exitOffset,)