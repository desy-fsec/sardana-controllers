import PyTango
import socket
import errno
from pool import MotorController
from pyIcePAP import *
import time

class IcepapController(MotorController):
    """This class is the Sardana motor controller for the ICEPAP motor controller.
    Appart from the standard Pool motor interface per axis, it provides extra attributes for some
    firmware attributes of the driver.
    """

    #ctrl_features = ['Encoder','Home_speed','Home_acceleration']

    ## The properties used to connect to the ICEPAP motor controller
    class_prop = {'Host':{'Type':'PyTango.DevString','Description':'The host name'},
                  'Port':{'Type':'PyTango.DevLong','Description':'The port number','DefaultValue':5000},
                  'Timeout':{'Type':'PyTango.DevLong','Description':'Connection timeout','DefaultValue':3}}

    ## The axis extra attributes that correspond to extra features from the Icepap drivers
    ctrl_extra_attributes = {'Indexer':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             # THIS POSITION REGISTER CAN HAVE VALUES DEFINED IN pyIcePAP.icepapdef.py
                             # WHICH ARE: [AXIS, INDEXER, EXTERR, SHFTENC, TGTENC, ENCIN, INPOS, ABSENC]
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
                             'Pulses_per_unit':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
                             ## 12/08/2009 REQUESTED FROM LOTHAR, A COMPLETE MESSAGE ABOUT WHAT IS HAPPENING
                             'StatusDriverBoard':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             ## 12/08/2009 GOOD TO KNOW WHAT IS REALLY HAPPENING TO THE AXIS POWER STATE
                             'PowerInfo':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'}
                             }

    
    gender = "Motor"
    model = "Icepap"
    organization = "ALBA"
    image = "icepaphw.png"
    logo = "icepap.png"
    icon = "icepapicon.png"
    state = ""
    status = ""
    
    MaxDevice = 128
    
    def __init__(self,inst,props):
        """ Do the default init plus the icepap connection
        @param inst instance name of the controller
        @param properties of the controller
        """
        MotorController.__init__(self,inst,props)
        
        self.iPAP = EthIcePAP(self.Host, self.Port, self.Timeout)
        self.attributes = {}
        self.moveMultipleValues = []

    def AddDevice(self,axis):
        """ Set default values for the axis and try to connect to it
        @param axis to be added
        """
        self.attributes[axis] = {}
        self.attributes[axis]["pos_sel"] = ""
        self.attributes[axis]["step_per_unit"] = 1  
        ## THIS IS A TEMPORARY TRICK UNTIL THE ICEPAP MANAGES ENCODER PULSES INPUT
        self.attributes[axis]["pulses_per_unit"] = 1
        self.attributes[axis]["statusdriverboard"] = "Not updated yet"
        self.attributes[axis]["powerinfo"] = "Not updated yet"


        # THIS CODE WILL BE REPLACED WHEN THE pyIcePAP library provide a better way to check if one axis is alive
        if self.iPAP.connected:
            drivers_alive = self.iPAP.getDriversAlive()
            if axis in drivers_alive:
                self._log.info('Added axis %d.' % axis)
            else:
                self._log.warning('Added axis %d BUT NOT ALIVE.' % axis)
        else:
            self._log.debug('AddDevice(%d). No connection to %s.' % (axis,self.Host))

        
    def DeleteDevice(self,axis):
        """ Nothing special to do. """
        pass
    
    
    def StateOne(self,axis):
        """ Connect to the hardware and check the state. If no connection available, return ALARM.
        @param axis to read the state
        @return the state value: {ALARM|ON|MOVING}
        """
        driver_status = '\nIcepap is not connected'
        power_info = '\nIcepap is not connected'
        if self.iPAP.connected:
            power_info = self.iPAP.isg_powerinfo(axis)
            driver_status = ''
            try:
                state = PyTango.DevState.UNKNOWN
                register = self._getStatusRegister(axis)
                if not isinstance(register,int):
                    self._log.warning('StateOne(%d): Invalid register: (%s)' % (axis,str(register)))
                    driver_status += '\nDriver board %d NOT OPERATIVE\nRegister: %s' % (axis,register)
                    register = 0
                statereg = IcepapStatus.isDisabled(register)
                if int(statereg) == 1:
                    driver_status += '\nDriver is disabled'
                    state = PyTango.DevState.ALARM
                else:
                    driver_status += '\nDriver is enabled'
                    power = self.iPAP.getPower(axis)
                    power = (power == IcepapAnswers.ON)
                    if power:
                        driver_status += '\nPower is ON'
                        state = PyTango.DevState.ON
                    else:
                        driver_status += '\nPower is OFF'
                        state = PyTango.DevState.ALARM
                    moving = IcepapStatus.isMoving(register)
                    if int(moving) == 1:
                        driver_status += '\nDriver is moving'
                        state = PyTango.DevState.MOVING
                if self.iPAP.getMode(axis) == IcepapMode.CONFIG:
                    driver_status += '\nDriver is in CONFIG mode'
                    state = PyTango.DevState.ALARM

                lower = IcepapStatus.getLimitNegative(register)
                upper = IcepapStatus.getLimitPositive(register)
                driver_status += '\nLower switch: %s Upper switch: %s' % (lower,upper)
                switchstate = 0
                if int(lower) == 1 and int(upper) == 1:
                    switchstate = 6
                elif int(lower) == 1:
                    switchstate = 4
                elif int(upper) == 1:
                    switchstate = 2
                if switchstate != 0:
                    driver_status += '\nAt least one of the lower/upper switches in activated'
                    state = PyTango.DevState.ALARM

                self.attributes[axis]["statusdriverboard"] = driver_status
                self.attributes[axis]["powerinfo"] = power_info
                return (int(state),switchstate)
            except Exception,e:
                self._log.error('StateOne(%d).\nException:\n%s' % (axis,str(e)))
                raise

        else:
            self._log.debug('StateOne(%d). No connection to %s.' % (axis,self.Host))
        self.attributes[axis]["statusdriverboard"] = driver_status
        self.attributes[axis]["powerinfo"] = power_info
        return (int(PyTango.DevState.ALARM),0)

    def PreReadAll(self):
        """ If there is no connection, to the Icepap system, return False"""
        if not self.iPAP.connected:
            return False

    def PreReadOne(self,axis):
        pass

    def ReadAll(self):
        """ We connect to the Icepap system for each axis. """
        pass

    def ReadOne(self,axis):
        """ Depending on which is the position register selected (pos_sel) return one or another value.
        @param axis to read the position
        @return the current axis position
        """
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
                self._log.error('ReadOne(%d).\nException:\n%s' % (axis,str(e)))
                raise
        else:
            self._log.debug('ReadOne(%d). No connection to %s.' % (axis,self.Host))
        return None

    def PreStartAll(self):
        """ If there is no connection, to the Icepap system, return False"""
        self.moveMultipleValues = []
        if not self.iPAP.connected:
            return False

    def PreStartOne(self,axis,pos):
        """ Store all positions in a variable and then react on the StartAll method.
        @param axis to start
        @param pos to move to
        """
        if self.iPAP.connected:
            pos = int(pos * self.attributes[axis]["step_per_unit"])
            try:
                self.moveMultipleValues.append((axis,int(pos)))
                return True
            except Exception,e:
                self._log.error('PreStartOne(%d,%f).\nException:\n%s' % (axis,pos,str(e)))
                raise
        else:
            self._log.debug('PreStartOne(%d,%f). No connection to %s.' % (axis,pos,self.Host))

    def StartOne(self,axis,pos):
        pass
            
    def StartAll(self):
        """ Move all axis at all position with just one command to the Icepap Controller. """
        if self.iPAP.connected:
            try:
                self.iPAP.moveMultiple(self.moveMultipleValues)
                self.moveMultipleValues = []
            except Exception,e:
                self._log.error('StartAll(%s).\nException:\n%s' % (str(self.moveMultipleValues),str(e)))
                raise                               
        else:
            self._log.debug('StartAll(). No connection to %s.' % (self.Host))

    def SetPar(self,axis,name,value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
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
                self._log.error('SetPar(%d,%s,%s).\nException:\n%s' % (axis,name,str(value),str(e)))
                raise
        else:
            self._log.debug('SetPar(%d,%s,%s). No connection to %s.' % (axis,name,str(value),self.Host))
        

    def GetPar(self,axis,name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        if self.iPAP.connected:
            try:
                register = self._getStatusRegister(axis)
                if not isinstance(register,int):
                    self._log.warning('GetPar(%d,%s): Invalid register: (%s)' % (axis,name,str(register)))
                    return None
                if IcepapStatus.isDisabled(register):
                    self._log.warning('GetPar(%d,%s): Not active driver.' % (axis,name))
                    return None
                
                # THESE PARAMETERS ARE ONLY ALLOWED ON ACTIVE DRIVERS
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
                self._log.error('GetPar(%d,%s).\nException:\n%s' % (axis,name,str(e)))
                raise
        else:
            self._log.debug('GetPar(%d,%s). No connection to %s.' % (axis,name,self.Host))

        return None

    def GetExtraAttributePar(self,axis,name):
        """ Get Icepap driver particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        if self.iPAP.connected:
            name = name.lower()
            try:
                if name == "indexer":
                    #return self.iPAP.getIndexerSource(axis)
                    return self.iPAP.getIndexer(axis)
                elif name == "position_register":
                    return self.attributes[axis]["pos_sel"]
                elif name == "enableencoder_5v":
                    ans = self.iPAP.getAuxPS(axis)
                    return ans == IcepapAnswers.ON
                elif name.startswith("info"):
                    name = name.upper()
                    #result = self.iPAP.getInfoSource(axis, name)
                    result = self.iPAP.getInfo(axis, name)
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
                elif name == "statusdriverboard":
                    return self.attributes[axis]["statusdriverboard"]
                elif name == "powerinfo":
                    return self.attributes[axis]["powerinfo"]
                else:
                    PyTango.Except.throw_exception("IcepapController_GetExtraAttributePar()", "Error getting " + name + ", not implemented", "GetExtraAttributePar()")
            except Exception,e:
                if name == "encshftenc" or name == "enctgtenc" or name == "posshftenc" or name == "postgtenc":
                    #IN SOME CASES THIS VALUES ARE NOT ACCESSIBLE
                    return
                self._log.error('GetExtraAttributePar(%d,%s).\nException:\n%s' % (axis,name,str(e)))
                raise
        else:
            self._log.debug('GetExtraAttributePar(%d,%s). No connection to %s.' % (axis,name,self.Host))

    def SetExtraAttributePar(self,axis,name,value):
        """ Set Icepap driver particular parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        if self.iPAP.connected:
            name = name.lower()
            try:
                if name == "indexer":
                    if value in IcepapRegisters.IndexerRegisters:
                        #self.iPAP.setIndexerSource(axis, value)
                        self.iPAP.setIndexer(axis, value)
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
                    
                    
                    #self.iPAP.setInfoSource(axis, name, src, polarity)                            
                    self.iPAP.setInfo(axis, name, src, polarity)                            
                else:
                    PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar()r", "Error setting " + name + ", not implemented", "SetExtraAttributePar()")
            except Exception,e:
                self._log.error('SetExtraAttributePar(%d,%s,%s).\nException:\n%s' % (axis,name,str(value),str(e)))
                raise
        else:
            self._log.debug('SetExtraAttributePar(%d,%s,%s). No connection to %s.' % (axis,name,str(value),self.Host))


    def AbortOne(self,axis):
        if self.iPAP.connected:
            #self.iPAP.abortMotor(axis)
            self.iPAP.abort(axis)
            time.sleep(0.050)
        else:
            self._log.debug('AbortOne(%d). No connection to %s.' % (axis,self.Host))

    def StopOne(self,axis):
        if self.iPAP.connected:
            #self.iPAP.stopMotor(axis)
            self.iPAP.stop(axis)
        else:
            self._log.debug('StopOne(%d). No connection to %s.' % (axis,self.Host))


    def DefinePosition(self, axis, position):
        if self.iPAP.connected:
            position = int(position * self.attributes[axis]["step_per_unit"])
            self.iPAP.setPosition(axis, position, self.attributes[axis]["pos_sel"])
        else:
            self._log.debug('DefinePosition(%d,%f). No connection to %s.' % (axis,position,self.Host))


    def GOAbsolute(self, axis, finalpos):
        if self.iPAP.connected:
            ret = self.iPAP.move(axis, finalpos)
        else:
            self._log.debug('GOAbsolute(%d,%f). No connection to %s.' % (axis,finalPos,self.Host))

    def SendToCtrl(self,cmd):
        """ Send the icepap native commands.
        @param command to send to the Icepap controller
        @return the result received
        """
        if self.iPAP.connected:
            cmd = cmd.upper()
            if cmd.find("?") >= 0 or cmd.find("#")>= 0:
                res = self.iPAP.sendWriteReadCommand(cmd)
            elif cmd.find("HELP")>=0:
                res = self.iPAP.sendWriteReadCommand(cmd)
            else:
                res = self.iPAP.sendWriteCommand(cmd)
            return res
        else:
            self._log.debug('SendToCtrl(%s). No connection to %s.' % (cmd,self.Host))


    def __del__(self):
        if self.iPAP.connected:
            self.iPAP.disconnect()


    def _getStatusRegister(self, axis):
        register = self.iPAP.getStatus(axis)
        try:
            if "x" in register:
                register = int(register,16)
            else:
                register = int(register)
        except Exception, e:
            pass
        return register
        
