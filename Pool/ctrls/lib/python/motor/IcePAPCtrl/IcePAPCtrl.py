import PyTango
import socket
import errno
from pool import MotorController
from pyIcePAP import *
import time

class IcepapController(MotorController):
    "This class is the Tango Sardana motor controller for the ICEPAP with properties"

    #ctrl_features = ['Encoder','Home_speed','Home_acceleration']

    class_prop = {'Host':{'Type':'PyTango.DevString','Description':'The host name'},
                 'Port':{'Type':'PyTango.DevLong','Description':'The port number','DefaultValue':5000},
                  'Timeout':{'Type':'PyTango.DevLong','Description':'Connection timeout','DefaultValue':3}}

    ctrl_extra_attributes = {'Indexer':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             'Position_Register':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             'PowerOn':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                             'InfoA':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             'InfoB':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             'InfoC':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             'EnableEncoder_5V':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                             ## Fulvio requires this closed loop boolean attribute
                             'ClosedLoop':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                             ## Julio Lidon points out that this info is very useful:
                             ## ?POS : AXIS INDEXER POSERR SHFTENC TGTENC ENCIN INPOS ABSENC
                             ## ?ENC : AXIS INDEXER EXTERR SHFTENC TGTENC ENCIN INPOS ABSENC
                             'PosAxis':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'PosIndexer':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             #'PosPosErr':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             'PosShftEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'PosTgtEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'PosEncIn':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'PosInPos':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'PosAbsEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncAxis':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncIndexer':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             #'EncExtErr':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             'EncShftEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncTgtEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncEncIn':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncInPos':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncAbsEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             ## THIS IS A TEMPORARY TRICK UNTIL THE ICEPAP MANAGES ENCODER PULSES INPUT
                             'Pulses_per_unit':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'}
                             }

    
    gender = "Motor"
    model = "Icepap"
    organization = "Esrf Alba"
    image = "icepaphw.png"
    logo = "icepap.png"
    icon = "icepapicon.png"
    state = ""
    status = ""
    
    MaxDevice = 128
    
    def __init__(self,inst,props):
        
        MotorController.__init__(self,inst,props)
        
        
        self.iPAP = EthIcePAP(self.Host, self.Port, self.Timeout)
        self.attributes = {}
        self.moveMultipleValues = []

    def AddDevice(self,axis):
        #print "[IcepapController]",self.inst_name,": In AddDevice method for axis",axis
        self.attributes[axis] = {}
        self.attributes[axis]["pos_sel"] = ""
        self.attributes[axis]["step_per_unit"] = 1  
        ## THIS IS A TEMPORARY TRICK UNTIL THE ICEPAP MANAGES ENCODER PULSES INPUT
        self.attributes[axis]["pulses_per_unit"] = 1

        if self.iPAP.connected:
            addr = axis % 10
            cratenr = axis / 10
            cratespresent = self.iPAP.getSysStatus()
            cratespresent = int(cratespresent, 16)
            if ((cratespresent >> cratenr) & 1) == 1:
                driversalive = self.iPAP.getRackStatus(cratenr)[1]
                driversalive = int(driversalive, 16)
                if ((driversalive >> (addr-1)) & 1) == 1:
                    print "[IcepapController]",self.inst_name,": Axis %d added"%axis
                else:
                    print "[IcepapController]",self.inst_name,": Axis %d not alive"%axis
                    #PyTango.Except.throw_exception("IcepapController_AddDevice", "Error adding axis, axis not available", "AddDevice()")

        
    def DeleteDevice(self,axis):
        pass
        #print "[IcepapController]",self.inst_name,": In DeleteDevice method for axis",axis
    
    
    def StateOne(self,axis):
        #print "PYTHON -> IcePapController/",self.inst_name,": In StateOne method for axis",axis
        if self.iPAP.connected:
            try:
                state = PyTango.DevState.UNKNOWN
                register = self.iPAP.getStatus(axis)
                if "x" in register:
                    register = int(register,16)
                else:
                    register = int(register)
                statereg = IcepapStatus.isDisabled(register)
                if int(statereg) == 1:
                    state = PyTango.DevState.ALARM
                else:
                    power = self.iPAP.getPower(axis)
                    power = (power == IcepapAnswers.ON)
                    if power:
                        state = PyTango.DevState.ON
                    else:
                        state = PyTango.DevState.ALARM
                    moving = IcepapStatus.isMoving(register)
                    if int(moving) == 1:
                        state = PyTango.DevState.MOVING
                if self.iPAP.getMode(axis) == IcepapMode.CONFIG:
                    state = PyTango.DevState.ALARM

                lower = IcepapStatus.getLimitNegative(register) 
                upper = IcepapStatus.getLimitPositive(register) 
                switchstate = 0
                if int(lower) == 1 and int(upper) == 1:
                    switchstate = 6
                elif int(lower) == 1:
                    switchstate = 4
                elif int(upper) == 1:
                    switchstate = 2
                if switchstate != 0:
                    state = PyTango.DevState.ALARM
                return (int(state),switchstate)
            except Exception,e:
                print "[IcepapController]",self.inst_name,": ERROR in StateOne for axis",axis
                print "[IcepapController]",self.inst_name,":",e

        return (int(PyTango.DevState.ALARM),0)

    def PreReadAll(self):
        #print "PYTHON -> IcePapController/",self.inst_name,": In PreReadAll method"
        if not self.iPAP.connected:
            return False

    def PreReadOne(self,axis):
        #print "PYTHON -> IcePapController/",self.inst_name,": In PreReadOne method for axis",axis
        pass

    def ReadAll(self):
        #print "PYTHON -> IcePapController/",self.inst_name,": In ReadAll method"
        pass

    def ReadOne(self,axis):
        #print "PYTHON -> IcePapController/",self.inst_name,": In ReadOne method for axis",axis
        if self.iPAP.connected:
            try:
                pos_sel = self.attributes[axis]["pos_sel"]
                pos = float(self.iPAP.getPosition(axis, pos_sel))
                if pos_sel == "" or pos_sel == "AXIS":
                    return pos / self.attributes[axis]["step_per_unit"]
                else:
                    ## THIS IS A TEMPORARY TRICK UNTIL THE ICEPAP MANAGES ENCODER PULSES INPUT
                    return  pos / self.attributes[axis]["pulses_per_unit"]
            except Exception,e:
                print "[IcepapController]",self.inst_name,": ERROR in ReadOne for axis",axis
                print "[IcepapController]",self.inst_name,":",e
                raise

    def PreStartAll(self):
        #print "PYTHON -> IcePapController/",self.inst_name,": In PreStartAll method"
        if not self.iPAP.connected:
            return False

    def PreStartOne(self,axis,pos):
        #print "PYTHON -> IcePapController/",self.inst_name,": In PreStartOne method for axis",axis," with pos",pos
        if self.iPAP.connected:
            pos = int(pos * self.attributes[axis]["step_per_unit"])
            try:
                self.moveMultipleValues.append((axis,int(pos)))
                return True
            except Exception,e:
                print "[IcepapController]",self.inst_name,": ERROR in PreStartOne for axis",axis,"and pos",pos
                print "[IcepapController]",self.inst_name,":",e
                raise
        return False

    def StartOne(self,axis,pos):
        #print "PYTHON -> IcePapController/",self.inst_name,": In StartOne method for axis",axis," with pos",pos
        pass
            
    def StartAll(self):
        #print "PYTHON -> IcePapController/",self.inst_name,": In StartAll method"
        if self.iPAP.connected:
            try:
                self.iPAP.moveMultiple(self.moveMultipleValues)
                self.moveMultipleValues = []
            except Exception,e:
                print "[IcepapController]",self.inst_name,": ERROR in StartAll",self.moveMultipleValues
                print "[IcepapController]",self.inst_name,":",e
                raise

    def SetPar(self,axis,name,value):
        #print "[IcepapController]",self.inst_name,": In SetPar method for axis",axis," name=",name," value=",value
        if self.iPAP.connected:
            try:
                if name.lower() == "velocity":
                    self.iPAP.setSpeed(axis, value)
                elif name.lower() == "base_rate":
                    pass
                elif name.lower() == "acceleration" or name == "deceleration":
                    self.iPAP.setAcceleration(axis, value)        
                elif name.lower() == "backlash":
                    PyTango.Except.throw_exception("IcepapController_SetPar", "Error setting backlash, not implemented", "SetPar()")
                elif name.lower() == "step_per_unit":
                    self.attributes[axis]["step_per_unit"] = float(value)
            except Exception,e:
                print "[IcepapController]",self.inst_name,": ERROR in SetPar for axis",axis,"name",name,"value",value
                print "[IcepapController]",self.inst_name,":",e
                raise
        

    def GetPar(self,axis,name):
        #print "[IcepapController]",self.inst_name,": In GetPar method for axis",axis," name=",name
        if self.iPAP.connected:
            register = self.iPAP.getStatus(axis)
            if "x" in register:
                register = int(register,16)
            else:
                register = int(register)
            if IcepapStatus.isDisabled(register):
                return None

            try:
                if name.lower() == "velocity":
                    return float(self.iPAP.getSpeed(axis))
                elif name.lower() == "base_rate":
                    #return float(self.iPAP.getCfgParameter(axis, "DEFIVEL"))
                    return float(self.iPAP.getCfgParameter(axis, "STRTVEL"))
                elif name.lower() == "acceleration" or name.lower() == "deceleration":
                    return float(self.iPAP.getAcceleration(axis))
                elif name.lower() == "backlash":
                    PyTango.Except.throw_exception("IcepapController_GetPar", "Error getting backlash, not implemented", "GetPar()")
                elif name.lower() == "step_per_unit":
                    return float(self.attributes[axis]["step_per_unit"]) 
                return None
            except Exception,e:
                print "[IcepapController]",self.inst_name,": ERROR in GetPar for axis",axis,"name",name
                print "[IcepapController]",self.inst_name,":",e
                raise
        else:
            return -1

    def GetExtraAttributePar(self,axis,name):
        if self.iPAP.connected:
            name = name.lower()
            try:
                if name == "indexer":
                    return self.iPAP.getIndexerSource(axis)
                elif name == "position_register":
                    return self.attributes[axis]["pos_sel"]
                elif name == "enableencoder_5v":
                    ans = self.iPAP.getAuxPS(axis)
                    return ans == IcepapAnswers.ON
                elif name.startswith("info"):
                    name = name.upper()
                    result = self.iPAP.getInfoSource(axis, name)
                    return result
                elif name == "poweron":
                    ans = self.iPAP.getPower(axis)
                    return ans == IcepapAnswers.ON
                ## Fulvio requires this closed loop boolean attribute
                elif name == "closedloop":
                    ans = self.iPAP.getClosedLoop(axis)
                    if ans.count("OFF") > 0:
                        return False
                    return True
                ## Julio Lidon points out that this info is very useful:
                ## ?POS : AXIS INDEXER POSERR SHFTENC TGTENC ENCIN INPOS ABSENC
                ## ?ENC : AXIS INDEXER EXTERR SHFTENC TGTENC ENCIN INPOS ABSENC
                elif name == "posaxis":
                    ans = self.iPAP.getPosition(axis,"AXIS")
                    return float(ans)
                elif name == "posindexer":
                    ans = self.iPAP.getPosition(axis,"INDEXER")
                    return float(ans)
                ##elif name == "posposerr":
                ##    ans = self.iPAP.getPosition(axis,"POSERR")
                ##    return ans
                elif name == "posshftenc":
                    ans = self.iPAP.getPosition(axis,"SHFTENC")
                    return float(ans)
                elif name == "postgtenc":
                    ans = self.iPAP.getPosition(axis,"TGTENC")
                    return float(ans)
                elif name == "posencin":
                    ans = self.iPAP.getPosition(axis,"ENCIN")
                    return float(ans)
                elif name == "posinpos":
                    ans = self.iPAP.getPosition(axis,"INPOS")
                    return float(ans)
                elif name == "posabsenc":
                    ans = self.iPAP.getPosition(axis,"ABSENC")
                    return float(ans)
                elif name == "encaxis":
                    ans = self.iPAP.getEncoder(axis,"AXIS")
                    return float(ans)
                elif name == "encindexer":
                    ans = self.iPAP.getEncoder(axis,"INDEXER")
                    return float(ans)
                ##elif name == "encexterr":
                ##    ans = self.iPAP.getEncoder(axis,"EXTERR")
                ##    return ans
                elif name == "encshftenc":
                    ans = self.iPAP.getEncoder(axis,"SHFTENC")
                    return float(ans)
                elif name == "enctgtenc":
                    ans = self.iPAP.getEncoder(axis,"TGTENC")
                    return float(ans)
                elif name == "encencin":
                    ans = self.iPAP.getEncoder(axis,"ENCIN")
                    return float(ans)
                elif name == "encinpos":
                    ans = self.iPAP.getEncoder(axis,"INPOS")
                    return float(ans)
                elif name == "encabsenc":
                    ans = self.iPAP.getEncoder(axis,"ABSENC")
                    return float(ans)
                ## THIS IS A TEMPORARY TRICK UNTIL THE ICEPAP MANAGES ENCODER PULSES INPUT
                elif name == "pulses_per_unit":
                    return float(self.attributes[axis]["pulses_per_unit"])
                else:
                    PyTango.Except.throw_exception("IcepapController_GetExtraAttributePar()r", "Error getting " + name + ", not implemented", "GetExtraAttributePar()")
            except Exception,e:
                if name == "encshftenc" or name == "enctgtenc" or name == "posshftenc" or name == "postgtenc":
                    #SORRY, IN SOME CASES THIS VALUES ARE NOT ACCESSIBLE
                    return
                print "[IcepapController]",self.inst_name,": ERROR in GetExtraAttributePar for axis",axis,"name",name
                print "[IcepapController]",self.inst_name,":",e
                raise

    def SetExtraAttributePar(self,axis,name,value):
        #print "PYTHON -> IcePapController/",self.inst_name,": In SetExtraAttributePar method for axis",axis," name=",name," value=",value
        if self.iPAP.connected:
            name = name.lower()
            try:
                if name == "indexer":
                    if value in IcepapRegisters.IndexerRegisters:
                        self.iPAP.setIndexerSource(axis, value)
                    else:
                        PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar()", "Error setting " + name + ", wrong value", "SetExtraAttributePar()")
                elif name == "position_register":
                    if value in IcepapRegisters.PositionRegisters:
                        self.attributes[axis]["pos_sel"] = value
                    else:
                        PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar()", "Error setting " + name + ", wrong value", "SetExtraAttributePar()")                
                elif name == "enableencoder_5v":
                    if value:
                        self.iPAP.setAuxPS(axis, IcepapAnswers.ON)
                    else:
                        self.iPAP.setAuxPS(axis, IcepapAnswers.OFF)
                elif name == "poweron":
                    if value:
                        self.iPAP.setPower(axis, IcepapAnswers.ON)
                    else:
                        self.iPAP.setPower(axis, IcepapAnswers.OFF)
                ## Fulvio requires this closed loop boolean attribute
                elif name == "closedloop":
                    if value:
                        self.iPAP.setClosedLoop(axis,"TGTENC")
                    else:
                        self.iPAP.setClosedLoop(axis,"OFF")
                ## THIS IS A TEMPORARY TRICK UNTIL THE ICEPAP MANAGES ENCODER PULSES INPUT
                elif name == "pulses_per_unit":
                    self.attributes[axis]["pulses_per_unit"] = float(value)
                    
                elif name.startswith("info"):
                    name = name.upper()
                    value = value.split()
                    src = value[0].upper()
                    if not src in IcepapInfo.Sources:
                        PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar(r", "Error setting " + name + ", [Source = ("+str(IcepapInfo.Sources) + "), Polarity= ("+str(IcepapInfo.Polarity)+")]", "SetExtraAttributePar()")
                    polarity = "NORMAL"
                    if len(value) > 1:
                        polarity = value[1].upper()
                        if not polarity in IcepapInfo.Polarity:
                            PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar(r", "Error setting " + name + ", [Source = ("+str(IcepapInfo.Sources) + "), Polarity= ("+str(IcepapInfo.Polarity)+")]", "SetExtraAttributePar()")
                    
                    
                    self.iPAP.setInfoSource(axis, name, src, polarity)                            
                else:
                    PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar()r", "Error setting " + name + ", not implemented", "SetExtraAttributePar()")
            except Exception,e:
                print "[IcepapController]",self.inst_name,": ERROR in SetExtraAttributePar for axis",axis,"name",name,"value",value
                print "[IcepapController]",self.inst_name,":",e
                raise


    def AbortOne(self,axis):
        #print "IcePAP-->before abortone"
        if self.iPAP.connected:
            self.iPAP.abortMotor(axis)
            time.sleep(0.050)
            #print "IcePAP-->Abort"

    def StopOne(self,axis):
        if self.iPAP.connected:
            self.iPAP.stopMotor(axis)
            #print "IcePAP-->Stop"


    def DefinePosition(self, axis, position):
        #print "IcePAP-->Set Position %d in axis %d" % (axis, position)
        if self.iPAP.connected:
            position = int(position * self.attributes[axis]["step_per_unit"])
            self.iPAP.setPosition(axis, position, self.attributes[axis]["pos_sel"])

    def GOAbsolute(self, axis, finalpos):
        if self.iPAP.connected:
            ret = self.iPAP.move(axis, finalpos)

    def SendToCtrl(self,cmd):
        #print "IcePAP-->SendToCtrl with data '%s'" % cmd
        # determine if the command has an answer
        if self.iPAP.connected:
            cmd = cmd.upper()
            if cmd.find("?") >= 0 or cmd.find("#")>= 0:
                res = self.iPAP.sendWriteReadCommand(cmd)
            elif cmd.find("HELP")>=0:
                res = self.iPAP.sendWriteReadCommand(cmd)
            else:
                res = self.iPAP.sendWriteCommand(cmd)
            return res 

    def __del__(self):
        #print "[IcepapController]",self.inst_name,": Exiting"
        if self.iPAP.connected:
            self.iPAP.disconnect()
        
        
if __name__ == "__main__":
    obj = IcepapController('test')
#    obj.AddDevice(2)
#    obj.DeleteDevice(2)
