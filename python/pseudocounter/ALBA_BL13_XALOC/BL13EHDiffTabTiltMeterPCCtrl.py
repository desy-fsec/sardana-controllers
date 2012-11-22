import time
import traceback
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController
import taurus

class BL13EHDiffTabTiltMeterPCController(PseudoCounterController):

    counter_roles = ()
    pseudo_counter_roles = ('diftabpitout',)
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        self.serial = taurus.Device('BL13/CT/PYSERIAL-10')

    def Calc(self, index, counter_values):
        try:
            # PySerial has been restarted, this is needed
            # and if not, it raises an exception...
            try: self.serial.Open()
            except: pass

            # From documentation, first wakeup then query value with CRC
            self.serial.write([0x02])
            time.sleep(0.001)
            self.serial.read(1)
            self.serial.write([0x92,0x00,0x00,0x00,0x92])
            ans = self.serial.read(13)
            value_str = ''.join(map(chr,ans[4:-1]))
            value_str = value_str.replace(',','.')
            return float(value_str)

        except Exception,e:
            traceback_exc = traceback.format_exc()
            self._log.error('It was not possible to read the tilt meter')
            self._log.error('Exception: %s' % str(e))
            self._log.error('traceback: %s' % traceback_exc)

        return float('NaN')
