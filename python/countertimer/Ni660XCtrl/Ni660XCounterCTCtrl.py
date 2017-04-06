import numpy
from Ni660XCTCtrl import Ni660XCTCtrl
from sardana.pool import AcqSynch


from sardana.pool.controller import CounterTimerController

# The order of inheritance is important. The CounterTimerController
# implements the API methods e.g. StateOne. Their default implementation raises
# the NotImplementedError. The Ni660XCTCtrl implementation must take
# precedence.
class Ni660XCounterCTCtrl(Ni660XCTCtrl, CounterTimerController):
    """This class is the Ni600X counter Sardana CounterTimerController.
    It can work in step and continuous scan mode. """

    BUFFER_ATTR = 'CountBuffer'
    APP_TYPE = 'CICountEdgesChan'
    SAMPLE_TIMING_TYPE = 'SampClk'
    CLK_SOURCE = 'sampleclocksource'

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        Ni660XCTCtrl.__init__(self, inst, props, *args, **kwargs)

