#!/usr/bin/env python

from BL29Energy import Energy

import math

import taurus
from sardana import DataAccess
from sardana.pool import PoolUtil
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool.controller import PseudoCounterController


class BL29EnergyPCCtrl(PseudoCounterController):
    """
    Energy pseudo counter controller for handling BL29-Boreas energy calculation given the positions
    of all the motors involved.
    """

    gender = 'PseudoCounter'
    model  = 'BL29-Boreas energy calculation'
    organization = 'CELLS - ALBA'
    image = 'energy.png'
    logo = 'ALBA_logo.png'

    counter_roles = ()
    pseudo_counter_roles = 'Energy',

    #controller properties
    ctrl_properties = {
        'sm_pseudo' : {
            Type : str,
            Description : 'The name of the DiscretePseudoMotor to read/select which SM to use'
        },
        'gr_pseudo' : {
            Type : str,
            Description : 'The name of the DiscretePseudoMotor to read/select which grating to use'
        },
    }

    #axis attributes
    axis_attributes = {
        'gr_pitch_source' : {
            Type : str,
            Description : 'The name of the source from which to read the grating pitch',
            Access : DataAccess.ReadWrite,
            DefaultValue : ''
        },
        'offset0' : {
            Type : float,
            Description : 'Offset in micro radiands to apply to the gr_pitch value got from the gr_pitch_source in order to get 0 reading at horizontal position',
            Access : DataAccess.ReadWrite,
            DefaultValue : Energy.offset0
        },
        'step_per_unit' : {
            Type : float,
            Description : 'Steps per unit to convert from the gr_pitch value got from the gr_pitch_source into micro radians',
            Access : DataAccess.ReadWrite,
            DefaultValue : Energy.step_per_unit
        },
        'ranges' : {
            Type : str,
            Description : 'Energy ranges for each combination of SM and GR',
            Access : DataAccess.ReadOnly
        }
    }

    def __init__(self, inst, props, *args, **kwargs):
        """
        Do the default init
        @param inst instance name of the controller
        @param properties of the controller
        @param *args extra arguments
        @param **kwargs keyword arguments
        """
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        self.sm_selected = PoolUtil.get_device(inst, self.sm_pseudo)
        self.gr_selected = PoolUtil.get_device(inst, self.gr_pseudo)
        self.gr_pitch = [None, None]
        self.gr_pitch_source = ['','']
        self.offset0 = Energy.offset0 #should be restored as a memorized attribute if modified
        self.step_per_unit = Energy.step_per_unit #should be restored as a memorized attribute

    def Calc(self,index,counter_values):
        """
        Given the physical motor positions, it computes the energy pseudo counter.
        @param[in] index:
        @param[in] counter_values
        @return the energy pseudo counter value
        @throws exception
        """
        try:
            #fist time, so build device proxy
            if self.gr_pitch[index-1] == None:
                self.gr_pitch[index-1] = PoolUtil.get_device(self.GetName(), self.gr_pitch_source[index-1])

            #get currently selected grating, selected spherical mirror and grating pitch encoder counts
            sm_selected = self.sm_selected.position
            gr_selected = self.gr_selected.position
            gr_pitch_dev_class = self.gr_pitch[index-1].info().dev_class.lower()

            #get the value of the gr pitch depending on the type of its source 
            if gr_pitch_dev_class == 'motor':
                gr_pitch = self.gr_pitch[index-1].encencin
            elif gr_pitch_dev_class == 'zerodexpchannel':
                gr_pitch = self.gr_pitch[index-1].value
            elif gr_pitch_dev_class == 'pysignalsimulator':
                gr_pitch = self.gr_pitch[index-1].encencin
            else:
                raise Exception
        except Exception, e:
            msg = 'Unable to determine SM and/or GR selected and/or GR pitch. Details: %s' % str(e)
            self._log.error(msg)
            raise Exception(msg)

        if not (sm_selected in Energy.SM_VALID) or not (gr_selected in Energy.GR_VALID) or (gr_pitch == None):
            msg = 'Spherical mirrors and/or grating mirror and/or grating pitch are not correctly set in CalcPseudo()'
            self._log.error(msg)
            raise Exception(msg)

        self._log.debug('gr_pitch raw (enc counts): %f' % gr_pitch)
        #compute and return energy
        energy = Energy.get_energy(sm_selected,gr_selected,gr_pitch,gr_source_is_encoder=True)
        self._log.debug('energy: %f' % energy)
        return energy

    def GetAxisExtraPar(self, axis, name):
        """
        Get extra controller parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to get (always one)
        @param name of the parameter to retrieve
        @return the value of the parameter
        """
        if name == 'gr_pitch_source':
            return self.gr_pitch_source[axis-1]
        elif name == 'offset0':
            return Energy.offset0
        elif name == 'step_per_unit':
            return Energy.step_per_unit
        elif name == 'ranges':
            return Energy.ranges
        else:
            msg = 'Invalid axis %s attribute %s' % (str(axis), str(name))
            self._log.error(msg)
            raise Exception(msg)

    def SetAxisExtraPar(self, axis, name, value):
        """
        Set extra axis parameters. These parameters should actually be
        controller parameters, but users asked to use them as axis parameters
        in order to directly use the motor name instead of the controller name
        to set/get these parameters
        @param axis to set (always one)
        @param name of the parameter to set
        @param value to be set
        """
        if name == 'gr_pitch_source':
            self.gr_pitch_source[axis-1] = value
        elif name == 'offset0':
            Energy.offset0 = value
        elif name == 'step_per_unit':
            Energy.step_per_unit = value
        else:
            return


class BL29MachinePCCtrl(PseudoCounterController):

    gender = 'PseudoCounter'
    model  = 'BL29-Boreas access to machine parameters'
    organization = 'CELLS - ALBA'
    image = 'machine.png'
    logo = 'ALBA_logo.png'

    counter_roles = ()
    pseudo_counter_roles = ('machine_current', 'fex', 'fez', 'ife1', 'ife2', 'ife3', 'ife4', 'ife')

    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)
        self.machine_attrs = {}
        self.MACH_CURRENT = 1
        self.machine_attrs[self.MACH_CURRENT] = 'tango://alba03:10000/expchan/id29eu_machine_attributes/1/Value'
        self.FEX = 2
        self.machine_attrs[self.FEX] = 'tango://alba03:10000/expchan/id29eu_machine_attributes/2/Value'
        self.FEZ = 3
        self.machine_attrs[self.FEZ] = 'tango://alba03:10000/expchan/id29eu_machine_attributes/3/Value'
        self.IFE1 = 4
        self.machine_attrs[self.IFE1] = 'tango://alba03:10000/expchan/id29eu_machine_attributes/4/Value'
        self.IFE2 = 5
        self.machine_attrs[self.IFE2] = 'tango://alba03:10000/expchan/id29eu_machine_attributes/5/Value'
        self.IFE3 = 6
        self.machine_attrs[self.IFE3] = 'tango://alba03:10000/expchan/id29eu_machine_attributes/6/Value'
        self.IFE4 = 7
        self.machine_attrs[self.IFE4] = 'tango://alba03:10000/expchan/id29eu_machine_attributes/7/Value'
        # Not from machine but calculated
        self.IFE = 8

    def read_tango_attribute(self, machine_tango_attribute):
        attr = taurus.Attribute(machine_tango_attribute)
        return attr.read().value

    def calc(self, index, counter_values):
        if index in self.machine_attrs.keys():
            return self.read_tango_attribute(self.machine_attrs[index])
        elif index == self.IFE:
            i1 = self.read_tango_attribute(self.machine_attrs[self.IFE1])
            i2 = self.read_tango_attribute(self.machine_attrs[self.IFE2])
            i3 = self.read_tango_attribute(self.machine_attrs[self.IFE3])
            i4 = self.read_tango_attribute(self.machine_attrs[self.IFE4])
            return i1 + i2 + i3 + i4


class BL29XmcdPCCtrl(PseudoCounterController):

    gender = 'PseudoCounter'
    model  = 'BL29-Boreas access to XMCD end station'
    organization = 'CELLS - ALBA'
    image = 'xmcd.png'
    logo = 'ALBA_logo.png'

    role_attribute = {
        'xmcd_he_main_level' : 'XMCD/CT/HDI/ChannelA',
        'xmcd_he_4K_level'   : 'XMCD/CT/HDI/ChannelB',
        'xmcd_he_pump_mode'  : 'XMCD/CT/HDI/RelayX',
        'xmcd_temp_1K'        : 'XMCD/CT/TC/ChannelA',
        'xmcd_temp_1K_target' : 'XMCD/CT/TC/Loop1SetPoint',
        'xmcd_temp_sample'    : 'XMCD/CT/TC/ChannelB',
        'xmcd_temp_magnet_top'    : 'XMCD/CT/TM/ChannelA',
        'xmcd_temp_magnet_bottom' : 'XMCD/CT/TM/ChannelB',
        'xmcd_temp_rotary'        : 'XMCD/CT/TM/ChannelC',
        'xmcd_n2_level'           : 'XMCD/CT/TM/ChannelD',
    }

    counter_roles = ()
    pseudo_counter_roles = tuple(sorted([key for key in role_attribute.keys()]))

    def __init__(self, inst, props, *args, **kwargs):
        PseudoCounterController.__init__(self, inst, props, *args, **kwargs)

    def read_tango_attribute(self, machine_tango_attribute):
        attr = taurus.Attribute(machine_tango_attribute)
        return attr.read().value

    def calc(self, index, counter_values):
        if  index in range(1,len(self.pseudo_counter_roles)+1):
            return self.read_tango_attribute(self.role_attribute[self.pseudo_counter_roles[index-1]])
