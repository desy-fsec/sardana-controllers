""" The standard pseudo counter controller library for the device pool """ 

from pool import PseudoCounterController, PoolUtil

from math import *

try:
    import scipy
    __SCIPY_AVAILABLE__ = True
except:
    __SCIPY_AVAILABLE__ = False
    
# Will disapear when we have pseudo counters that can have other pseudo counters
# in their counter roles.
class MCA2SCACtrl(PseudoCounterController):
    """ A counter controller which receives an MCA Spectrum und return a single value"""

    # NO COUNTERS NEEDED
    counter_roles = ()

    # THE EXTRA ATTRIBUTES: RoIs definition
    
    ctrl_extra_attributes ={'RoI1':
                            {'Type':'PyTango.DevLong'
                             ,'Description':'The low limit of the Region of Interest '
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            ,'RoI2':
                            {'Type':'PyTango.DevLong'
                             ,'Description':'The upper limit of the Region of Interest'
                             ,'R/W Type':'PyTango.READ_WRITE'}
                            }

    
    class_prop = { 'MCADevice' : { 'Description' : 'the MCA device name (or alias)','Type' : 'PyTango.DevString'} }

    def __init__(self,inst,props):
        
        PseudoCounterController.__init__(self,inst,props)

# En caso de que el device no fuese del pool        
#        self.device_proxy = PyTango.DeviceProxy(self.MCADevice)
# Si el device es del pool
        self.device_proxy = PoolUtil().get_device(self.inst_name,self.MCADevice)
        self.counterExtraAttributes = {}
        self.counterExtraAttributes[1] = {"RoI1":0,
                                          "RoI2":0}
    
    def GetExtraAttributePar(self,index,name):
        # IMPLEMENTED THE EXTRA ATTRIBUTE 'Formula','ExternalAttribute'
        print "GetExtraAttributePar " + str(index) + " name " + name
        return self.counterExtraAttributes[1][name]

    def SetExtraAttributePar(self,counter,name,value):
        # IMPLEMENTED THE EXTRA ATTRIBUTE 'Formula'
        print "GetExtraAttributePar " + str(counter) + " name " + name + " value " + str(value)
        self.counterExtraAttributes[1][name] = value

    def calc(self,index,counter_values):
        sum = 0
        try:
            data = self.device_proxy.read_attribute( "Value")
        except:
            data = self.device_proxy.read_attribute( "Data")
        for i in range(self.counterExtraAttributes[1]['RoI1'],self.counterExtraAttributes[1]['RoI2']):
            sum = sum + data.value[i]
        return float(sum)
