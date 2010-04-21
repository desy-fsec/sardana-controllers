#############################################################################
##
## file :    AttenuatorOICtrl.py
##
## description : 
##
## project :    Sardana/Pool/ctrls/OIRegister
##
## developers history: sblanch
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

from PyTango import DevState,EventType
from pool import IORegisterController
from pool import PoolUtil

from math import * #to evaluate the formula

#EXTRA ATTRIBUTES and auxiliars of each
#with the underscore to diferenciate to the used in the formula: THICKNESS, ENERGY, DENSITY
_LABELS = 'Labels'

_VALVE = 'Valve'
_VALVE_DEVICE = 'valve_dname'
_VALVE_ATTRIBUTE = 'valve_aname'
_VALVE_DPROXY = 'valve_dproxy'

_FORMULA = 'AbsortionFormula'
_FOILS = 'Foils_Thickness'
_FOIL = 'CurrentFoil_Thickness'
_DENSITIES = 'Foils_Density'
_DENSITY = 'CurrentFoil_Density'
_ABSORTIONS = 'Foils_Absortion'
_ABSORTION = 'CurrentFoil_Absortion'
_ENERGY = 'EnergyAttribute'
_ENERGY_DEVICE = 'Energy_dname'
_ENERGY_ATTRIBUTE = 'Energy_aname'
#_ENERGY_DPROXY = 'Energy_dproxy'
_ENERGY_EVENT = 'Energy_event'
_ENERGY_VALUE = 'Energy_value'

_ARMS = 'Arms'
_ARMS_DEVICE = 'Arms_device'
_ARMS_ATTRIBUTE = 'Arms_attr'
_ARMS_LABELS = 'Arms_Labels'
_ARMS_DPROXY = 'Arms_proxies'

####
# lower level auxiliar methods
def cutDevAttrStr(name):
    """Given a complete name of an attr, return the pair (dev,attr)"""
    nslash = name.count("/")
    if nslash == 3 or nslash == 1:
        idx = name.rfind("/")
        return name[:idx],name[idx+1:]
    else: return name,None
# end lower level
####

class AttenuatorIOCtrl(IORegisterController):
    """This is a particular IORegister for an arm of attenuators.
       Each channel _MUST_HAVE_ some extra attributes:
       *) Valve: the element that this will move
       Each channel _SHOULD_HAVE_ some extra attributes:
       *) Labels: User readable tag for each position
       *) EnergyAttribute: From where is take the energy value to know the attenuation
       *) AbsortionFormula: 
       *) Foils_Thickness:
       *) Foils_Density:
    """
    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    #@todo: check the units
    ctrl_extra_attributes = {
                             ## READ_WRITE extra attrs:
                             _LABELS:#type hackish until arrays supported
                              {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarStringArray',
                              'Description':'String list as user readable tag for each position',
                              'R/W Type':'PyTango.READ_WRITE'},
                             _VALVE:
                              {'Type':'PyTango.DevString',
                              'Description':'Attribute for a discrete motor position (e.g. my/tango/dev/attr) even a ioregister or a PLCValve',
                              'R/W Type':'PyTango.READ_WRITE'},
                             _ENERGY:
                              {'Type':'PyTango.DevString',
                              'Description':'The Tango Attribute to read the energy value in eV (e.g. my/tango/dev/attr)',
                              'R/W Type':'PyTango.READ_WRITE'},
                             _FORMULA:
                              {'Type':'PyTango.DevString',
                              'Description':'String with the formula to know the attenuation, keywords \'THICKNESS\', \'ENERGY\' and \'DENSITY\'.',
                              'R/W Type':'PyTango.READ_WRITE'},
                             _FOILS:#type hackish until arrays supported
                              {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarDoubleArray',
                              'Description':'List of thicknesses of the foils (in micrometers)',
                              'R/W Type':'PyTango.READ_WRITE'},
                             _DENSITIES:#type hackish until arrays supported
                              {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarDoubleArray',
                              'Description':'List of desities of the foils (in __unit__)',
                              'R/W Type':'PyTango.READ_WRITE'},
                             ## READ_ONLY extra attrs:
                             _FOIL:
                              {'Type':'PyTango.DevDouble',
                              'Description':'Thickness of the current foil (in micrometers)',
                              'R/W Type':'PyTango.READ'},
                             _DENSITY:
                              {'Type':'PyTango.DevDouble',
                              'Description':'Desity of the current foil (in __unit__)',
                              'R/W Type':'PyTango.READ'},
                             _ABSORTIONS:
                              {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarDoubleArray',
                              'Description':'List of computed absortions of the foils (in __unit__)',
                              'R/W Type':'PyTango.READ'},
                             _ABSORTION:
                              {'Type':'PyTango.DevDouble',#{'Type':'PyTango.DevVarDoubleArray',
                              'Description':'Computed absortion of the current foil (in __unit__)',
                              'R/W Type':'PyTango.READ'},
                            }

    MaxDevice = 1024

    def __init__(self, inst, props):
        IORegisterController.__init__(self, inst, props)
        self._log.debug("AttenuatorIOCtrl::__init__(%s,%s) "%(inst,props))
        self.devsExtraAttributes = {}
        self.revers_EnergyAttr2axis = {} #used in push_event

    def AddDevice(self, axis):
        self._log.debug("AttenuatorIOCtrl::AddDevice(%s) "%(axis))
        self.devsExtraAttributes[axis] = {}
        self.devsExtraAttributes[axis][_LABELS] = []
        self.devsExtraAttributes[axis][_VALVE] = None
        self.devsExtraAttributes[axis][_ENERGY] = None
        self.devsExtraAttributes[axis][_FORMULA] = None
        self.devsExtraAttributes[axis][_FOILS] = []
        self.devsExtraAttributes[axis][_DENSITIES] = []
        self.devsExtraAttributes[axis][_ABSORTIONS] = []

    def DeleteDevice(self, axis):
        self._log.debug("AttenuatorIOCtrl::DeleteDevice(%s) "%(axis))
        if self.devsExtraAttributes[axis].has_key(_ENERGY_EVENT):
            dev = dev,attr = cutDevAttrStr(self.devsExtraAttributes[axis][_ENERGY_ATTRIBUTE])
            dproxy = PoolUtil().get_device(self.inst_name, dev)
            dproxy.unsubscribe_event(self.devsExtraAttributes[axis][_ENERGY_EVENT])
        del self.devsExtraAttributes[axis]
    
    def StateOne(self, axis):
        self._log.debug("AttenuatorIOCtrl::StateOne(%s) "%(axis))
        if self.devsExtraAttributes[axis][_VALVE] == None:
            return (DevState.DISABLE,
                    "Not yet configured the %s Attribute"%_VALVE)
        else:
            return (self.devsExtraAttributes[axis][_VALVE_DPROXY].state(),
                    "The valve status says: %s"%self.devsExtraAttributes[axis][_VALVE_DPROXY].status())

    def ReadOne(self, axis):
        self._log.debug("AttenuatorIOCtrl::ReadOne(%s) "%(axis))
        try:
            return int(self.devsExtraAttributes[axis][_VALVE_DPROXY].read_attribute(self.devsExtraAttributes[axis][_VALVE_ATTRIBUTE]).value)
        except Exception,e:
            self._log.error('Exception reading attribute Value on axis %d' %(axis))
            print "%s"%e
            raise Exception('Invalid')

    def WriteOne(self, axis, value):
        self._log.debug("AttenuatorIOCtrl::WriteOne(%s,%s) "%(axis,value))
        try:
            self.devsExtraAttributes[axis][_VALVE_DPROXY].write_attribute(self.devsExtraAttributes[axis][_VALVE_ATTRIBUTE],value)
        except Exception, e:
            self._log.error('Exception writing attribute Value on axis %d' %(axis))

    def GetExtraAttributePar(self, axis, name):
        self._log.debug("AttenuatorIOCtrl::GetExtraAttributePar(%s,%s) "%(axis,name))
        case = {_LABELS:self.getterStringList,
                _VALVE:self.getValve,
                _ENERGY:self.getEnergy,
                _FORMULA:self.getFormula,
                _FOILS:self.getterStringList,#will be double
                _DENSITIES:self.getterStringList,#will be double
                _FOIL:self.getCurrentFoil,
                _DENSITY:self.getCurrentDensity,
                _ABSORTIONS:self.getterStringList,#will be double
                _ABSORTION:self.getCurrentAbsortion,
               }
        return case.get(name,self.getterDefault)(axis,name)

    def SetExtraAttributePar(self, axis, name, value):
        self._log.debug("AttenuatorIOCtrl::SetExtraAttributePar(%s,%s,%s) "%(axis,name,value))
        case = {_LABELS:self.setterStringList,
                _VALVE:self.setValve,
                _ENERGY:self.setEnergy,
                _FORMULA:self.setFormula,
                _FOILS:self.setFoils,
                _DENSITIES:self.setDensities,
               }
        case.get(name,self.setterDefault)(axis,name,value)

    def SendToCtrl(self, in_data):
        return "Adios"

    ####
    # Auxiliar methods for the extra attributes
    def getterDefault(self,axis,name):
        self._log.warn("Ignoring the GET on the %s extra attr"%name)
        return None
    def setterDefault(self,axis,name,value):
        self._log.warn("Ignoring the SET on the %s extra attr"%name)
    
    def getterStringList(self,axis,name):
        """Common method for all the extra attr, that converts lists to strings."""
        try:
            bar = "".join("%s "%e for e in self.devsExtraAttributes[axis][name])
            return bar[:-1]
        except: return ""
        #hackish until we support DevVarStringArray in extra attrs
        #return self.devsExtraAttributes[axis][name]
    def setterStringList(self,axis,name,value):
        #hackish until we support DevVarStringArray in extra attrs
        value = value.split()
        self.devsExtraAttributes[axis][name] = value
    
    def getValve(self,axis,name):
        return self.devsExtraAttributes[axis][name] or ""
    def setValve(self,axis,name,value):
        self.devsExtraAttributes[axis][name] = value
        dev,attr = cutDevAttrStr(value)
        self.devsExtraAttributes[axis][_VALVE_DEVICE] = dev
        self.devsExtraAttributes[axis][_VALVE_ATTRIBUTE] = attr
        self.devsExtraAttributes[axis][_VALVE_DPROXY] = PoolUtil().get_device(self.inst_name, dev)
        self.refreshLabels(axis)
    
    def getEnergy(self,axis,name):
        return self.devsExtraAttributes[axis][name] or ""
    def setEnergy(self,axis,name,value):
        self.devsExtraAttributes[axis][name] = value
        try:
            dev,attr = cutDevAttrStr(value)
            self.devsExtraAttributes[axis][_ENERGY_DEVICE] = dev
            self.devsExtraAttributes[axis][_ENERGY_ATTRIBUTE] = attr
            dproxy = PoolUtil().get_device(self.inst_name, dev)
            self.revers_EnergyAttr2axis[value] = axis#value is non dictionary way to mention _ENERGY.
            self.devsExtraAttributes[axis][_ENERGY_EVENT] = dproxy.subscribe_event(attr,EventType.CHANGE_EVENT,self,[],True)
        except Exception,e:
            self._log.warn("AttenuatorIOCtrl::setEnergy Exception setting the Energy attribute for %s"%event.attr_name)
    
    def getFormula(self,axis,name):
        return self.devsExtraAttributes[axis][name] or ""
    def setFormula(self,axis,name,value):
        #hackish until we support DevVarStringArray in extra attrs
        self.devsExtraAttributes[axis][name] = value
        self.refreshLabels(axis)
    
    def setFoils(self,axis,name,value):
        self.devsExtraAttributes[axis][name] = map(float,value.split())
        self.refreshLabels(axis)
        
    def setDensities(self,axis,name,value):
        self.devsExtraAttributes[axis][name] = map(float,value.split())
        self.refreshLabels(axis)
        
    def getCurrentLabel(self,axis,name):
        try: return self.devsExtraAttributes[axis][_LABELS][self.ReadOne(axis)]
        except: raise Exception("Cannot read label")
    def getCurrentFoil(self,axis,name):
        try: return self.devsExtraAttributes[axis][_FOILS][self.ReadOne(axis)]
        except: raise Exception("Cannot read Foil")
    def getCurrentDensity(self,axis,name):
        try: return self.devsExtraAttributes[axis][_DENSITIES][self.ReadOne(axis)]
        except: raise Exception("Cannot read density")
    def getCurrentAbsortion(self,axis,name):
        try: return self.devsExtraAttributes[axis][_ABSORTIONS][self.ReadOne(axis)]
        except: raise Exception("Cannot read absortion")

    def push_event(self,event):
        try:
            print("AttenuatorIOCtrl::push_event")
            axis = self.revers_EnergyAttr2axis[event.attr_name]
            self._log.debug("AttenuatorIOCtrl::push_event axis %d"%axis)
            self.devsExtraAttributes[axis][_ENERGY_VALUE] = event.attr_value.value
            self.refreshLabels(axis)
        except Exception,e:
            self._log.warn("AttenuatorIOCtrl::push_event Cannot manage the push_event for %s"%event.attr_name)
            print "%s"%e

    def refreshLabels(self,axis):
        try:
            foils = self.devsExtraAttributes[axis][_FOILS]
            densities = self.devsExtraAttributes[axis][_DENSITIES]
            if (not len(foils) == 0 or not len(densities) == 0) and not len(foils) == len(densities):
                raise Exception("Not well configured the extra attributes.")
            formula = self.devsExtraAttributes[axis][_FORMULA]
            labels = []
            for i in range(len(foils)):
                THICKNESS = foils[i]
                try: ENERGY = self.devsExtraAttributes[axis][_ENERGY_VALUE]
                except: pass
                DENSITY = densities[i]
                #just in case someone wrotes it like the attr
                Thickness = THICKNESS
                try: Energy = ENERGY
                except: pass
                Density = DENSITY
                labels.append(eval(formula))
            self.devsExtraAttributes[axis][_ABSORTIONS] = labels
        except Exception,e:
            self._log.warn("AttenuatorIOCtrl::refreshLabels Cannot eval the formula for axis %d"%axis)
    # end aux for extras
    ####


class GroupAttenuatorIOCtrl(IORegisterController):
    """This is a IORegister to group many attenuator arms as a single thing.
       Each channel _MUST_HAVE_ some extra attributes:
       *) Arms: list of elements to combine
       Each channel _SHOULD_HAVE_ some extra attributes:
       *) Labels: User readable tag for each position
    """
    gender = ""
    model  = ""
    organization = "CELLS - ALBA"
    image = ""
    icon = ""
    logo = "ALBA_logo.png"

    #@todo: check the units
    ctrl_extra_attributes = {
                             ## READ_WRITE extra attrs:
                             _LABELS:#type hackish until arrays supported
                              {'Type':'PyTango.DevString',#{'Type':'PyTango.DevVarStringArray',
                              'Description':'String list as user readable tag for each position',
                              'R/W Type':'PyTango.READ_WRITE'},
                             _ARMS:#todo: PyTango.DevVarStringArray
                              {'Type':'PyTango.DevString',
                              'Description':'List of the attenuator arms to combine',
                              'R/W Type':'PyTango.READ_WRITE'},
                             ## READ_ONLY extra attrs:
                             _FOIL:
                              {'Type':'PyTango.DevDouble',
                              'Description':'Thickness of the current foil (in micrometers)',
                              'R/W Type':'PyTango.READ'},
                             _ABSORTION:
                              {'Type':'PyTango.DevDouble',#{'Type':'PyTango.DevVarDoubleArray',
                              'Description':'Combined absortion for the current arms position (in __unit__)',
                              'R/W Type':'PyTango.READ'},
                            }

    MaxDevice = 1024

    def __init__(self, inst, props):
        IORegisterController.__init__(self, inst, props)
        self._log.debug("GroupAttenuatorIOCtrl::__init__(%s,%s) "%(inst,props))
        self.devsExtraAttributes = {}

    def AddDevice(self, axis):
        self._log.debug("GroupAttenuatorIOCtrl::AddDevice(%s) "%(axis))
        self.devsExtraAttributes[axis] = {}
        self.devsExtraAttributes[axis][_LABELS] = []
        self.devsExtraAttributes[axis][_ARMS] = []
        self.devsExtraAttributes[axis][_ABSORTION] = None

    def DeleteDevice(self, axis):
        self._log.debug("GroupAttenuatorIOCtrl::DeleteDevice(%s) "%(axis))
        del self.devsExtraAttributes[axis]

    def StateOne(self, axis):
        self._log.debug("GroupAttenuatorIOCtrl::StateOne(%s) "%(axis))
        if self.devsExtraAttributes[axis][_ARMS] == []:
            return (DevState.DISABLE,
                    "Not yet configured the %s Attribute"%_ARMS)
        else:
            return (DevState.ON,"")
            #@todo: combine the states and substates in the status
            #return (self.devsExtraAttributes[axis][_VALVE_DPROXY].state(),
            #        "The valve status says: %s"%self.devsExtraAttributes[axis][_VALVE_DPROXY].status())

    def ReadOne(self, axis):
        self._log.debug("GroupAttenuatorIOCtrl::ReadOne(%s) "%(axis))
        try:
            label = ""
            for i,dev in enumerate(self.devsExtraAttributes[axis][_ARMS_DPROXY]):
                armposition,armlabels = dev.read_attributes([self.devsExtraAttributes[axis][_ARMS_ATTRIBUTE][i],_LABELS])
                armposition = armposition.value
                armlabels = armlabels.value.split()
                label += "%s+"%armlabels[armposition]
            label = label[:-1]
            labels = self.getLabels(axis,_LABELS).split()
            return int(labels.index(label))
        except Exception,e:
            self._log.error('Exception reading attribute Value on axis %d' %(axis))
            print "%s"%e
            raise Exception('Invalid')

    def WriteOne(self, axis, value):
        self._log.debug("GroupAttenuatorIOCtrl::WriteOne(%s,%s) "%(axis,value))
        try:
            label = self.getLabels(axis,_LABELS).split()[value].split('+')
            for i,dev in enumerate(self.devsExtraAttributes[axis][_ARMS_DPROXY]):
                bar = dev.read_attribute(_LABELS).value.split()
                foo = bar.index(label[i])
                dev.write_attribute(self.devsExtraAttributes[axis][_ARMS_ATTRIBUTE][i],foo)
        except Exception, e:
            self._log.error('Exception writing attribute Value on axis %d' %(axis))
            print "%s"%e

    def GetExtraAttributePar(self, axis, name):
        self._log.debug("AttenuatorIOCtrl::GetExtraAttributePar(%s,%s) "%(axis,name))
        case = {_LABELS:self.getLabels,
                _ARMS:self.getArms,
                _FOIL:self.getCurrentFoil,
                _ABSORTION:self.getCurrentAbsortion,
               }
        return case.get(name,self.getterDefault)(axis,name)

    def SetExtraAttributePar(self, axis, name, value):
        self._log.debug("AttenuatorIOCtrl::SetExtraAttributePar(%s,%s,%s) "%(axis,name,value))
        case = {_LABELS:self.setterStringList,
                _ARMS:self.setArms,
               }
        case.get(name,self.setterDefault)(axis,name,value)

    def SendToCtrl(self, in_data):
        return "Adios"

    ####
    # Auxiliar methods for the extra attributes
    def getterDefault(self,axis,name):
        self._log.warn("Ignoring the GET on the %s extra attr"%name)
        return None
    def setterDefault(self,axis,name,value):
        self._log.warn("Ignoring the SET on the %s extra attr"%name)
    
    def getterStringList(self,axis,name):
        """Common method for all the extra attr, that converts lists to strings."""
        try:
            bar = "".join("%s "%e for e in self.devsExtraAttributes[axis][name])
            return bar[:-1]
        except: return ""
        #hackish until we support DevVarStringArray in extra attrs
        #return self.devsExtraAttributes[axis][name]
    def setterStringList(self,axis,name,value):
        #hackish until we support DevVarStringArray in extra attrs
        value = value.split()
        self.devsExtraAttributes[axis][name] = value

    def getArms(self,axis,name):
        self._log.debug("GroupAttenuatorIOCtrl::getArms(%s) "%(axis))
        bar = "".join("%s "%e for e in self.devsExtraAttributes[axis][name])
        return bar[:-1]
    def setArms(self,axis,name,value):
        self._log.debug("GroupAttenuatorIOCtrl::setArms(%s) "%(axis))
        value = value.split()
        self.devsExtraAttributes[axis][name] = value
        self.devsExtraAttributes[axis][_ARMS_DEVICE] = []
        self.devsExtraAttributes[axis][_ARMS_ATTRIBUTE] = []
        self.devsExtraAttributes[axis][_ARMS_DPROXY] = []
        for devattr in value:
            dev,attr = cutDevAttrStr(devattr)
            self.devsExtraAttributes[axis][_ARMS_DEVICE].append(dev)
            self.devsExtraAttributes[axis][_ARMS_ATTRIBUTE].append(attr)
            self.devsExtraAttributes[axis][_ARMS_DPROXY].append(PoolUtil().get_device(self.inst_name, dev))
        #@todo: ?anything to refresh

    def getLabels(self,axis,name):
        self._log.debug("GroupAttenuatorIOCtrl::getLabels(%s) "%(axis))
        labels = [dev.read_attribute(_LABELS).value.split() for dev in self.devsExtraAttributes[axis][_ARMS_DPROXY]]
        #return self.combine(self.forLabels,labels[0],labels[1])
        bar = "".join("%s "%e for e in self.combine(self.forLabels,labels[0],labels[1]))
        return bar[:-1]
    def setLabels(self,axis,name,value):
        self._log.debug("GroupAttenuatorIOCtrl::setLabels(%s) "%(axis))
        #raise Exception("Ignoring write operation")
        return ""

    def getCurrentFoil(self,axis,name):
        self._log.debug("GroupAttenuatorIOCtrl::setCurrentFoil(%s) "%(axis))
        accumulated = 0.0
        for dev in self.devsExtraAttributes[axis][_ARMS_DPROXY]:
            accumulated += dev.read_attribute(_FOIL).value
        return accumulated

    def getCurrentAbsortion(self,axis,name):
        self._log.debug("GroupAttenuatorIOCtrl::setCurrentAbsortion(%s) "%(axis))
        accumulated = 1.0
        for dev in self.devsExtraAttributes[axis][_ARMS_DPROXY]:
            accumulated *= dev.read_attribute(_ABSORTION).value/100.0
        return accumulated*100.0

    # end aux for extras
    ####

    ####
    # lower level auxiliar methods
    def combine(self,method,*args):
        try:
            first = args[0]
            second = args[1:]
            if len(second)>1:
                second = self.combine(method,*second)
            else: second = second[0]
            res = []
            for i in first:
                for j in second:
                    res.append(method(i,j))
            return res
        except: return args[0]
        
    def forLabels(self,i,j):
        return "".join("%s+%s"%(i,j))
    
    #def forPositions(self,i,j):
    #    return "".join("%s %s"%(i,j))
    
    # end lower level
    ####

if __name__ == "__main__":
    obj = AttenuatorIOCtrl('test')
