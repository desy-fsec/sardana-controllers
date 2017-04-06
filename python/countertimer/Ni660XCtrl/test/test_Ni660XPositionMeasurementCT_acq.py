#!/usr/bin/env python

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
import logging
from os import path
import sys

from taurus.external import unittest
from taurus.test import insertTest
from sardana.pool.test import AcquisitionTestCase

# IMPORTANT: use your device name!
TRIGGER_CHANNEL_DEV_NAMES = 'controls01:10000/io/lab/ictlael01-Dev1-ctr0,'
COUNTER_CHANNEL_DEV_NAMES = ',controls01:10000/io/lab/ictlael01-Dev1-ctr7'
SAMPLE_CLK_SRC = '/Dev1/PFI36'

@insertTest(helper_name='hw_continuous_acquisition', offset=0, 
            active_period=0.01, passive_period=0.02, repetitions=10,
            integ_time=0.01)
@insertTest(helper_name='hw_continuous_acquisition', offset=0, 
            active_period=0.1, passive_period=0.1, repetitions=10,
            integ_time=0.1)
class Ni660XTriggerGateCTAcqTestCase(AcquisitionTestCase, unittest.TestCase):
    """Integration test.
    """
    tg_ctrl_name = '_test_nitg_ctrl_1'
    tg_elem_name = '_test_nitg_1_1'
    chn_ctrl_name = '_test_nipm_ctrl_1'
    chn_elem_name1 = '_test_nipm_1_1'
    chn_elem_name2 = '_test_nipm_1_2'
    ## Configure the fake pool
    _nitestpath = path.dirname( path.abspath(__file__) )
    _nictrlpath = _nitestpath.rsplit('/', 1)[0]
    POOLPATH = list(AcquisitionTestCase.POOLPATH)
    POOLPATH.append(_nictrlpath)
    LOGLEVEL = logging.DEBUG

    def setUp(self):
        """Create a Controller, TriggerGate and PoolTGGeneration objects from
        Ni660XTriggerGateController and Ni660XPositionCTCtrl configurations.
        """
        ## TODO: Wortk arround for load modules
        # The pool can not load a module as a group of controllers
        sys.path.append(self._nictrlpath)
        ##
        unittest.TestCase.setUp(self)
        AcquisitionTestCase.setUp(self)
        # create TG ctrl and element
        ctrl_props = {'channelDevNames': TRIGGER_CHANNEL_DEV_NAMES}
        tg_ctrl_obj = self.createController(self.tg_ctrl_name,
                                'Ni660XTriggerGateController',
                                'Ni660XTriggerGateController.py',
                                ctrl_props)
        self.createTGElement(tg_ctrl_obj, self.tg_elem_name, 1)

        # create Ni660XPositionMeasurementCT ctrl and element
        ctrl_props = {'channelDevNames': COUNTER_CHANNEL_DEV_NAMES}
        ch_ctrl_obj = self.createController(self.chn_ctrl_name,
                                'Ni660XPositionCTCtrl',
                                'Ni660XPositionCTCtrl.py',
                                ctrl_props)
        self.createCTElement(ch_ctrl_obj, self.chn_elem_name1, 1)
        self.createCTElement(ch_ctrl_obj, self.chn_elem_name2, 2)
        ch_ctrl_obj.set_axis_attr(2, 'sampleclocksource', SAMPLE_CLK_SRC)

        self.channel_names.append(self.chn_elem_name1)
        self.channel_names.append(self.chn_elem_name2)

    def tearDown(self):
        ## TODO: Workaround
        sys.path.remove(self._nictrlpath)
        ##
        AcquisitionTestCase.tearDown(self)
        unittest.TestCase.tearDown(self)

