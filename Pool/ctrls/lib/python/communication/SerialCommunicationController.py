import PyTango
from pool import CommunicationController
import time
import pool
import array

class SerialComCtrl(CommunicationController):
    """A generic Sardana serial line communication controller"""

    gender = "Serial Line"
    model  = "Generic RS232"
    organization = "CELLS - ALBA"
    image = "dummy_com.png"
    logo = "ALBA_logo.png"
        
    ctrl_extra_attributes = {
       'BaudRate'   : {'Type':'PyTango.DevLong',   'R/W Type':'PyTango.READ_WRITE'},
       'DataBits'   : {'Type':'PyTango.DevLong',   'R/W Type':'PyTango.READ_WRITE'},
       'FlowControl': {'Type':'PyTango.DevString', 'R/W Type':'PyTango.READ_WRITE'},
       'InputBuffer': {'Type':'PyTango.DevLong',   'R/W Type':'PyTango.READ'},
       'Parity'     : {'Type':'PyTango.DevString', 'R/W Type':'PyTango.READ_WRITE'},
       'Port'       : {'Type':'PyTango.DevString', 'R/W Type':'PyTango.READ_WRITE'},
       'StopBits'   : {'Type':'PyTango.DevLong',   'R/W Type':'PyTango.READ_WRITE'},
       'Terminator' : {'Type':'PyTango.DevString', 'R/W Type':'PyTango.READ_WRITE'},
       'Timeout'    : {'Type':'PyTango.DevDouble', 'R/W Type':'PyTango.READ_WRITE'}}
    
    def __init__(self,inst,props):
        CommunicationController.__init__(self,inst,props)
        self.serial_data = []


class RemoteSerialData:
    def __init__(self):
        self.device_name = ""
        self.proxy = None
        self.available = False


class SerialRemoteTangoComCtrl(SerialComCtrl):
    """A Sardana serial line communication controller for a remote serial line through a 
       generic Tango serial line device server"""

    model = "Serial"

    ctrl_extra_attributes = dict(SerialComCtrl.ctrl_extra_attributes)
    ctrl_extra_attributes['Device'] = {'Type':'PyTango.DevString', 'R/W Type':'PyTango.READ'}
                 
    class_prop = {'TangoDevices':{'Type':'PyTango.DevVarStringArray','Description':'Serial device names'}}

    def __init__(self,inst,props):
        SerialComCtrl.__init__(self,inst,props)
        self.serial_data = len(self.TangoDevices)*[None,]

    def is_serial_available(self,ind):
        sd = self.serial_data[ind-1]
        if sd.available == False:
            if sd.proxy != None:
                try:
                    sd.proxy.ping()
                    sd.available = True
                except Exception:
                    pass
        return sd.available
    
    def get_serial_device_data(self,ind):
        available = self.is_serial_available(ind)
            
        if available == False:
            raise Exception("Tango device server %s is not available" % self.serial_data[ind-1].device_name)
        
        return self.serial_data[ind-1]

    def AddDevice(self,ind):
        if ind > len(self.TangoDevices):
            raise Exception("No Tango device defined for index %d in 'TangoDevices' property for this controller" % ind)
        
        sd = RemoteSerialData()
        sd.device_name = self.TangoDevices[ind-1]

        sd.proxy = PyTango.DeviceProxy(sd.device_name)

        if sd.proxy != None:
            try:
                sd.proxy.ping()
                sd.available = True
            except Exception:
                print "Warning: Tango device server ", sd.device_name, " is not available"

        self.serial_data[ind-1] = sd
        
    def DeleteDevice(self,ind):
        self.serial_data[ind-1] = None
        
    def StateOne(self,ind):
        sd = self.get_serial_device_data(ind)
        
        state = sd.proxy.state()
        
        if state == PyTango.DevState.ON:
            return (PyTango.DevState.ON, "The serial line is ready")
        elif state == PyTango.DevState.OFF:
            return (PyTango.DevState.ON, "The serial line is closed")
        elif state == PyTango.DevState.FAULT or state == PyTango.DevState.UNKNOWN:
            return (state, sd.proxy.status())
        else:
            return (PyTango.DevState.UNKNOWN, sd.proxy.status())
        
        
class SerialRemotePyTangoComCtrl(SerialRemoteTangoComCtrl):
    """A Sardana serial line communication controller for a remote serial line through a 
       PySerial Tango serial line device server"""

    model = "PySerial"
    image = "dummy_com.png"
    logo = "ALBA_logo.png"

    MaxDevice = 64
    
    TERMINATOR = ["LF/CR", "CR/LF", "CR", "LF", "NONE"]

    def __init__(self,inst,props):
        SerialRemoteTangoComCtrl.__init__(self,inst,props)
        
    def OpenOne(self,ind):
        sd = self.get_serial_device_data(ind)
        if sd.proxy.state() == PyTango.DevState.OFF:
            sd.proxy.open()
    
    def CloseOne(self,ind):
        sd = self.get_serial_device_data(ind)
        if sd.proxy.state() != PyTango.DevState.OFF:
            sd.proxy.close()
    
    def ReadOne(self,ind,max_read_len):
        sd = self.get_serial_device_data(ind)
        
        if sd.proxy.state() != PyTango.DevState.ON:
            return ""
        
        if max_read_len == -1:
            max_read_len = sd.proxy.read_attribute("InputBuffer").value
        
        if max_read_len > 0:
            charArray = sd.proxy.read(max_read_len)
        else:
            charArray = sd.proxy.readline(max_read_len)

        return array.array('B', charArray).tostring()

    def ReadLineOne(self,ind):
        sd = self.get_serial_device_data(ind)
        
        if sd.proxy.state() != PyTango.DevState.ON:
            return ""
        
        charArray = sd.proxy.ReadLine()
        return array.array('B', charArray).tostring()

    def WriteOne(self,ind,buf,write_len):
        sd = self.get_serial_device_data(ind)

        if sd.proxy.state() != PyTango.DevState.ON:
            return 0

        sd.proxy.FlushInput()
        sd.proxy.FlushOutput()
        
        byteArray = array.array('B')
        byteArray.fromstring(buf)
        charArray = byteArray.tolist()
        sd.proxy.write(charArray)
        return write_len

    def WriteReadOne(self,ind,buf,write_len,max_read_len):
        sd = self.get_serial_device_data(ind)
        if sd.proxy.state() != PyTango.DevState.ON:
            return ""
        self.WriteOne(ind, buf, write_len)
        res = self.ReadOne(ind, max_read_len)
        return res
        
    def GetExtraAttributePar(self,ind,name):
        sd = self.get_serial_device_data(ind)
        
        if name == "Device":
            return sd.device_name 
        elif name == "BaudRate":
            return sd.proxy.read_attribute("BaudRate").value 
        elif name == "DataBits":
            return sd.proxy.read_attribute("DataBits").value
        elif name == "FlowControl":
            return sd.proxy.read_attribute("FlowControl").value
        elif name == "InputBuffer":
            return sd.proxy.read_attribute("InputBuffer").value
        elif name == "Parity":
            return sd.proxy.read_attribute("Parity").value
        elif name == "Port":
            return sd.proxy.read_attribute("Port").value
        elif name == "StopBits":
            return sd.proxy.read_attribute("StopBits").value
        elif name == "Terminator":
            return sd.proxy.read_attribute("Terminator").value
        else:
            return float(sd.proxy.read_attribute("Timeout").value)

    def SetExtraAttributePar(self,ind,name,value):
        sd = self.get_serial_device_data(ind)
        
        if sd.proxy.state() == PyTango.DevState.ON:
            sd.proxy.close()

        if name == "BaudRate":
            sd.proxy.write_attribute("BaudRate",value) 
        elif name == "DataBits":
            sd.proxy.write_attribute("DataBits",value)
        elif name == "FlowControl":
            sd.proxy.write_attribute("FlowControl",value)
        elif name == "Parity":
            sd.proxy.write_attribute("Parity",value)
        elif name == "Port":
            sd.proxy.write_attribute("Port",value)
        elif name == "StopBits":
            sd.proxy.write_attribute("StopBits",value)
        elif name == "Terminator":
            sd.proxy.write_attribute("Terminator",value)
        else:
            sd.proxy.write_attribute("Timeout",value)
        sd.proxy.open()
        
    def SendToCtrl(self,in_data):
        return "Adios"


class SerialRemoteCPPTangoComCtrl(SerialRemoteTangoComCtrl):
    """A Sardana serial line communication controller for a remote serial line through a 
       C++ Tango serial line device server"""
                 
    MaxDevice = 64
    
    def __init__(self,inst,props):
        SerialRemoteTangoComCtrl.__init__(self,inst,props)

    def OpenOne(self,ind):
        #TODO
        pass
    
    def CloseOne(self,ind):
        #TODO
        pass

    def ReadOne(self,ind,max_read_len):
        #TODO
        pass

    def ReadLineOne(self,ind,max_read_len):
        #TODO
        pass
    
    def WriteOne(self,ind,buf,write_len):
        #TODO
        pass

    def WriteReadOne(self,ind,buff,write_len,max_read_len):
        #TODO
        pass

    def GetExtraAttributePar(self,ind,name):
        #TODO
        pass

    def SetExtraAttributePar(self,ind,name,value):
        #TODO
        pass

    def SendToCtrl(self,in_data):
        #TODO
        pass
        
if __name__ == "__main__":
    obj = SerialRemotePyTangoComCtrl('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
