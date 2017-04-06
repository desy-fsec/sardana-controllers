from taurus.test.base import insertTest
from sardana.pool.poolcontrollers.test import TriggerGateControllerTestCase
from Ni660XPositionTriggerGateController import\
                                            Ni660XPositionTriggerGateController

@insertTest(helper_name='abort', configuration={'repetitions': 10,
                                                'offset': 4,
                                                'active_interval': 2,
                                                'passive_interval': 2},
            abort=0.5)
@insertTest(helper_name='axisPar', name='repetitions', value=10)
@insertTest(helper_name='axisPar', name='active_interval', value=2)
@insertTest(helper_name='axisPar', name='passive_interval', value=2)
@insertTest(helper_name='axisPar', name='offset', value=10)
@insertTest(helper_name='axisPar', name='offset', value=0, expected_value=4)
@insertTest(helper_name='axisPar', name='resolution', value=0.1)
class Ni660XPositionTriggerGateControllerTestCase(TriggerGateControllerTestCase):
    KLASS = Ni660XPositionTriggerGateController
    PROPS = {
        'positionDevNames': 'controls01:10000/io/lab/ictlael01-Dev1-ctr7,',
        'generatorDevNames': 'controls01:10000/io/lab/ictlael01-Dev1-ctr0,'
    }

    def test_offset_resolution(self):
        self.ctrl.SetAxisPar(1, 'resolution', 0.01)
        self.axisPar('offset', 10)
