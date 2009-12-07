#!/usr/bin/env python2.5

#############################################################################
##
## file :    PmacLTPIOCtrl.py
##
## description : 
##
## project :    miscellaneous/PoolControllers/MotorControllers
##
## developers history: zreszela
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

from PyTango import DevState
from pool import IORegisterController
from pool import PoolUtil

class LTPIORController(IORegisterController):
    """ This controller provides the state of the air supply and the airpads to the pool.
    +) first axis is the state of air supply
    +) second axis is the state of airpads for top axis
       -)   0: top axis lifted
       -)  63: top axis landed
    +) third axis is the state of airpads for bottom axis
       -) 0: bottom axis lifted
       -) 3: bottom axis landed
    """
    
    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    # The PMAC Device Server to get the info
    class_prop = {'PmacDevName':{'Description' : 'The Pmac Tango DS','Type' : 'PyTango.DevString'}}
    
    MaxDevice = 3

    def __init__(self, inst, props):
        IORegisterController.__init__(self, inst, props)
	self.pmac_eth = PoolUtil().get_device(self.inst_name, self.PmacDevName)

    def AddDevice(self, axis):
        self._log.debug('AddDevice %d' % axis)

    def DeleteDevice(self, axis):
        self._log.debug('DeleteDevice %d' % axis)

    def StateOne(self, axis):
        try:
            value = self.ReadOne(axis)
            bits = 1
            if axis == 2: bits = 6
            elif axis == 3: bits = 2
            str_bin_value = self._to_binary(value, bits)
        except Exception, e:
            self._log.error(str(e))
            value = '???'
            str_bin_value = '????????' 

        # THE STATE CAN BE ON (everything OK), OR ALARM (not all OK)
        state = DevState.ON
        status = 'Hardware value: %s' % str_bin_value
        if axis == 1 and value != 1:
            state = DevState.ALARM
            status += ' The air supply is NOT OK'
        elif axis == 2 and value != 0:
            state = DevState.ALARM
            status += ' Some airpads are not lifted: %s' % str_bin_value
        elif axis == 3 and value != 0:
            state = DevState.ALARM
            status += ' Some airpads are not lifted: %s' % str_bin_value
        return (state, status)

    def ReadOne(self, axis):
        # DO THE STUFF TO READ FROM THE PMAC
        # ...
        value = int(self.pmac_eth.command_inout("GetMVariable", 100))
        if axis == 1:
            value &= 1
        elif axis == 2:
            value >>= 1
            value &= 63
        elif axis == 3:
            value >>= 7
            value &= 3
        return value

    def WriteOne(self, axis, value):
        # IT IS ONLY POSSIBLE TO WRITE THE AIRPADS (axis 2)
        if axis == 1:
            return
        if axis == 2:
            current_3axis = self.ReadOne(3)
            write_value = value + (current_3axis << 6)
        if axis == 3:
            current_2axis = self.ReadOne(2)
            write_value = (value << 6) + current_2axis
        self.pmac_eth.command_inout("SetMVariable", [101,write_value])
            
            
            # DO THE STUFF TO SET THE VALUE IN THE PMAC

    def GetExtraAttributePar(self, axis, name):
        pass

    def SetExtraAttributePar(self,axis, name, value):
        pass
        
    def SendToCtrl(self,in_data):
        return "Not implemented yet"

    def _to_binary(self, number, bits):
        str_binary_number = ''
        for pos in range(bits):
            index = bits - pos - 1
            shifted_number = number / pow(2,index)
            bit = '0'
            if shifted_number & 1:
                bit = '1'
            str_binary_number = str_binary_number+bit
        return str_binary_number
                                                                        
