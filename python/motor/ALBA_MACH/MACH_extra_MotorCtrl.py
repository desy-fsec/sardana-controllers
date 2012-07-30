import PyTango
import pool
from pool import MotorController
import array
import sys

# TEMPORARY HACK UNTIL WE HAVE THE TANGO DEVICE INSTALLED
from DummyMotorController import DummyMotorController

class BO_RFCavPhVol_MotController(DummyMotorController):
    """"""
    class_prop = {'devName':{'Description':'The tango device to connect to.'
                                   ,'Type' : 'PyTango.DevString'}
                  }
