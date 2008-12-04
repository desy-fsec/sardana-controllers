import PyTango
from pool import CounterTimerController
import time
import datetime
import sys

class SimuCoTiController(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for the SimuCoTiCtrl tango device"

    ctrl_extra_attributes = {'PyCT_extra_1':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                 'PyCT_extra_2':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ'},
                 'PyCT_extra_3':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'}}
                 
    class_prop = {'DevName':{'Type':'PyTango.DevString','Description':'The ctrl simulator Tango device name'}}
                 
    gender = "Simulation"
    model  = "Best"
    organization = "CELLS - ALBA"
    image = "motor_simulator.png"
    icon = "motor_simulator_icon.png"
    logo = "ALBA_logo.png"
                     
    MaxDevice = 1024

    def __init__(self,inst,props):
        CounterTimerController.__init__(self,inst,props)

        self.simu_ctrl = None
        self.simu_ctrl = PyTango.DeviceProxy(self.DevName)
        self.started = False

        self.dft_PyCT_extra_1 = 88.99
        self.dft_PyCT_extra_2 = 33
        self.dft_PyCT_extra_3 = True

        self.PyCT_extra_1 = []
        self.PyCT_extra_2 = []
        self.PyCT_extra_3 = []

        try:
            self.simu_ctrl.ping()
        except:
            self.simu_ctrl = None
            raise

    def AddDevice(self, ind):
        self.PyCT_extra_1.append(self.dft_PyCT_extra_1)
        self.PyCT_extra_2.append(self.dft_PyCT_extra_2)
        self.PyCT_extra_3.append(self.dft_PyCT_extra_3)
        
    def DeleteDevice(self,ind):
        pass
        
    def StateOne(self,ind):
        if self.simu_ctrl != None:
            if self.started == True:
                now = time.time()
                delta_t = now - self.start_time
                if delta_t > 4.0:
                    for index in self.wantedCT:
                        self.simu_ctrl.command_inout("Stop",index)
                    self.started = False
            sta = self.simu_ctrl.command_inout("GetCounterState",ind)
            #print "State in controller =",sta
            tup = (sta,"OK")
        else:
            raise RuntimeError,"Ctrl Tango's proxy null!!!"
        return tup

    def PreReadAll(self):
        pass
        
    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self,ind):
        if self.simu_ctrl != None:
            return self.simu_ctrl.command_inout("GetCounterValue",ind)
        else:
            raise RuntimeError("Ctrl Tango's proxy null!!!")
    
    def AbortOne(self,ind):
        if self.simu_ctrl != None:
            self.simu_ctrl.command_inout("Stop",ind)
            self.started = False
        else:
            raise RuntimeError("Ctrl Tango's proxy null!!!")
        
    def PreStartAllCT(self):
        self.wantedCT = []
    
    def StartOneCT(self,ind):
        self.wantedCT.append(ind)
    
    def StartAllCT(self):
        for index in self.wantedCT:
            self.simu_ctrl.command_inout("Start",index)
        self.started = True
        self.start_time = time.time()
                 
    def LoadOne(self,ind,value):
        if self.simu_ctrl != None:
            self.simu_ctrl.command_inout("Clear",ind)
        else:
            raise RuntimeError("Ctrl Tango's proxy null!!!")
    
    def GetExtraAttributePar(self,ind,name):
        if name == "PyCT_extra_1":
            return self.PyCT_extra_1[ind]
        if name == "PyCT_extra_2":
            return self.PyCT_extra_2[ind]
        return self.PyCT_extra_3[ind]

    def SetExtraAttributePar(self,ind,name,value):
        if name == "PyCT_extra_1":
            self.PyCT_extra_1[ind] = value
        elif name == "PyCT_extra_2":
            self.PyCT_extra_2[ind] = value
        else:
            self.PyCT_extra_3[ind] = value
        
    def SendToCtrl(self,in_data):
        return "Adios"


        
if __name__ == "__main__":
    obj = SimuCoTiController('test',{'DevName' : 'tcoutinho/simulator/motctrl1'})

