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

from PyTango import DevState
from pool import IORegisterController
from pool import PoolUtil

TANGO_ATTR = 'TangoAttribute'
DEVICE = 'Device'
#DPROXY = 'DeviceProxy'
ATTRIBUTE = 'Attribute'
CALIBRATION = 'Calibration'
LABELS = 'Labels'
READFAILED = 'readFailed'
VALUELABEL = 'ValueLabel'

def agrupate(l,n):
    #print "agrupate(%s,%s) "%(l,n)
    res = []
    if not len(l)%n == 0: raise Exception("Impossible for this length.")
    for i in range(len(l)/n):
        sub = []
        for j in range(n):
            sub.append(l[(i*n)+j])
        res.append(sub)
    return res

def flatten(l):
    #print "flatten(%s) "%(l)
    result = []
    for el in l:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result


class TangoAttrIORController(IORegisterController):
    """This controller offers as many IORegisters as the user wants.
    Each IORegisters _MUST_HAVE_ extra attributes:
    +) TangoAttribute - Tango attribute to retrieve the value of the IORegister
    As examples you could have:
    ch1.TangoExtraAttribute = 'my/tango/device/attribute1'
    ch2.TangoExtraAttribute = 'my/tango/device/attribute2'
    ch3.TangoExtraAttribute = 'my_other/tango/device/attribute1'
    Each IORegisters _MAY_HAVE_ extra attributes:
    +) Calibration - String of the triples min,cal,max
    As examples you could have:
    ch1.Calibration = "-50 0 50 950 1000 1050 1950 2000 2050 2950 3000 3050 3950 4000 4050 4950 5000 5050"
    That means: [[-50.0, 0.0, 50.0],
                 [950.0, 1000.0, 1050.0],
                 [1950.0, 2000.0, 2050.0],
                 [2950.0, 3000.0, 3050.0],
                 [3950.0, 4000.0, 4050.0],
                 [4950.0, 5000.0, 5050.0]]
    +) Labels - Human readable way to understand the positions. This is what
                the user will know about positions.
    As examples you have:
    ch1.Labels: "16.66% 33.33% 50% 66.66% 83.33% 100%"
    That means: {0:'16.66%',1:'33.33%',2:'50%',3:'66.66%',4:'83.33%',5'100%']
    Another extra attibute will be usable if the IORegisters is well configured:
    ValueLabel: string based attribute to move the IORegister using an string 
                (it must correspond with the Labels list)
    """

    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    ctrl_extra_attributes ={TANGO_ATTR:
                            {'Type':'PyTango.DevString',
                             'Description':'The first Tango Attribute to read (e.g. my/tango/dev/attr)',
                             'R/W Type':'PyTango.READ_WRITE'},
                            CALIBRATION:#type hackish until arrays supported
                            {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarDoubleArray',
                             'Description':'Flatten list of a list of triples and [min,cal,max]',
                             'R/W Type':'PyTango.READ_WRITE'},
                            LABELS:#type hackish until arrays supported
                            {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarStringArray',
                             'Description':'String list with the meaning of each discrete position',
                             'R/W Type':'PyTango.READ_WRITE'},
                            VALUELABEL:
                            {'Type':'PyTango.DevString',
                             'Description':'String to move the discrete motor in terms of the label.',
                             'R/W Type':'PyTango.READ_WRITE'},
                           }
    MaxDevice = 1024

    def __init__(self, inst, props):
        IORegisterController.__init__(self, inst, props)
        self.devsExtraAttributes = {}

    def AddDevice(self, axis):
        self._log.debug('AddDevice %d' % axis)
        self.devsExtraAttributes[axis] = {}
        self.devsExtraAttributes[axis][TANGO_ATTR] = None
        self.devsExtraAttributes[axis][CALIBRATION] = []
        self.devsExtraAttributes[axis][LABELS] = []
        #When the ReadOne raise an exception, inform the state
        self.devsExtraAttributes[axis][READFAILED] = False

    def DeleteDevice(self, axis):
        del self.devsExtraAttributes[axis]

    def StateOne(self, axis):
        tango_attr = self.devsExtraAttributes[axis][TANGO_ATTR]
        llabels = len(self.devsExtraAttributes[axis][LABELS])
        lcalibration = len(self.devsExtraAttributes[axis][CALIBRATION])
        readFailed = self.devsExtraAttributes[axis][READFAILED]
        if tango_attr == None:
            return (DevState.DISABLE,
                    "Not yet configured the Tango Attribute")
        if not llabels == lcalibration:
            return(DevState.DISABLE,
                   "Bad configuration of the extra attributes, this cannot be operated")
        else:
            dev_proxy = self._buildProxy(axis)
            dev_state = dev_proxy.state()
            if readFailed and not dev_state == DevState.MOVING:
                return (DevState.ALARM,
                        "Fault on read attibute.\nThe tango device status says: %s"%dev_proxy.status())
            return (dev_proxy.state(),
                    "The tango device status says: %s"%dev_proxy.status())

        

    def ReadOne(self, axis):
        dev = self.devsExtraAttributes[axis][DEVICE]
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        dev_proxy = self._buildProxy(axis)
        if dev_proxy == None: return #anything can be done
        labels = self.devsExtraAttributes[axis][LABELS]
        llabels = len(labels)
        calibration = self.devsExtraAttributes[axis][CALIBRATION]
        lcalibration = len(calibration)
        try:
            if llabels == 0 and lcalibration == 0:
                value = dev_proxy.read_attribute(attr).value
                self.devsExtraAttributes[axis][READFAILED] = False
                return int(value)
            elif llabels == lcalibration:
                value = dev_proxy.read_attribute(attr).value
                for fussyPos in calibration:
                    if value >= fussyPos[0] and value <= fussyPos[2]:
                        self.devsExtraAttributes[axis][READFAILED] = False
                        return int(calibration.index(fussyPos))
                self.devsExtraAttributes[axis][READFAILED] = True
                raise Exception("Invalid position.")
            else:
                raise Exception("Bad configuration on optional extra attributes.")
        except Exception,e:
            self._log.error('Exception reading attribute:%s.%s' % (dev,attr))
            try: self.devsExtraAttributes[axis][READFAILED] = True
            except: pass

    def WriteOne(self, axis, value):
        dev = self.devsExtraAttributes[axis][DEVICE]
        attr = self.devsExtraAttributes[axis][ATTRIBUTE]
        dev_proxy = self._buildProxy(axis)
        labels = self.devsExtraAttributes[axis][LABELS]
        llabels = len(labels)
        calibration = self.devsExtraAttributes[axis][CALIBRATION]
        lcalibration = len(calibration)
        try:
            if llabels == 0 and lcalibration == 0:
                dev_proxy.write_attribute(attr, value)
            elif llabels == lcalibration:
                if value >= len(labels): raise Exception("Out of range.")
                dev_proxy.write_attribute(attr,calibration[value][1])
        except Exception, e:
            self._log.error('Exception writing attribute:%s.%s' % (dev,attr))

    def GetExtraAttributePar(self, axis, name):
        #case to apply the correspondant method per each extra attr
        return {TANGO_ATTR:self.getTangoAttr,
                CALIBRATION:self.getCalibration,
                LABELS:self.getLabels,
                VALUELABEL:self.getValueLabel,
               }[name](axis,name)
        

    def SetExtraAttributePar(self,axis, name, value):
        self._log.debug('SetExtraAttributePar [%d] %s = %s' % (axis, name, value))
        #case to apply the correspondant method per each extra attr
        {TANGO_ATTR:self.setTangoAttr,
         CALIBRATION:self.setCalibration,
         LABELS:self.setLabels,
         VALUELABEL:self.setValueLabel,
        }[name](axis,name,value)

    def SendToCtrl(self,in_data):
        return ""

    ####
    # Auxiliar methods for the extra attributes

    def getTangoAttr(self,axis,name):
        return self.devsExtraAttributes[axis][name]

    def setTangoAttr(self,axis,name,value):
        self.devsExtraAttributes[axis][name] = value
        idx = value.rfind("/")
        dev = value[:idx]
        attr = value[idx+1:]
        self.devsExtraAttributes[axis][DEVICE] = dev
        #self.devsExtraAttributes[axis][DPROXY] = self._buildProxy(axis)
        self.devsExtraAttributes[axis][ATTRIBUTE] = attr
    def _buildProxy(self,axis):
        '''Try to create a device proxy, or return None to mark it (to try when available).'''
        try:
            return PoolUtil().get_device(self.inst_name, self.devsExtraAttributes[axis][DEVICE])
        except:
            self._log.warn("Cannot create the proxy for the device %s (axis %d)"%(self.devsExtraAttributes[axis][DEVICE],axis))
            return None

    def getCalibration(self,axis,name):
        bar = "".join("%s "%e for e in flatten(self.devsExtraAttributes[axis][CALIBRATION]))
        return bar[:-1]
        #hackish until we support DevVarDoubleArray in extra attrs
        #return flatten(self.devsExtraAttributes[axis][CALIBRATION])

    def setCalibration(self,axis,name,value):
        #hackish until we support DevVarDoubleArray in extra attrs
        value = value.split()
        for i in range(len(value)): value[i] = float(value[i])
        self.devsExtraAttributes[axis][CALIBRATION] = agrupate(value,3)

    def getLabels(self,axis,name):
        bar = "".join("%s "%e for e in self.devsExtraAttributes[axis][LABELS])
        return bar[:-1]
        #hackish until we support DevVarDoubleArray in extra attrs
        #return self.devsExtraAttributes[axis][LABELS]

    def setLabels(self,axis,name,value):
        #hackish until we support DevVarStringArray in extra attrs
        value = value.split()
        self.devsExtraAttributes[axis][LABELS] = value

    def getValueLabel(self,axis,name):
        IOR_value = self.ReadOne(axis)
        return self.devsExtraAttributes[axis][LABELS][IOR_value]

    def setValueLabel(self,axis,name,value):
        try:
            IOR_value = self.devsExtraAttributes[axis][LABELS].index(value)#find the string in the list of labels
            self.WriteOne(axis, IOR_value)
        except:
            return "Invalid position"#if is not in the list

    # end aux for extras
    ####
