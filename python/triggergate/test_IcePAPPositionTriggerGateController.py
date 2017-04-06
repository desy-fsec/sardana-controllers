##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

import time
import PyTango

from taurus.test.base import insertTest
from sardana.pool.pooldefs import SynchDomain
from sardana.pool.poolcontrollers.test import TriggerGateControllerTestCase
from IcePAPPositionTriggerGateController import\
                                            IcePAPPositionTriggerGateController

configuration = [dict(delay={SynchDomain.Position: 0},
                      initial={SynchDomain.Position: 0},
                      active={SynchDomain.Position: 1},
                      total={SynchDomain.Position: 3},
                      repeats=10)]


@insertTest(helper_name='generation', configuration=configuration)
@insertTest(helper_name='stateOne')
class IcePAPPositionTriggerGateController(TriggerGateControllerTestCase):
    KLASS = IcePAPPositionTriggerGateController
    PROPS = {'Motors': 'mot_test',
             'Info_channels': 'InfoA InfoB InfoC,'}
    AXIS = 1
    DEBUG = False

    def post_configuration_hook(self):
        motor_name = self.PROPS.get('Motors').split(',')[0]
        motor = PyTango.DeviceProxy(motor_name)
        motor.write_attribute('velocity',2000)
        motor.write_attribute('acceleration', 0.01)
        motor.write_attribute_asynch('position', -20)
        while motor.State() == PyTango.DevState.MOVING:
            time.sleep(0.01)
        group = self.configuration[0]
        initial = group['initial'][SynchDomain.Position]
        total = group['total'][SynchDomain.Position]
        repeats = group['repeats'] - 1
        self._final_pos = initial + (total * repeats) + 20
        motor.write_attribute_asynch('position', self._final_pos)

    def post_generation_hook(self):
        motor_name = self.PROPS.get('Motors').split(',')[0]
        motor = PyTango.DeviceProxy(motor_name)
        pos = motor.position
        msg = ('The motor %s is not in the expected position %s, %s'
               %(motor.name, pos, self._final_pos))
        # check if the motor is in the expected position
        self.assertEqual(pos, self._final_pos, msg)
        # check if the ctrl state is ON
        self.stateOne()
