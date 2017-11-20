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

import numpy
import taurus

from sardana import State
from sardana.pool.pooldefs import SynchDomain, SynchParam
from sardana.pool.controller import TriggerGateController
from sardana.pool.controller import Type, Access, Description, DefaultValue

class IcePAPPositionTriggerGateController(TriggerGateController):
    """Basic IcePAPPositionTriggerGateController.
    """

    organization = "ALBA-Cells"
    gender = "TriggerGate"
    model = "Icepap"

    ActivePeriod = 50e-6 # 50 micro seconds

    # The properties used to connect to the ICEPAP motor controller
    ctrl_properties = {
        'Motors': {Type: str,
                   Description: 'List of IcePap motors name separated by '
                                'comma(s)'
        },
        'Info_channels': {Type: str,
                          Description: 'List of groups of Info channel(s) '
                                       'separated by space(s) to be used as '
                                       'trigger separated by comma(s). '
                                       'e.g: "InfoA InfoB,InfoB InfoC,InfoB"'
        }
    }

    def __init__(self, inst, props, *args, **kwargs):
        """
        :param inst:
        :param props:
        :param args:
        :param kwargs:
        :return:
        """
        TriggerGateController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug('IcePAPPositionTriggerCtr init....')
        self.triggers = {}
        self.motor_names = self.Motors.split(',')
        self.info_channels = map(str.split, self.Info_channels.split(','))

    def AddDevice(self, axis):
        """
        :param axis: axis of the controller
        :return:
        """
        self._log.debug('AddDevice(%d): entering...' % axis)
        idx = axis - 1
        motor = taurus.Device(self.motor_names[idx])
        info_channels = self.info_channels[idx]
        self.triggers[idx] = {'motor': motor,
                              'offset': 0,
                              'passive_interval': 0,
                              'repetition': 1,
                              'sign': 1,
                              'info_channels': info_channels
                              }

    def DeleteDevice(self, axis):
        """
        :param axis:
        :return:
        """
        idx = axis - 1
        self.triggers.pop(idx)

    def StateOne(self, axis):
        """Get the trigger/gate state"""
        self._log.debug('StateOne(%d): entering...' % axis)
        idx = axis - 1
        tg = self.triggers[idx]
        motor = tg['motor']
        return motor.state, motor.status

    def PreStartOne(self, axis):
        """PreStart the specified trigger
        """
        self._log.debug('PreStartOne(%d): entering...' % axis)
        idx = axis - 1
        tg = self.triggers[idx]
        motor = tg['motor']
        for info_chn in tg['info_channels']:
            info_cfg = motor.__getattr__(info_chn).upper()
            if info_cfg != 'ECAM NORMAL':
                msg = ('PreStartOne(%d): The axis has the %s wrong '
                      'configured (%s)' %(idx, info_chn.upper(), info_cfg))
                self._log.debug(msg)
                return False
#         pos0 = motor.position
#         velocity = motor.velocity
#         offset = tg.get('offset', 0)
#         sign = tg.get('sign', 1)
#         tg['active_interval'] = active_interval = self.ActivePeriod * velocity
#         repetitions = tg.get('repetitions', 1)
#         passive_interval = tg.get('passive_interval')
#         start_pos = pos0 + offset
#         step = (active_interval + passive_interval) * sign
#         end_pos = step * repetitions
#         # TODO if we want a trigger in the last position:
#         # - end_pos +=  active_interval + passive_interval
#         # - repetitions += 1
#         motor.ecamdat = [start_pos, end_pos, repetitions]

        return True

    def StartOne(self, axis):
        """Overwrite the StartOne method
        """
        pass

    def AbortOne(self, axis):
        """Start the specified trigger
        """
        self._log.debug('AbortOne(%d): entering...' % axis)

    def SetAxisPar(self, axis, name, value):
        idx = axis - 1
        tg = self.triggers[idx]
        name = name.lower()
        pars = ['offset', 'passive_interval', 'repetitions', 'sign',
                 'info_channels']
        if name in pars:
            tg[name] = value

    def GetAxisPar(self, axis, name):
        idx = axis - 1
        tg = self.triggers[idx]
        name = name.lower()
        v = tg.get(name, None)
        if v is None:
            msg = ('GetAxisPar(%d). The parameter %s does not exist.'
                    % (axis, name))
            self._log.error(msg)
        return v

    def SynchOne(self, axis, configuration):
        idx = axis - 1
        motor = self.triggers[idx]['motor']

        # TODO Implement the multiple groups
        step_per_unit = motor['step_per_unit'].value
        offset = motor['offset'].value
        sign = motor['sign'].value

        group = configuration[0]
        initial_user = group[SynchParam.Initial][SynchDomain.Position]
        nr_points = group[SynchParam.Repeats]
        total_user = group[SynchParam.Total][SynchDomain.Position]

        initial = (initial_user - offset) * (step_per_unit / sign)
        total = total_user * (step_per_unit / sign)
        final = initial + (total * nr_points)
        self._log.debug('IcepapTriggerCtr configuration: %f %f %d %d' %
                        (initial, final, nr_points, total))

        # There is a limitation of numbers of point on the icepap (8192)
        # ecamdat = motor.getAttribute('ecamdatinterval')
        # ecamdat.write([initial, final, nr_points], with_read=False)

        trigger_positions_tables = numpy.linspace(int(initial), int(final-total), int(nr_points))
        # ECAMDAT HAS TO BE A LIST WITH l[0] < l[-1]
        if trigger_positions_tables[0] > trigger_positions_tables[-1]:
            trigger_positions_tables = [x for x in reversed(trigger_positions_tables)]
        self._log.debug('trigger table %s'%str(trigger_positions_tables))
        ecamdattable = motor.getAttribute('ecamdattable')
        ecamdattable.write(trigger_positions_tables, with_read=False)
