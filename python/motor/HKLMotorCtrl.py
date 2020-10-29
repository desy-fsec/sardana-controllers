# from sardana import pool
import PyTango
from sardana.pool.controller import MotorController, Description, Type


class HKLMotorCtrl(MotorController):
    """This class is the Tango Sardana motor controller
    for the HKL axis of the diffractometer device.
    """

    # The property used to connect to the diffractometer controller
    ctrl_properties = {
        'DiffracDevName': {
            Type: 'PyTango.DevString',
            Description: 'The diffractometer device name'}
    }

    gender = "Motor"
    model = "HKLMotor"
    organization = "DESY"
    image = "motor_simulator.png"
    logo = "ALBA_logo.png"
    icon = "motor_simulation_icon.png"
    state = ""
    status = ""

    MaxDevice = 3

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the connection to the
        diffractometer device. And the readout of the properties
        need
        @param inst instance name of the controller
        @param properties of the controller
        """
        MotorController.__init__(self, inst, props, *args, **kwargs)

        self.diffrac = PyTango.DeviceProxy(self.DiffracDevName)

        self.hkl_device = []

        h_dev_name = self.DiffracDevName + "-h"
        self.hkl_device.append(PyTango.DeviceProxy(h_dev_name))

        k_dev_name = self.DiffracDevName + "-k"
        self.hkl_device.append(PyTango.DeviceProxy(k_dev_name))

        l_dev_name = self.DiffracDevName + "-l"
        self.hkl_device.append(PyTango.DeviceProxy(l_dev_name))

        hkl_simu_dev_name = self.DiffracDevName + "-sim-hkl"
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

    def StateOne(self, axis):
        """ Return the state from the h, k or l device.
        @param axis to read the state
        @return the state value: {ALARM|ON|MOVING}
        """
        sta = self.hkl_device[axis-1].command_inout("State")
        tup = (sta, 0)
        return tup

    def PreReadAll(self):
        """ Nothing special to do"""
        pass

    def PreReadOne(self, axis):
        pass

    def ReadAll(self):
        """ We connect to the Icepap system for each axis. """
        pass

    def ReadOne(self, axis):
        """ Return the position of the h, k or l device.
        @param axis to read the position
        @return the current axis position
        """

        return self.hkl_device[axis-1].position

    def PreStartAll(self):
        """ Nothing special to do"""
        pass

    def PreStartOne(self, axis, pos):
        """ Nothing special to do.
        @param axis to start
        @param pos to move to
        """
        return True

    def StartOne(self, axis, pos):
        """ Move the axis separtely,
        for multiple movements use the macro br """

        if axis == 1:
            self.hkl_simu_device.write_attribute("h", pos)
            pos1 = self.hkl_device[1].position
            self.hkl_simu_device.write_attribute("k", pos1)
            pos1 = self.hkl_device[2].position
            self.hkl_simu_device.write_attribute("l", pos1)
        elif axis == 2:
            pos1 = self.hkl_device[0].position
            self.hkl_simu_device.write_attribute("h", pos1)
            self.hkl_simu_device.write_attribute("k", pos)
            pos1 = self.hkl_device[2].position
            self.hkl_simu_device.write_attribute("l", pos1)
        elif axis == 3:
            pos1 = self.hkl_device[0].position
            self.hkl_simu_device.write_attribute("h", pos1)
            pos1 = self.hkl_device[1].position
            self.hkl_simu_device.write_attribute("k", pos1)
            self.hkl_simu_device.write_attribute("l", pos)

        self.diffrac.write_attribute("Simulated", 1)

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
            angle_dev.write_attribute("Position", angles_to_set[angle])

        self.diffrac.write_attribute("Simulated", 0)

    def StartAll(self):
        """ Nothis special to do """
        pass

    def GetAxisExtraPar(self, axis, name):
        """ Get HKLMotor driver particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        pass

    def SetAxisExtraPar(self, axis, name, value):
        """ Set HKLMotor driver particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        pass

    def AbortOne(self, axis):
        pass

    def StopOne(self, axis):
        pass

    def DefinePosition(self, axis, position):
        pass

    def GOAbsolute(self, axis, finalpos):
        pass

    def SendToCtrl(self, cmd):
        pass

    def __del__(self):
        # print "[HKLMotorCtrl]", self.inst_name,": Exiting"
        pass


if __name__ == "__main__":
    obj = HKLMotorCtrl('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
