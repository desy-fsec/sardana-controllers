import PyTango
from pool import CounterTimerController
import time

class SIS3820Ctrl(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the VCT6"
    ctrl_extra_attributes = {'Offset':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'}}
			     
    class_prop = {'CtrlDevName':{'Type':'PyTango.DevString','Description':'The ctrl simulator Tango device name'}}
	
    MaxDevice = 9
	
    def __init__(self,inst,props):
        CounterTimerController.__init__(self,inst,props)
#        print "PYTHON -> SIS3820Ctrl ctor for instance",inst
		#	raise NameError,"Ouuups"
		
        self.ct_name = "SIS3820Ctrl/" + self.inst_name
        self.sis3820_ctrl = None
        self.sis3820_ctrl = PyTango.DeviceProxy(self.CtrlDevName)
        self.started = False
        self.dft_Offset = 0
        self.Offset = []
		
        try:
            self.sis3820_ctrl.ping()
        except:
            self.sis3820_ctrl = None
            raise


    def AddDevice(self,ind):
#		print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In AddDevice method for index",ind
		self.Offset.append(self.dft_Offset)
		
        
    def DeleteDevice(self,ind):
		print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In DeleteDevice method for index",ind
        
		
    def StateOne(self,ind):
		sta = self.sis3820_ctrl.command_inout("GetAxeStatus",ind)
		tup = (sta,"Status error string from controller")
		return tup

    def PreReadAll(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In PreReadAll method"
        pass
        

    def PreReadOne(self,ind):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In PreReadOne method for index",ind
        pass

    def ReadAll(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,ind):
#        print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In ReadOne method for index",ind
        if self.sis3820_ctrl != None:
            return self.sis3820_ctrl.command_inout("GetAxeCounts",ind)
        else:
            raise RuntimeError,"Ctrl Tango's proxy null!!!"
	
    def AbortOne(self,ind):
		pass
        
    def PreStartAllCT(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In PreStartAllCT method"
		self.wantedCT = []

    def PreStartOneCT(self,ind):	
		if self.sis3820_ctrl != None:
			self.sis3820_ctrl.command_inout("ResetAxe",ind)
			return True	
		else:
			raise RuntimeError,"Ctrl Tango's proxy null!!!"
			return False
		
    def StartOneCT(self,ind):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In StartOneCT method for index",ind
        self.wantedCT.append(ind)
	
    def StartAllCT(self):
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In StartAllCT method"
        self.started = True
        self.start_time = time.time()
		     	
    def LoadOne(self,ind,value):
		pass
        #print "PYTHON -> SIS3820Ctrl/",self.inst_name,": In LoadOne method for index",ind," with value",value
	
    def GetExtraAttributePar(self,ind,name):
        if name == "Offset":
			par_value = self.sis3820_ctrl.command_inout("GetAxeOffset",ind)
			return float(par_value)
            
    def SetExtraAttributePar(self,ind,name,value):
        if name == "Offset":
            self.sis3820_ctrl.command_inout("SetAxeOffset",ind)
			
    def SendToCtrl(self,in_data):
#        print "Received value =",in_data
        return "Adios"

    def __del__(self):
        print "PYTHON -> SIS3820Ctrl/",self.inst_name,": Aarrrrrg, I am dying"

 
if __name__ == "__main__":
    obj = SIS3820Ctrl('test')
