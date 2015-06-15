import time
import numpy
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
        retries = 0
        # Jordis requested to do us much retries as needed
        # in order to have a value available.
        while retries < 50:
            value = self.getValueFromSerialLine()
            if str(value) == 'nan':
                retries += 1
                self._log.error('Tiltmeter answered with an invalid answer, retries: %d' % retries)
                time.sleep(0.05)
            else:
                return value
        raise Exception('Can not read from serial line after %d retries' % retries)

    def getValueFromSerialLine(self):
        try:
            # PySerial has been restarted, this is needed
            # and if not, it raises an exception...
            try: self.serial.Open()
            except: pass

            # From documentation, first wakeup then query value with CRC
            # with this specific timing
            self.serial.write([0x02])
            time.sleep(0.001)
            self.serial.read(1)
            self.serial.write([0x92,0x00,0x00,0x00,0x92])
            retries = 0
            ans = self.serial.read(13)
            while len(ans) < 13 and retries < 5:
                numpy.append(ans, self.serial.read(13-len(ans)))
                retries += 1
            if retries == 5:
                raise 'Tiltmeter did not answer with 13 characters...'

            value_str = ''.join(map(chr,ans[4:-1]))
            value_str = value_str.replace(',','.')
            return float(value_str)

        except Exception,e:
            traceback_exc = traceback.format_exc()
            self._log.error('It was not possible to read the tilt meter')
            self._log.error('Exception: %s' % str(e))
            self._log.error('traceback: %s' % traceback_exc)

        return float('NaN')


