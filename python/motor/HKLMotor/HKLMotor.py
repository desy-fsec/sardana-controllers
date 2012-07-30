import pool
import PyTango
from pool import MotorController

class HKLMotorController(MotorController):
    """This class is the Tango Sardana motor controller for the HKL axis of the diffractometer device.
    """

    #ctrl_features = ['Encoder','Home_speed','Home_acceleration']

    ## The properties used to connect to the diffraco motor controller
    class_prop = {'DiffracDevName':{'Type':'PyTango.DevString','Description':'The diffractometer device name'}}
    
    gender = "Motor"
    model = "HKLMotor"
    organization = "DESY"
    image = "motor_simulator.png"
    logo = "ALBA_logo.png"
    icon = "motor_simulation_icon.png"
    state = ""
    status = ""
    
    MaxDevice = 3
    
    def __init__(self,inst,props):
        """ Do the default init plus the connection to the
        diffractometer device. And the readout of the properties
        need 
        @param inst instance name of the controller
        @param properties of the controller
        """
        MotorController.__init__(self,inst,props)
        
        self.diffrac = PyTango.DeviceProxy(self.DiffracDevName)

        self.hkl_device = []
        
        h_dev_name = self.DiffracDevName + "-h"       
        self.hkl_device.append(PyTango.DeviceProxy(h_dev_name))
        
        k_dev_name =  self.DiffracDevName + "-k"       
        self.hkl_device.append(PyTango.DeviceProxy(k_dev_name))
        
        l_dev_name =  self.DiffracDevName + "-l"     
        self.hkl_device.append(PyTango.DeviceProxy(l_dev_name))
        
        hkl_simu_dev_name =  self.DiffracDevName + "-sim-hkl"       
        self.hkl_simu_device = PyTango.DeviceProxy(hkl_simu_dev_name)
        
        prop = self.diffrac.get_property(['DiffractometerType'])        
        for v in prop['DiffractometerType']:       
            self.type = v
    
        prop = self.diffrac.get_property(['RealAxisProxies'])        
        self.angle_device_name = {}         
        self.angle_names = []      
        for v in prop['RealAxisProxies']:       
            name_list = v.split(":")       
            self.angle_names.append(name_list[0])      
            self.angle_device_name[name_list[0]] = name_list[1]

    def AddDevice(self,axis):
        """ Nothing special to do
        @param axis to be added
        """
        pass
        #print "[HKLMotorcController]",self.inst_name,": In AddDevice method for axis",axis

        
    def DeleteDevice(self,axis):
        """ Nothing special to do. """
        pass
        #print "[HKLMotorController]",self.inst_name,": In DeleteDevice method for axis",axis
    
    
    def StateOne(self,axis):
        """ Return the state from the h, k or l device.
        @param axis to read the state
        @return the state value: {ALARM|ON|MOVING}
        """
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In StateOne method for axis",axis
        sta = self.hkl_device[axis-1].command_inout("State")
        tup = (sta,0)
        return tup

    def PreReadAll(self):
        """ Nothing special to do"""
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In PreReadAll method"
        pass

    def PreReadOne(self,axis):
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In PreReadOne method for axis",axis
        pass

    def ReadAll(self):
        """ We connect to the Icepap system for each axis. """
        #print "PYTHON -> IcePapController/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,axis):
        """ Return the position of the h, k or l device.
        @param axis to read the position
        @return the current axis position
        """
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In ReadOne method for axis",axis

        return self.hkl_device[axis-1].position

    def PreStartAll(self):
        """ Nothing special to do"""
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In PreStartAll method"
        pass

    def PreStartOne(self,axis,pos):
        """ Nothing special to do.
        @param axis to start
        @param pos to move to
        """
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In PreStartOne method for axis",axis," with pos",pos
        return True

    def StartOne(self,axis,pos):
        """ Move the axis separtely, for multiple movements use the macro br """
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In StartOne method for axis",axis," with pos",pos
        
        if axis == 1:
            self.hkl_simu_device.write_attribute("h",pos)
            pos1 = self.hkl_device[1].position
            self.hkl_simu_device.write_attribute("k",pos1)
            pos1 = self.hkl_device[2].position
            self.hkl_simu_device.write_attribute("l",pos1)
        elif axis == 2:
            pos1 = self.hkl_device[0].position
            self.hkl_simu_device.write_attribute("h",pos1)
            self.hkl_simu_device.write_attribute("k",pos)
            pos1 = self.hkl_device[2].position
            self.hkl_simu_device.write_attribute("l",pos1)
        elif axis == 3:
            pos1 = self.hkl_device[0].position
            self.hkl_simu_device.write_attribute("h",pos1)
            pos1 = self.hkl_device[1].position
            self.hkl_simu_device.write_attribute("k",pos1)
            self.hkl_simu_device.write_attribute("l",pos)
            
        self.diffrac.write_attribute("Simulated",1)

        
        angles_to_set = {}
    
        if self.type == 'E6C':    
            mu = self.diffrac.axisMu
            omega = self.diffrac.axisOmega
            chi = self.diffrac.axisChi
            phi = self.diffrac.axisPhi
            gamma = self.diffrac.axisGamma
            delta = self.diffrac.axisDelta
        
            angles_to_set["mu"] = mu
            angles_to_set["omega"] = omega
            angles_to_set["chi"] = chi
            angles_to_set["phi"] = phi
            angles_to_set["gamma"] = gamma
            angles_to_set["delta"] = delta        
        elif self.type == 'E4CV':
            omega = self.diffrac.axisOmega
            chi = self.diffrac.axisChi
            phi = self.diffrac.axisPhi
            tth = self.diffrac.axisTth
            
            angles_to_set["omega"] = omega
            angles_to_set["chi"] = chi
            angles_to_set["phi"] = phi
            angles_to_set["tth"] = tth
            
        for angle in self.angle_names:
            angle_dev = PyTango.DeviceProxy(self.angle_device_name[angle])
            angle_dev.write_attribute("Position",angles_to_set[angle])
            
        self.diffrac.write_attribute("Simulated",0)
        
        
    def StartAll(self):
        """ Nothis special to do """
        #print "PYTHON -> IcePapController/",self.inst_name,": In StartAll method"
        pass

    def SetPar(self,axis,name,value):
        """ Set the standard pool motor parameters. Not sense in this controller
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        #print "[HKLMotorController]",self.inst_name,": In SetPar method for axis",axis," name=",name," value=",value
        pass
        

    def GetPar(self,axis,name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        #print "[HKLMotorController]",self.inst_name,": In GetPar method for axis",axis," name=",name
        pass

    def GetExtraAttributePar(self,axis,name):
        """ Get HKLMotor driver particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        pass
    
    def SetExtraAttributePar(self,axis,name,value):
        """ Set HKLMotor driver particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        #print "PYTHON -> HKLMotorController/",self.inst_name,": In SetExtraAttributePar method for axis",axis," name=",name," value=",value
        pass

    def AbortOne(self,axis):
        pass

    def StopOne(self,axis):
        pass


    def DefinePosition(self, axis, position):
        pass

    def GOAbsolute(self, axis, finalpos):
        pass

    def SendToCtrl(self,cmd):
        pass

    def __del__(self):
        #print "[HKLMotorController]",self.inst_name,": Exiting"
        pass
        
        
if __name__ == "__main__":
    obj = HKLMotorController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
