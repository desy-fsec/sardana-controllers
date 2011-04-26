from scan import ascan
from macro import Type, Macro
import math

class rscan(ascan): 
    """Do an absolute scan of the specified motor.
    ascan scans one motor, as specified by motor. The motor starts at the
    position given by start_pos and ends at the position given by final_pos.
    The step size is given by a step_size parameter. The number of data points collected
    will be floor((final_pos - start_pos)/step_size) + 1. Count time is given by time which if positive,
    specifies seconds and if negative, specifies monitor counts. """

    param_def = [
       ['motor',      Type.Motor,   None, 'Motor to move'],
       ['start_pos',  Type.Float,   None, 'Scan start position'],
       ['final_pos',  Type.Float,   None, 'Scan final position'],
       ['step_size',  Type.Float, None, 'Scan step size'],
       ['integ_time', Type.Float,   None, 'Integration time']
    ]

    def prepare(self, motor, start_pos, final_pos, step_size, integ_time,
                **opts):
        nr_interv = math.floor(abs(final_pos - start_pos)/step_size)
        final_pos = start_pos + step_size * nr_interv
        self._prepare([motor], [start_pos], [final_pos], nr_interv, integ_time, **opts)
        
        
class xxx(Macro):
    
    param_def = [
       ['motor',      Type.Motor,   None, 'Motor check pos']
    ]
    
#    def #prepare(self, motor, **opts):
        
    
    def run(self, motor, **opts):
        self.execMacro("lsenv")
    