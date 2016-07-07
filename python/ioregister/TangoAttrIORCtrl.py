#############################################################################
##
## file :    TangoAttrIORCtrl.py
##
## description : 
##
## project :    Sardana/Pool/ctrls/OIRegister
##
## developers history: gcuni,sblanch
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

from PyTango import DevState,DevFailed
from sardana import State, DataAccess
from sardana.pool import PoolUtil
from sardana.pool.controller import IORegisterController
from sardana.pool.controller import Type, Access, Description
from sardana.tango.core.util import from_tango_state_to_state

import json

TANGO_ATTR = 'TangoAttribute'
DEVICE = 'Device'
DPROXY = 'DeviceProxy'
ATTRIBUTE = 'Attribute'
LABELS = 'Labels'
POSITIONS = 'Positions'
CALIBRATION = 'Calibration'
READFAILED = 'readFailed'

#def agrupate(l,n):
#    #print "agrupate(%s,%s) "%(l,n)
#    res = []
#    if not len(l)%n == 0: raise Exception("Impossible for this length.")
#    for i in range(len(l)/n):
#        sub = []
#        for j in range(n):
#            sub.append(l[(i*n)+j])
#        res.append(sub)
#    return res

#def flatten(l):
#    #print "flatten(%s) "%(l)
#    result = []
#    for el in l:
#        if hasattr(el, "__iter__") and not isinstance(el, basestring):
#            result.extend(flatten(el))
#        else:
#            result.append(el)
#    return result


class TangoAttrIORController(IORegisterController):
    """This controller offers as many IORegisters as the user wants.
    Each IORegisters _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the IORegister
        As examples you could have:
        ch1.TangoExtraAttribute = 'my/tango/device/attribute1'
        ch2.TangoExtraAttribute = 'my/tango/device/attribute2'
        ch3.TangoExtraAttribute = 'my_other/tango/device/attribute1'
    Each IORegisters _MAY_HAVE_ extra attributes:
    +) Labels - Human readable tag followed to the corresponding position (integer) value.
        As examples you have:
        ch1.Labels: "16.66%:16 33.33%:33 50%:50 66.66%:66 83.33%:83 100%:100"
        That means: The possible values for the IOR are {16,33,50,66,83,100}
    +) Calibration - String of the triples min,pos,max
        This is extra and dependent that the Labels exists
        As examples you could have:
        ch1.Calibration = "[[0.4,0.5,0.6],[1.4,1.5,1.6],
                            [2.4,2.5,2.6],[3.4,3.5,3.6],
                            [4.4,4.5,4.6],[5.4,5.5,5.6]]"
        That means: set position of the IOR 83, will write 4.5 to the TangoAttr.
                    when the reading of the TangoAttr is between [1.4,1.6] the
                    IOR value will be 33.
        Note: bounds included, in case of no fussy area but needs calibration,
              you can use the same value for all in the triples.
    """

    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    axis_attributes ={TANGO_ATTR:
                        {Type : str,
                         Description : 'The first Tango Attribute to read (e.g. my/tango/dev/attr)',
                         Access : DataAccess.ReadWrite,
                         'fget' : 'get%s' % TANGO_ATTR,
                         'fset' : 'set%s' % TANGO_ATTR},
                      CALIBRATION:#type hackish until arrays supported
                        {Type : str,
                         Description : 'Flatten list of a list of triples and [min,cal,max]',
                         Access : DataAccess.ReadWrite,
                         'fget' : 'get%s' % CALIBRATION,
                         'fset' : 'set%s' % CALIBRATION},
                      LABELS:#type hackish until arrays supported
                        {Type : str,
                         Description : 'String list with the meaning of each discrete position',
                         Access : DataAccess.ReadWrite,
                         'fget' : 'get%s' % LABELS,
                         'fset' : 'set%s' % LABELS}
                      }
    MaxDevice = 1024

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        self.devsExtraAttributes = {}

    def AddDevice(self, axis):
        self._log.debug('AddDevice %d' % axis)
        self.devsExtraAttributes[axis] = {}
        self.devsExtraAttributes[axis][TANGO_ATTR] = None
        self.devsExtraAttributes[axis][DPROXY] = None
        self.devsExtraAttributes[axis][LABELS] = []
        self.devsExtraAttributes[axis][POSITIONS] = []
        self.devsExtraAttributes[axis][CALIBRATION] = []
        #When the ReadOne raise an exception, inform the state
        self.devsExtraAttributes[axis][READFAILED] = False

    def DeleteDevice(self, axis):
        del self.devsExtraAttributes[axis]

    def StateOne(self, axis):
        tango_attr = self.devsExtraAttributes[axis][TANGO_ATTR]
        try: dev_proxy = self.devsExtraAttributes[axis][DPROXY] or self._buildProxy(axis)
        except Exception,e: return (State.Init,str(e))
        llabels = len(self.devsExtraAttributes[axis][LABELS])
        lcalibration = len(self.devsExtraAttributes[axis][CALIBRATION])
        readFailed = self.devsExtraAttributes[axis][READFAILED]
        if tango_attr == None or dev_proxy == None:
            return (State.Disable,
                    "Not yet configured the Tango Attribute, or cannot proxy it")
        if not lcalibration == 0 and not llabels == lcalibration:
            return(State.Disable,
                   "Bad configuration of the extra attributes, this cannot be operated")
        else:
            dev_state = dev_proxy.state()
            if readFailed and not dev_state == DevState.MOVING:
                return (State.Alarm,
                        "Fault on read attibute.\nThe tango device status says: %s"%dev_proxy.status())
            # IF PROXY DEVICE IS IN FAULT, MASK IT AS 'ALARM' AND INFORM IN STATUS
            state = dev_proxy.state()
            status = dev_proxy.status()
            if state in (DevState.FAULT, DevState.UNKNOWN):
                status = 'Masked ALARM state, tango device is in %s state with status: %s' % (state, status)
                state = State.Alarm
            else:
                state = from_tango_state_to_state(state)
            return (state, status)

    def ReadOne(self, axis):
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        dev_proxy = self.devsExtraAttributes[axis][DPROXY] or self._buildProxy(axis)
        llabels = len(self.devsExtraAttributes[axis][LABELS])
        positions = self.devsExtraAttributes[axis][POSITIONS]
        calibration = self.devsExtraAttributes[axis][CALIBRATION]
        lcalibration = len(calibration)
        try:
            value = dev_proxy.read_attribute(attr).value
            self.devsExtraAttributes[axis][READFAILED] = False
            #case 0: nothing to translate, only round about integer the attribute value
            if llabels == 0:
                return int(value)
            #case 1: only uses the labels. Available positions in POSITIONS
            elif lcalibration == 0:
                value = int(value)
                try: positions.index(value)
                except: raise Exception("Invalid position.")
                else: return value
            #case 1+fussy: the read from the attribute must be in one of the 
            #              defined ranges, and the IOR position is defined in labels
            elif llabels == lcalibration:
                for fussyPos in calibration:
                    if value >= fussyPos[0] and value <= fussyPos[2]:
                        return positions[calibration.index(fussyPos)]
                #if the loop ends, current value is not in the fussy areas.
                self.devsExtraAttributes[axis][READFAILED] = True
                raise Exception("Invalid position.")
            else:
                raise Exception("Bad configuration on optional extra attributes.")
        except Exception,e:
            self._log.error('Exception reading attribute:%s.%s'
                            %(self.devsExtraAttributes[axis][DEVICE],attr))
            try: self.devsExtraAttributes[axis][READFAILED] = True
            except: pass

    def WriteOne(self, axis, value):
        #If Labels is well defined, the write value must be one this struct
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        dev_proxy = self.devsExtraAttributes[axis][DPROXY] or self._buildProxy(axis)
        llabels = len(self.devsExtraAttributes[axis][LABELS])
        positions = self.devsExtraAttributes[axis][POSITIONS]
        calibration = self.devsExtraAttributes[axis][CALIBRATION]
        lcalibration = len(calibration)
        try:
            dev = self.devsExtraAttributes[axis][DEVICE]#to be removed after debug
            #case 0: nothing to translate, what is written goes to the attribute
            if llabels == 0:
                dev_proxy.write_attribute(attr, value)
            #case 1: only uses the labels. Available positions in POSITIONS
            elif lcalibration == 0:
                self._log.debug("%s value = %s"%(dev,value))
                try: positions.index(value)
                except: raise Exception("Invalid position.")
                dev_proxy.write_attribute(attr, value)
            #case 1+fussy: the write to the to the IOR is translated to the 
            #              central position of the calibration.
            elif llabels == lcalibration:
                self._log.debug("%s value = %s"%(dev,value))
                try: ior_destination = positions.index(value)
                except: raise Exception("Invalid position.")
                self._log.debug("%s ior_destination = %s"%(dev,ior_destination))
                calibrated_position = calibration[ior_destination][1]#central element
                self._log.debug("%s calibrated_position = %s"%(dev,calibrated_position))
                dev_proxy.write_attribute(attr,calibrated_position)
        except Exception, e:
            self._log.error('Exception writing attribute:%s.%s'
                            %(self.devsExtraAttributes[axis][DEVICE],attr))

    ####
    # Auxiliar methods for the extra attributes

    def getTangoAttribute(self,axis):
        return self.devsExtraAttributes[axis][TANGO_ATTR]

    def setTangoAttribute(self,axis,value):
        self.devsExtraAttributes[axis][TANGO_ATTR] = value
        idx = value.rfind("/")
        dev = value[:idx]
        attr = value[idx+1:]
        self.devsExtraAttributes [axis][DEVICE] = dev
        try: self.devsExtraAttributes[axis][DPROXY] = self._buildProxy(axis)
        except: self.devsExtraAttributes[axis][DPROXY] = None
        self.devsExtraAttributes[axis][ATTRIBUTE] = attr

    def _buildProxy(self,axis):
        '''Try to create a device proxy, or return None to mark it (to try when available).'''
        try:
            return PoolUtil().get_device(self.inst_name, self.devsExtraAttributes[axis][DEVICE])
        except:
            msg = "Cannot create the proxy for the device %s (axis %d)"%(self.devsExtraAttributes[axis][DEVICE],axis)
            self._log.warn(msg)
            raise DevFailed(msg)

    def getLabels(self,axis):
        #hackish until we support DevVarDoubleArray in extra attrs
        labels = self.devsExtraAttributes[axis][LABELS]
        positions = self.devsExtraAttributes[axis][POSITIONS]
        labels_str = ""
        for i in range(len(labels)):
            labels_str += "%s:%d "%(labels[i],positions[i])
        return labels_str[:-1]#remove the final space

    def setLabels(self,axis,value):
        #hackish until we support DevVarStringArray in extra attrs
        labels = []
        positions = []
        for pair in value.split():
            l,p = pair.split(':')
            labels.append(l)
            positions.append(int(p))
        if len(labels) == len(positions):
            self.devsExtraAttributes[axis][LABELS] = labels
            self.devsExtraAttributes[axis][POSITIONS] = positions
        else:
            raise Exception("Rejecting labels: invalid structure")

    def getCalibration(self,axis):
        return json.dumps(self.devsExtraAttributes[axis][CALIBRATION])

    def setCalibration(self,axis,value):
        try:
            self.devsExtraAttributes[axis][CALIBRATION] = json.loads(value)
        except:
            raise Exception("Rejecting calibration: invalid structure")

    # end aux for extras
    ####
