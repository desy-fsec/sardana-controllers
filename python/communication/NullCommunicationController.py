from pool import CommunicationController
import PyTango
import time

class NullCommunicationController(CommunicationController):
    """This class is the Tango Sardana NULL communication controller"""

    ctrl_extra_attributes = {'Py0D_extra_1':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
			     'Py0D_extra_2':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ'},
			     'Py0D_extra_3':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'}}
			     
#    class_prop = {'CtrlDevName':{'Type':'PyTango.DevString','Description':'The ctrl simulator Tango device name'}}
			     
    MaxDevice = 10
    
    def __init__(self,inst,props):
        CommunicationController.CommunicationController.__init__(self,inst,props)
        print "PYTHON -> NullCommunicationController ctor for instance",inst
        
        self.dft_PyCT_extra_1 = 88.99
        self.dft_PyCT_extra_2 = 33
        self.dft_PyCT_extra_3 = True

        self.PyCT_extra_1 = []
        self.PyCT_extra_2 = []
        self.PyCT_extra_3 = []
       
    def OpenOne(self,ind):
        pass
    
    def CloseOne(self,ind):
        pass
        
    def AddDevice(self,ind):
        print "PYTHON -> NullCommunicationController/",self.inst_name,": In AddDevice method for index",ind
#        raise RuntimeError,"Hola la la"
        self.PyCT_extra_1.append(self.dft_PyCT_extra_1)
        self.PyCT_extra_2.append(self.dft_PyCT_extra_2)
        self.PyCT_extra_3.append(self.dft_PyCT_extra_3)        
        
    def DeleteDevice(self,ind):
        print "PYTHON -> NullCommunicationController/",self.inst_name,": In DeleteDevice method for index",ind
        
    def StateOne(self,ind):
        print "PYTHON -> NullCommunicationController/",self.inst_name,": In StateOne method for index",ind
        return (PyTango.DevState.ON, "I am Ok!")

    def ReadOne(self,ind,max_read_len):
        print "PYTHON -> NullCommunicationController/",self.inst_name,": In ReadOne method for index",ind
        return "tonteria"

    def WriteOne(self,ind,buf,write_len):
        print "PYTHON -> NullCommunicationController/",self.inst_name,": In WriteOne method for index",ind
        print "          with data = ",buf, " write_len = ", write_len
        return write_len

    def WriteReadOne(self,ind,buff,write_len,max_read_len):
        print "PYTHON -> NullCommunicationController/",self.inst_name,": In WriteReadOne method for index",ind
        print "          with data = ",buf, " write_len = ", write_len, " max_read_len = ", max_read_len
        return "tonteria"
	
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
        print "Received value =",in_data
        return "Adios"

    def __del__(self):
        print "PYTHON -> NullCommunicationController/",self.inst_name,": Aarrrrrg, I am dying"

        
if __name__ == "__main__":
    obj = NullCommunicationController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
