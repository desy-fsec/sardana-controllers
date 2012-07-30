import PyTango
import pool
from pool import CounterTimerController
import array
import sys

# TEMPORARY HACK UNTIL WE HAVE THE TANGO DEVICE AVAILABLE
from DummyCounterTimerController import DummyCounterTimerController

class BO_AFG_CTController(DummyCounterTimerController):
    """Controller to interact with the AFG device server."""
    class_prop = {'devName':{'Description':'The tango device to connect to.'
                                   ,'Type' : 'PyTango.DevString'}
                  }
