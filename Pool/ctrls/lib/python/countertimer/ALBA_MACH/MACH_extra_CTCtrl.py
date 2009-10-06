import PyTango
import pool
from pool import MotorController
import array
import sys

# TEMPORARY HACK UNTIL WE HAVE THE TANGO DEVICE INSTALLED
from DummyCounterTimerController import DummyCounterTimerController

class BO_AFG_CTController(DummyCounterTimerController):
    """"""
    class_prop = {'devName':{'Description':'The tango device to connect to.'
                                   ,'Type' : 'PyTango.DevString'}
                  }
