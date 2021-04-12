from Ni660XCTCtrl import Ni660XCTCtrl

from taurus import Attribute
from sardana import DataAccess
from sardana.pool import AcqSynch
from sardana.pool.controller import (CounterTimerController,
                                     Memorize, NotMemorized, Memorized)
from sardana.pool.controller import Type, Access

ReadWrite = DataAccess.ReadWrite

# The order of inheritance is important. The CounterTimerController
# implements the API methods e.g. StateOne. Their default implementation raises
# the NotImplementedError. The Ni660XCTCtrl implementation must take
# precedence.
class Ni660XPositionCTCtrl(Ni660XCTCtrl, CounterTimerController):
    "This class is the Ni600X position capture Sardana CounterTimerController"

    BUFFER_ATTR = 'PositionBuffer'
    QUERY_FILTER = 1
    SAMPLE_TIMING_TYPE = 'SampClk'
    APP_TYPE = 'CIAngEncoderChan'
    CLK_SOURCE = 'sampleclocksource'

    axis_attributes = dict(Ni660XCTCtrl.axis_attributes)
    axis_attributes.update({
        "pulsesPerRevolution": {
            Type: long,
            Access: ReadWrite,
            Memorize: Memorized
        },
        "initialPos": {
            Type: float,
            Access: ReadWrite,
            Memorize: NotMemorized
        },
        "initialPosAttr": {
            Type: str,
            Access: ReadWrite
        },
        "zIndexEnabled": {
            Type: bool,
            Access: ReadWrite,
            Memorize: NotMemorized
        },
        "units": {
            Type: str,
            Access: ReadWrite,
            Memorize: NotMemorized
        },
        "sign": {
            Type: int,
            Access: ReadWrite,
        }
    })

    direct_attributes = Ni660XCTCtrl.direct_attributes + (
        'units', 'pulsesperrevolution', 'zindexenabled')

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        Ni660XCTCtrl.__init__(self, inst, props, *args, **kwargs)

    def AddDevice(self, axis):
        Ni660XCTCtrl.AddDevice(self, axis)
        if axis != 1:
            #readount ot 60000 buffer takes aprox 10 seconds
            self.channels[axis].set_timeout_millis(120000)
            self.attributes[axis]['sign'] = 1
            self.attributes[axis]['initialpos'] = None
            self.attributes[axis]['initialposattr'] = ""
            self.attributes[axis]['initialposvalue'] = 0

    def PreStartOneCT(self, axis):
        if Ni660XCTCtrl.PreStartOneCT(self, axis) and axis != 1:
            initial_pos_value = self.attributes[axis]['initialpos']
            self.attributes[axis]['initialpos'] = None
            if initial_pos_value is None:
                initial_pos_attr = self.attributes[axis]['initialposattr']
                if len(initial_pos_attr) > 0:
                    attr_value = Attribute(initial_pos_attr).read().value
                    try:
                        initial_pos_value = float(attr_value)
                    except ValueError:
                        msg = "initialPosAttr (%s) is not float" % initial_pos_attr
                        raise Exception(msg)
                else:
                    initial_pos_value = 0
            self.attributes[axis]["initialposvalue"] = initial_pos_value
        return True

    def _calculate(self, axis, data, index):
        data = data[index:]
        if self.attributes[axis]["sign"] == -1:
            data = data * -1
        data = data + self.attributes[axis]["initialposvalue"]
        return data
