import PyTango
import array
import time
import traceback

from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoCounterController
import taurus

class BL13OHInfinityMeterPCCtrl(PseudoCounterController):

    counter_roles = ()
    pseudo_counter_roles = ('vfmstrnb', 'vfmstrnf', 'hfmstrnb', 'hfmstrnf')
    
    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        self.serials = {}
        self.serials[1] = taurus.Device('BL13/CT/SERIAL422-01')
        self.serials[2] = taurus.Device('BL13/CT/SERIAL422-02')
        self.serials[3] = taurus.Device('BL13/CT/SERIAL422-03')
        self.serials[4] = taurus.Device('BL13/CT/SERIAL422-04')

    def Calc(self, index, counter_values):
        try:
            serial = self.serials[index]
            retries = 1
            while True:
	        try:
                    ans = self._read(serial)
                    break
                except:
                    if not retries: raise
                    retries -= 1

            # IN CASE OF OVERFLOW, THE ANSWER IS: '0_X0_?+999999\r'
            value = ans[5:].strip().replace('?','')
            return float(value)

        except Exception,e:
            traceback_exc = traceback.format_exc()
            self._log.error('It was not possible to read any answer for index %d' % index)
            self._log.error('Exception: %s' % str(e))
            self._log.error('traceback: %s' % traceback_exc)

        return float('NaN')

    def _read(self, serial):
        serial.DevSerFlush(2)
        serial.DevSerWriteString('*01X01\r')
        ans = serial.DevSerReadNChar(13)
        return ans
