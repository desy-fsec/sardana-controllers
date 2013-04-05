import PyTango, taurus

from sardana import pool, State
from sardana.pool.controller import IORegisterController

class XiaIORController(IORegisterController):

    ctrl_properties = {'Device' : {'Type' : 'PyTango.DevString', 'Description' : 'Name tango device'}}

    axis_attributes = { "time"    : { "Type" : float, "R/W Type": "READ_WRITE" },
                        "enabled" : { "Type" : bool, "R/W Type": "READ_WRITE" }}

    MaxDevice = 4

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        if len(self.Device.split('/')) != 3:
            raise Exception('Device property is not properly set.')
        self.device = taurus.Device(self.Device)
        
    def AddDevice(self, axis):
        pass
        
    def DeleteDevice(self, axis):
        pass

    def StateOne(self, axis):
        self._log.debug("StateOne() entering... ")
        if axis == 1:
            dev_response = self.device.read_attribute("PF2S2_Shutter_Status").value
            if dev_response.count("Disabled") == 1:
                sta = State.Unknown
                status = "Shutter mode is disabled. Write %s/PF2S2_Shutter_Status attribute to True (1) to enable it." % self.Device
                return (sta,status)
        sta = self.device.State()
        status = self.device.Status()
        return (sta,status)

    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        self._log.debug("ReadOne() entering...")
        if axis == 1:
            dev_response = self.device.read_attribute("PF2S2_Shutter_Status").value
            if dev_response.count("Open") >= 1: 
                value = 1
            elif dev_response.count("Closed") >= 1:
                value = 0
            else:
                self._log.debug("!!!!!!!!!!!!!!!!!!!!!!dev_response: %s" % dev_response)
                self.state = State.Alarm
                self.status = "It was not possible to interpret shutter position returned by Xia device server. Going into ALARM state..."
                raise Exception(self.status)
        else:
            devAxisVal = self.device.read_attribute("Filter_Positions").value.split(" ")[3][(axis-2)]
            value = int(devAxisVal)
        return value
        
    def WriteOne(self, axis, value):        
      self._log.debug("WriteOne() entering...")
      if axis == 1:
          if value == 0:
              self.device.write_attribute("Close_Shutter", str(axis))
          if value == 1:
              self.device.write_attribute("Open_Shutter", str(axis))
          elif value == 2:
              self.device.write_attribute("Start_Exposure", axis)
      else:
          if value == 1:
              self.device.write_attribute("Insert_Filter", str(axis-1))
          elif value == 0:
              self.device.write_attribute("Remove_Filter", str(axis-1))

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("SetAxisExtraPar() entering...")
        name = name.lower()
        if name == "time":
            if axis != 1:
                raise Exception("time attribute is not allowed for axis %d." % axis)
            else:
                dev_response = self.device.read_attribute("Exposure_TimeUnit").value
                value = dev_response/100
        elif name == "enabled":
            if axis != 1:
                raise Exception("enabled attribute is not allowed for axis %d." % axis)
            else:
                dev_response = self.device.read_attribute("PF2S2_Shutter_Status").value
                if dev_response.find("Disabled") == -1:
                    value = True
                else:
                    value = False
        return value


    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar() entering...")
        if name == "time":
            if axis != 1:
                raise Exception("time attribute is not allowed for axis %d." % axis)
            else:
                value = int(value * 100)
                self.device.write_attribute("Exposure_TimeUnit", value)
        elif name == "enabled":
            if axis != 1:
                raise Exception("enabled attribute is not allowed for axis %d." % axis)
            else:
                value = str(value)
                self.device.write_attribute("PF2S2_Shutter_Status",value)
