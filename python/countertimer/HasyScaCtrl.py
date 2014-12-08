import PyTango
from sardana.pool.controller import CounterTimerController
import time, os


from sardana import State, DataAccess
from sardana.pool.controller import MotorController
from sardana.pool.controller import Type, Access, Description, DefaultValue
from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class HasyScaCtrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the HasySca"
#    axis_attributes = {'Offset':{Type:float,Access:ReadWrite}}
                 
    class_prop = {'mca':{Type:str,Description:'The MCA name, tango device'},
                  'roi1':{Type:str,Description:'The lower ROI limit'},
                  'roi2':{Type:str,Description:'The upper ROI limit'},
                  }
      
    gender = "CounterTimer"
    model = "HasySca"
    organization = "DESY"
    state = ""
    status = ""
    
    def __init__(self,inst,props, *args, **kwargs):
        CounterTimerController.__init__(self,inst,props, *args, **kwargs)
        self.max_device = 1
        self.tango_device = [None]
        self.proxy = [ None]
        self.device_available = [0]
        self.started = False
        self.debugFlag = False
        if os.isatty(1): 
            self.debugFlag = True


    def AddDevice(self,ind):
        CounterTimerController.AddDevice(self,ind)
        if self.debugFlag: print "HasyScaCtrl.AddDevice %s %s %s index %d" % (self.mca, self.roi1, self.roi2, ind)
        if ind > self.max_device:
            print "HasyScaCtrl wrong index"
            return
        self.proxy[ind-1] = PyTango.DeviceProxy( self.mca)
        self.device_available[ind-1] = 1
        
        
    def DeleteDevice(self,ind):
        if self.debugFlag: print "HasyScaCtrl.DeleteDevice", self.inst_name, "index", ind
        CounterTimerController.DeleteDevice(self,ind)
        self.proxy[ind-1] =  None
        self.device_available[ind-1] = 0
        
        
    def StateOne(self,ind):
        if self.debugFlag: print "HasyScaCtrl.StateOne", self.inst_name, "index", ind
        if  self.device_available[ind-1] == 1:
            #
            # at this point the state of the mca-controller somehow stays MOVING
            #
            sta = self.proxy[ind-1].State()
            sta = PyTango.DevState.ON
            tup = (sta, "Message from HasyScaCtrl")
            return tup

    def PreReadAll(self):
        if self.debugFlag: print "HasyScaCtrl.PreReadAll", self.inst_name
        pass
        
    def PreReadOne(self,ind):
        if self.debugFlag: print "HasyScaCtrl.PreReadOne", self.inst_name, "index", ind
        pass

    def ReadAll(self):
        if self.debugFlag: print "HasyScaCtrl.ReadAll", self.inst_name
        pass

    def ReadOne(self,ind):
        if self.debugFlag: print "HasyScaCtrl.readOne", self.inst_name, "index", ind
        if self.device_available[ind-1] == 0:
            return False
        if self.proxy[ind-1].BankId != 0:
            print "HasyScaCtrl, BankId != 0 (%d) for %s" % (self.proxy[ind-1].BankId, self.proxy[ind-1].name())
            self._log.error( "HasyScaCtrl, BankId != 0 (%d) for %s" % (self.proxy[ind-1].BankId, self.proxy[ind-1].name()))
            return 0

        if self.proxy[ind-1].StateBank0 != 0:
            if self.debugFlag: print "HasyScaCtrl.readOne Stop and Read "
            self.proxy[ind-1].Stop()
            self.proxy[ind-1].Read()
        data = self.proxy[ind-1].Data
        sum = 0
        for i in range( int(self.roi1), int(self.roi2)):
            sum += data[i]
        return sum
    
    def AbortOne(self,ind):
        if self.debugFlag: print "HasyScaCtrl.AbortOne", self.inst_name, "index", ind
        return True
        
    def PreStartAllCT(self):
        if self.debugFlag: print "HasyScaCtrl.PreStartAllCT", self.inst_name
        self.wantedCT = []

    def PreStartOneCT(self,ind):
        if self.debugFlag: print "HasyScaCtrl.PreStartOne", self.inst_name, "index", ind
        return True
        
    def StartOneCT(self,ind):
        if self.debugFlag: print "HasyScaCtrl.StartOneCT", self.inst_name, "index", ind
        self.wantedCT.append(ind)
    
    def StartAllCT(self):
        if self.debugFlag: print "HasyScaCtrl.StartAllCT", self.inst_name
        self.started = True
        self.start_time = time.time()
        return True
                
    def LoadOne(self,ind,value):
        if self.debugFlag: print "HasyScaCtrl.LoadOne", self.inst_name, "index", ind
        pass
    
    def GetExtraAttributePar(self,ind,name):
        if self.debugFlag: print "HasyScaCtrl.GetExtraAttr", self.inst_name, "index", ind
        if name == "Offset":
            if self.device_available[ind-1]:
                return float(self.proxy[ind-1].read_attribute("Offset").value)
        
            
    def SetExtraAttributePar(self,ind,name,value):
        if self.debugFlag: print "HasyScaCtrl.SetExtraAttr", self.inst_name, "index", ind
        if name == "Offset":
            if self.device_available[ind-1]:
                self.proxy[ind-1].write_attribute("Offset",value)
            
    def SendToCtrl(self,in_data):
        if self.debugFlag: print "HasyScaCtrl.SendToCtrl"
        return "Nothing sent"

    def start_acquisition(self, value=None):
        if self.debugFlag: print "HasyScaCtrl.start_acq", self.inst_name
        return True
    
    def __del__(self):
        if self.debugFlag: print "PYTHON -> HasyScaCtrl/",self.inst_name,": dying"

 
if __name__ == "__main__":
    obj = HasyScaCtrl('test')
