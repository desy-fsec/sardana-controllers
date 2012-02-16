#############################################################################
##
## file :    SIS3610Ctrl.py
##
## description : 
##
## project :    Sardana/Pool/ctrls/OIRegister
##
## developers history: tnunez
##
## copyleft :    Cells / Alba Synchrotron
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Sardana.
##
## This is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This software is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################

import PyTango

import time

from sardana import State, DataAccess
from sardana.pool.controller import IORegisterController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite

import json

class SIS3610Controller(IORegisterController):
    """This class is the Tango Sardana Motor controller for the SIS3610 IORegister.
    """

    gender = "IORegister"
    model  = "SIS3610"
    organization = "DESY"
    image = ""
    icon = ""
    logo = ""
    			     
    ctrl_properties = {'RootDeviceName':{Type:str,Description:'The root name of the Motor Tango devices'}}
    
    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        
        self.db = PyTango.Database()
        name_dev_ask =  self.RootDeviceName + "*"
	self.devices = self.db.get_device_exported(name_dev_ask)
        self.max_device = 0
        self.tango_device = []
        self.proxy = []
        self.device_available = []
	for name in self.devices.value_string:
            self.tango_device.append(name)
            self.proxy.append(None)
            self.device_available.append(0)
            self.max_device =  self.max_device + 1

    def AddDevice(self, ind):
        IORegisterController.AddDevice(self,ind)
        if ind > self.max_device:
            print "False index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy(self.tango_device[ind-1])
        self.device_available[ind-1] = 1

    def DeleteDevice(self, ind):
        MotorController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0

    def StateOne(self, ind):
        if  self.device_available[ind-1] == 1:
            sta = self.proxy[ind-1].command_inout("State")
            if sta == PyTango.DevState.ON:
                status_string = "IORegister is in ON state"
            elif sta == PyTango.DevState.FAULT:
                status_string = "IORegister is in FAULT state"
            tup = (sta, status_string)
            return tup

    def ReadOne(self, ind):
        if self.device_available[ind-1] == 1:
            return self.proxy[ind-1].read_attribute("Value").value

    def WriteOne(self, ind, value):
        if self.device_available[ind-1] == 1:
            self.proxy[ind-1].write_attribute("Value", value)
        
    def SendToCtrl(self,in_data):
        return ""
