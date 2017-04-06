from taurus.external import unittest
from taurus.test import insertTest
from sardana.pool.test.test_tggeneration import TGGenerationTestCase
from sardana.pool.pooldefs import SynchParam, SynchDomain
from sardana.pool.poolcontrollers.test import TriggerGateControllerTestCase
from Ni660XTriggerGateController import Ni660XTriggerGateController

# IMPORTANT: use your device name!
CHANNEL_DEV_NAMES = 'controls01:10000/io/lab/ictlael01-Dev1-ctr0,'

@insertTest(helper_name='tggeneration',
            ctrl_lib = 'Ni660XTriggerGateController',
            ctrl_klass = 'Ni660XTriggerGateController',
            ctrl_props = {'channelDevNames': CHANNEL_DEV_NAMES},
            offset=0, active_period=0.001, passive_period=0.002, repetitions=10)
@insertTest(helper_name='abort_tggeneration',
            ctrl_lib = 'Ni660XTriggerGateController',
            ctrl_klass = 'Ni660XTriggerGateController',
            ctrl_props = {'channelDevNames': CHANNEL_DEV_NAMES},
            offset=0, active_period=0.1, passive_period=0.1, repetitions=100,
            abort_time=0.3)
class Ni660XTGGenerationTestCase(TGGenerationTestCase, unittest.TestCase):
    """Integration TestCase of TGGeneration with Ni660XTriggerGateController.
    """

    def setUp(self):
        unittest.TestCase.setUp(self)
        TGGenerationTestCase.setUp(self)

    def tearDown(self):
        TGGenerationTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)


configuration = [{SynchParam.Delay: {SynchDomain.Time: 0.03},
                  SynchParam.Active: {SynchDomain.Time: 0.005},
                  SynchParam.Total: {SynchDomain.Time: 0.01},
                  SynchParam.Repeats: 4}]


@insertTest(helper_name='generation', configuration=configuration)
@insertTest(helper_name='stateOne')
class Ni660XTriggerGateControllerTestCase(TriggerGateControllerTestCase):
    KLASS = Ni660XTriggerGateController
    PROPS = {'channelDevNames': CHANNEL_DEV_NAMES}
    AXIS = 1
    DEBUG = False