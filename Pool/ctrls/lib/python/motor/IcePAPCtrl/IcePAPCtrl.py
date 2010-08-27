import PyTango
import socket
import errno
from pool import MotorController
from pool import PoolUtil
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
                             'PosMotor':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncAxis':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncIndexer':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             #'EncExtErr':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             'EncShftEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncTgtEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncEncIn':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncInPos':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             'EncAbsEnc':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             ## 12/08/2009 REQUESTED FROM LOTHAR, A COMPLETE MESSAGE ABOUT WHAT IS HAPPENING
                             'StatusDriverBoard':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             ## 12/08/2009 GOOD TO KNOW WHAT IS REALLY HAPPENING TO THE AXIS POWER STATE
                             'PowerInfo':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             ## 19/03/2010 USAGE OF THE FSTATUS MULTICOMMAND FOR THE TRITON
                             'MotorEnabled':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                             ## 30/03/2010 ADD ALL INFO FROM STATUS AS EXTRA ATTRIBUTES
                             'Status5vpower':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusAlive':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusCode':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ'},
                             'StatusPowerOn':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusDisable':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             'StatusHome':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusIndexer':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             'StatusInfo':{'Type':'PyTango.DevLong','R/W Type':'PyTango.READ'},
                             'StatusLim+':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusLim-':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusMode':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             'StatusMoving':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusOutOfWin':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusPresent':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusReady':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusSettling':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusStopCode':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             'StatusVersErr':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusWarning':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ'},
                             'StatusDetails':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ'},
                             ## 30/03/2010 ADD THE POSSIBILITY OF HAVING AN EXTERNAL ENCODER SOURCE WITH SPECIFIC FORMULA
                             'UseEncoderSource':{'Type':'PyTango.DevBoolean','R/W Type':'PyTango.READ_WRITE'},
                             'EncoderSource':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             'EncoderSourceFormula':{'Type':'PyTango.DevString','R/W Type':'PyTango.READ_WRITE'},
                             'Encoder':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ'},
                             ## 29/07/2010 ALLOW THE USER TO SPECIFY THE SPEED AS A 'FREQUENCY' OF THE MOTOR STEPS
                             'Frequency':{'Type':'PyTango.DevDouble','R/W Type':'PyTango.READ_WRITE'},
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
        # DO NOT CONNECT BY DEFAULT SINCE THIS CAN RAISE A TANGO TIMEOUT EXCEPTION IN THE POOL COMMAND CreateController.
        # self.iPAP.connect()
        self.attributes = {}
        self.stateMultiple = []
        self.positionMultiple = []
        self.moveMultipleValues = []

    def AddDevice(self,axis):
        """ Set default values for the axis and try to connect to it
        @param axis to be added
        """
        self.attributes[axis] = {}
        self.attributes[axis]["step_per_unit"] = 1
        self.attributes[axis]["status_value"] = None
        self.attributes[axis]["last_state_value"] = None
        self.attributes[axis]["position_value"] = None
        self.attributes[axis]["MotorEnabled"] = True
        self.attributes[axis]['use_encoder_source'] = False
        self.attributes[axis]['encoder_source'] = 'attr://EncEncIn'
        self.attributes[axis]['encoder_source_formula'] = 'VALUE'
        self.attributes[axis]['encoder_source_tango_attribute'] = FakedAttributeProxy(self, axis, 'attr://EncEncIn')

        if self.iPAP.connected:
            drivers_alive = self.iPAP.getDriversAlive()
            if axis in drivers_alive:
                self._log.info('Added axis %d.' % axis)
            else:
                self.attributes[axis]["MotorEnabled"] = False
                self._log.warning('Added axis %d BUT NOT ALIVE -> MotorEnabled set to False.' % axis)
        else:
            self._log.error('AddDevice(%d). No connection to %s.' % (axis,self.Host))


    def DeleteDevice(self,axis):
        """ Nothing special to do. """
        pass

    def PreStateAll(self):
        """ If there is no connection, to the Icepap system, return False"""
        self.stateMultiple = []
        if not self.iPAP.connected:
            return False

    def PreStateOne(self,axis):
        """ Store all positions in a variable and then react on the StateAll method.
        @param axis to get state
        """
        if self.attributes[axis]['MotorEnabled'] == True:
            self.stateMultiple.append(axis)
            

    def StateAll(self):
        """ Get State of all axis with just one command to the Icepap Controller. """
        if self.iPAP.connected:
            try:
                ans = self.iPAP.getMultipleStatus(self.stateMultiple)
                for axis, status in ans:
                    self.attributes[axis]['status_value'] = status
            except Exception,e:
                self._log.error('StateAll(%s) Hint: some driver board not present?.\nException:\n%s' % (str(self.stateMultiple),str(e)))
        else:
            self._log.error('StateAll(). No connection to %s.' % (self.Host))

    def StateOne(self,axis):
        """ Connect to the hardware and check the state. If no connection available, return ALARM.
        @param axis to read the state
        @return the state value: {ALARM|ON|MOVING}
        """
        if axis not in self.stateMultiple:
            self._log.warning('StateOne(%d) Not enabled. Check the Driver Board is present in %s.'%(axis,self.Host))
            self.attributes[axis]["last_state_value"] = PyTango.DevState.ALARM
            return (PyTango.DevState.ALARM, 'Motor Not Enabled or Not Present', 0)

        status_template = "STATE(%s) PWR(%s) RDY(%s) MOVING(%s) SETTLING(%s) STPCODE(%s) LIM+(%s) LIM-(%s)"
        status_state = '?'
        status_power = '?'
        status_ready = '?'
        status_moving = '?'
        status_settling = '?'
        status_stopcode = '?'
        status_limpos = '?'
        status_limneg = '?'
        if self.iPAP.connected:
            try:
                register = self.attributes[axis]['status_value']
                status_dict = self.iPAP.decodeStatus(register)
                previous_state = self.attributes[axis]["last_state_value"]


                if status_dict is None:
                    self.attributes[axis]["last_state_value"] = PyTango.DevState.ALARM
                    return (PyTango.DevState.ALARM, 'Status Register not available', 0)

                # CHECK POWER LED
                poweron = status_dict['poweron'][0]
                disable, status_power = status_dict['disable']
                if poweron == 1:
                    state = PyTango.DevState.ON
                    status_state = 'ON'
                else:
                    state = PyTango.DevState.ALARM
                    status_state = 'ALARM_AXIS_DISABLE'

                # CHECK LIMIT SWITCHES
                lower, status_limneg = status_dict['lim-']
                upper, status_limpos = status_dict['lim+']
                switchstate = 0
                if lower == 1 and upper == 1:
                    switchstate = 6
                elif lower == 1:
                    switchstate = 4
                elif upper == 1:
                    switchstate = 2
                if switchstate != 0 and state == PyTango.DevState.ON:
                    state = PyTango.DevState.ALARM
                    status_state = 'ALARM_LIMIT_SWITCH'
                        
                # CHECK READY
                # Not used because slave axis are 'BUSY' (NOT READY) and should not be an alarm
                ready, status_ready = status_dict['ready']
                #if ready == 0 and state == PyTango.DevState.ON:
                #    state = PyTango.DevState.ALARM
                #    status_state = 'ALARM_NOT_READY'

                # CHECK MOTION
                moving, status_moving = status_dict['moving']
                settling, status_settling = status_dict['settling']
                if moving == 1 or settling == 1:
                    state = PyTango.DevState.MOVING
                    status_state = 'MOVING'

                # STOP CODE
                status_stopcode = status_dict['stopcode'][1]

                # CHECK CONFIG MODE BUT THIS IS VERY LOW_PERFORMANCE (INDIVIDUAL QUERY PER AXIS)
                # TWO OPTIONS, PUT CONFIG MODE IN STATUS REGISTER
                #              OR PROVIDE MULTI_AXIS COMMAND FOR MODE - SOMETHING LIKE ?FMODE
                #if self.iPAP.getMode(axis) == IcepapMode.CONFIG:
                #    state = PyTango.DevState.ALARM
                #    status_state = 'ALARM_CONFIG'

                status_string = status_template % (status_state,status_power,status_ready,status_moving,status_settling,status_stopcode,upper,lower)
                if previous_state != PyTango.DevState.ALARM and state == PyTango.DevState.ALARM:
                    dump = self.iPAP.debug_internals(axis)
                    self._log.warning('StateOne(%d).State change from %s to %s. Icepap internals dump:\n%s' % (axis, previous_state, state, dump))
                self.attributes[axis]["last_state_value"] = state
                return (state, status_string, switchstate)
            except Exception,e:
                self._log.error('StateOne(%d).\nException:\n%s' % (axis,str(e)))
                raise

        else:
            self._log.error('StateOne(%d). No connection to %s.' % (axis,self.Host))
        return (PyTango.DevState.ALARM, 'Icepap Not Connected', 0)

    def PreReadAll(self):
        """ If there is no connection, to the Icepap system, return False"""
        self.positionMultiple = []
        if not self.iPAP.connected:
            return False

    def PreReadOne(self,axis):
        self.attributes[axis]["position_value"] = None
        # THERE IS AN IMPROVEMENT HERE, WE COULD GROUP ALL THE AXIS WHICH HAVE A COMMON TANGO DEVICE IN THE POSITION SOURCE
        # AND QUERY ALL AT ONCE THE ATTRIBUTES RELATED TO THOSE AXIS
        # OF COURSE THIS MEANS THAT ReadAll HAS ALSO TO BE REIMPLEMENTED
        # AND self.positionMultiple HAS TO BE SPLITTED IN ORDER TO QUERY SOME AXIS TO ICEPAP
        # SOME OTHERS TO ONE DEVICE, SOME OTHERS TO ANOTHER DEVICE, ETC....
        if self.attributes[axis]['MotorEnabled'] == True and not self.attributes[axis]['use_encoder_source']:
            self.positionMultiple.append(axis)

    def ReadAll(self):
        """ We connect to the Icepap system for each axis. """
        if self.iPAP.connected:
            try:
                ans = self.iPAP.getMultiplePosition(self.positionMultiple)
                for axis, position in ans:
                    self.attributes[axis]['position_value'] = long(position)
            except Exception,e:
                self._log.error('ReadAll(%s) Hint: some driver board not present?.\nException:\n%s' % (str(self.positionMultiple),str(e)))
        else:
            self._log.error('ReadAll(). No connection to %s.' % (self.Host))

    def ReadOne(self,axis):
        """ Read the position of the axis.
        @param axis to read the position
        @return the current axis position
        """
        if axis not in self.positionMultiple:
            # IN CASE OF EXTERNAL SOURCE, JUST READ IT AND EVALUATE THE FORMULA
            if self.attributes[axis]['use_encoder_source']:
                return self.GetExtraAttributePar(axis,'Encoder')
            else:
                self._log.warning('ReadOne(%d) Not enabled. Check the Driver Board is present in %s.'%(axis,self.Host))
                raise Exception(self.inst_name,'Axis %d is not enabled: No position value available'%axis)

        if self.iPAP.connected:
            try:
                pos = self.attributes[axis]['position_value']
                return (1.0 * pos) / self.attributes[axis]["step_per_unit"]
            except Exception,e:
                self._log.error('ReadOne(%d).\nException:\n%s' % (axis,str(e)))
                raise
        else:
            self._log.error('ReadOne(%d). No connection to %s.' % (axis,self.Host))
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
            desired_absolute_steps_pos = long(pos * self.attributes[axis]["step_per_unit"])
            # CHECK IF THE POSITION SOURCE IS SET, IN THAT CASE POS HAS TO BE RECALCULATED USING SOURCE + FORMULA
            if self.attributes[axis]['use_encoder_source']:
                current_source_pos = self.GetExtraAttributePar(axis,'Encoder')
                position_increment = pos - current_source_pos
                steps_increment = long(position_increment * self.attributes[axis]["step_per_unit"])
                current_steps_pos = long(self.iPAP.getPosition(axis))
                desired_absolute_steps_pos = current_steps_pos + steps_increment
            try:
                self.moveMultipleValues.append((axis,desired_absolute_steps_pos))
                return True
            except Exception,e:
                self._log.error('PreStartOne(%d,%f).\nException:\n%s' % (axis,pos,str(e)))
                raise
        else:
            self._log.error('PreStartOne(%d,%f). No connection to %s.' % (axis,pos,self.Host))
        
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
            self._log.error('StartAll(). No connection to %s.' % (self.Host))

    def SetPar(self,axis,name,value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """
        if self.iPAP.connected:
            try:
                if name.lower() == "velocity":
                    value_steps = value * self.attributes[axis]["step_per_unit"]
                    self.iPAP.setSpeed(axis, value_steps)
                elif name.lower() == "base_rate":
                    # ONLY ALLOWED WHEN CONFIGURING THE MOTOR (IcepapCMS)
                    self._log.error('SetPar(%d,%s,%s).\nThis is a configuration parameter set by an expert with IcepapCMS\n' % (axis,name,str(value)))
                    raise Exception('This is a configuration parameter set by an expert with IcepapCMS')
                elif name.lower() == "acceleration" or name == "deceleration":
                    self.iPAP.setAcceleration(axis, value)
                elif name.lower() == "step_per_unit":
                    self.attributes[axis]["step_per_unit"] = float(value)
            except Exception,e:
                self._log.error('SetPar(%d,%s,%s).\nException:\n%s' % (axis,name,str(value),str(e)))
                raise
        else:
            self._log.error('SetPar(%d,%s,%s). No connection to %s.' % (axis,name,str(value),self.Host))


    def GetPar(self,axis,name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """
        if self.iPAP.connected:
            try:
                if name.lower() == "velocity":
                    freq = self.iPAP.getSpeed(axis)
                    freq_float = 1.0 * float(freq)
                    return float(freq_float / self.attributes[axis]["step_per_unit"])
                elif name.lower() == "base_rate":
                    start_vel = self.iPAP.getCfgParameter(axis, "STRTVEL")
                    strt_vel_float = 1.0 * float(start_vel)
                    return float(strt_vel_float / self.attributes[axis]["step_per_unit"])
                elif name.lower() == "acceleration" or name.lower() == "deceleration":
                    return float(self.iPAP.getAcceleration(axis))
                elif name.lower() == "step_per_unit":
                    return float(self.attributes[axis]["step_per_unit"])
            except Exception,e:
                self._log.error('GetPar(%d,%s).\nException:\n%s' % (axis,name,str(e)))
                raise
        else:
            self._log.error('GetPar(%d,%s). No connection to %s.' % (axis,name,self.Host))

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
                    ans = self.iPAP.getPositionFromBoard(axis,"AXIS")
                    return float(ans)
                elif name == "posindexer":
                    ans = self.iPAP.getPositionFromBoard(axis,"INDEXER")
                    return float(ans)
                ##elif name == "posposerr":
                ##    ans = self.iPAP.getPosition(axis,"POSERR")
                ##    return ans
                elif name == "posshftenc":
                    ans = self.iPAP.getPositionFromBoard(axis,"SHFTENC")
                    return float(ans)
                elif name == "postgtenc":
                    ans = self.iPAP.getPositionFromBoard(axis,"TGTENC")
                    return float(ans)
                elif name == "posencin":
                    ans = self.iPAP.getPositionFromBoard(axis,"ENCIN")
                    return float(ans)
                elif name == "posinpos":
                    ans = self.iPAP.getPositionFromBoard(axis,"INPOS")
                    return float(ans)
                elif name == "posabsenc":
                    ans = self.iPAP.getPositionFromBoard(axis,"ABSENC")
                elif name == "posmotor":
                    ans = self.iPAP.getPositionFromBoard(axis,"MOTOR")
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
                elif name == "powerinfo":
                    ans = self.iPAP.isg_powerinfo(axis)
                    return ans
                elif name == 'motorenabled':
                    return self.attributes[axis]["MotorEnabled"]
                elif name == "statusdriverboard":
                    ans = self.iPAP.decodeStatus(self.attributes[axis]["status_value"])
                    return str(ans)
                elif name == "statusdetails":
                    ans = self.iPAP.getVStatus(axis)
                    return str(ans)
                elif name.startswith('status'):
                    #register = self.iPAP.getStatusFromBoard(axis)
                    register = self.attributes[axis]["status_value"]
                    status_dict = self.iPAP.decodeStatus(register)
                    status_key = name.replace('status','')
                    if status_key in ['disable','indexer','mode','stopcode']:
                        return status_dict[status_key][1]
                    elif status_key == 'info':
                        return int(status_dict[status_key][0])
                    elif status_key == 'code':
                        return int(register,16)
                    else:
                        return bool(status_dict[status_key][0])
                elif name == 'useencodersource':
                    return self.attributes[axis]['use_encoder_source']
                elif name == 'encodersource':
                    return self.attributes[axis]['encoder_source']
                elif name == 'encodersourceformula':
                    return self.attributes[axis]['encoder_source_formula']
                elif name == 'encoder':
                    try:
                        if self.attributes[axis]['encoder_source_tango_attribute'] != None:
                            VALUE = self.attributes[axis]['encoder_source_tango_attribute'].read().value
                            value = VALUE
                            current_source_pos = eval(self.attributes[axis]['encoder_source_formula'])
                            return float(current_source_pos)
                        else:
                            return float('NaN')
                    except Exception,e:
                        self._log.error('Encoder(%d). Could not read from encoder source (%s)\nException:\n%s' % (axis,self.attributes[axis]['encoder_source'],str(e)))
                        raise e
                elif name == 'frequency':
                    return float(self.iPAP.getSpeed(axis))
                else:
                    PyTango.Except.throw_exception("IcepapController_GetExtraAttributePar()", "Error getting " + name + ", not implemented", "GetExtraAttributePar()")
            except Exception,e:
                if name == "encshftenc" or name == "enctgtenc" or name == "posshftenc" or name == "postgtenc":
                    #IN SOME CASES THIS VALUES ARE NOT ACCESSIBLE
                    return
                self._log.error('GetExtraAttributePar(%d,%s).\nException:\n%s' % (axis,name,str(e)))
                raise
        else:
            self._log.error('GetExtraAttributePar(%d,%s). No connection to %s.' % (axis,name,self.Host))

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
                        PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar()", "Error setting " + name + ", value not in "+str(IcepapRegisters.IndexerRegisters), "SetExtraAttributePar()")
                elif name == "enableencoder_5v":
                    if value:
                        self.iPAP.setAuxPS(axis, IcepapAnswers.ON)
                    else:
                        self.iPAP.setAuxPS(axis, IcepapAnswers.OFF)
                elif name == "poweron":
                    if value:
                        # IN SOME CASES THE POWER CAN BE AUTOMATICALLY SWITCHED OFF BECAUSE CLOSE LOOP FAILURE
                        # POWER ON IS ONLY POSSIBLE IF ENCODERS ARE SYNCHED
                        # IT SHOULD BE BETTER CHECKING A FUTURE 'DoEsyncWhenPowerOn' EXTRA ATTRIBUTE
                        #self.iPAP.syncEncoders(axis)
                        self.iPAP.setPower(axis, IcepapAnswers.ON)
                    else:
                        self.iPAP.setPower(axis, IcepapAnswers.OFF)
                ## Fulvio requires this closed loop boolean attribute
                elif name == "closedloop":
                    if value:
                        self.iPAP.setClosedLoop(axis,"ON")
                    else:
                        self.iPAP.setClosedLoop(axis,"OFF")
                elif name == 'motorenabled':
                    self.attributes[axis]["MotorEnabled"] = value

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
                elif name == 'useencodersource':
                    self.attributes[axis]['use_encoder_source'] = value
                elif name == 'encodersource':
                    self.attributes[axis]['encoder_source'] = value
                    self.attributes[axis]['encoder_source_tango_attribute'] = None
                    try:
                        if value != '':
                            try:
                                # check if it is an internal attribute
                                if value.lower().startswith('attr://'):
                                    self.attributes[axis]['encoder_source_tango_attribute'] = FakedAttributeProxy(self, axis, value)
                                else:
                                    self.attributes[axis]['encoder_source_tango_attribute'] = PyTango.AttributeProxy(value)
                            except Exception,e:
                                self._log.error('SetExtraAttributePar(%d,%s).\nException:\n%s' % (axis,name,str(e)))
                                self.attributes[axis]['use_encoder_source'] = False
                    except Exception,e:
                        raise e
                    
                elif name == 'encodersourceformula':
                    self.attributes[axis]['encoder_source_formula'] = value
                elif name == 'frequency':
                    self.iPAP.setSpeed(axis, value)
                else:
                    PyTango.Except.throw_exception("IcepapController_SetExtraAttributePar()r", "Error setting " + name + ", not implemented", "SetExtraAttributePar()")
            except Exception,e:
                self._log.error('SetExtraAttributePar(%d,%s,%s).\nException:\n%s' % (axis,name,str(value),str(e)))
                raise
        else:
            self._log.error('SetExtraAttributePar(%d,%s,%s). No connection to %s.' % (axis,name,str(value),self.Host))


    def AbortOne(self,axis):
        if self.iPAP.connected:
            #self.iPAP.abortMotor(axis)
            self.iPAP.abort(axis)
            time.sleep(0.050)
        else:
            self._log.error('AbortOne(%d). No connection to %s.' % (axis,self.Host))

    def DefinePosition(self, axis, position):
        if self.iPAP.connected:
            position = long(position * self.attributes[axis]["step_per_unit"])
            self.iPAP.setPosition(axis, position)
        else:
            self._log.error('DefinePosition(%d,%f). No connection to %s.' % (axis,position,self.Host))


    #def GOAbsolute(self, axis, finalpos):
    #    if self.iPAP.connected:
    #        ret = self.iPAP.move(axis, finalpos)
    #    else:
    #        self._log.error('GOAbsolute(%d,%f). No connection to %s.' % (axis,finalPos,self.Host))

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
            self._log.error('SendToCtrl(%s). No connection to %s.' % (cmd,self.Host))


    def __del__(self):
        if self.iPAP.connected:
            self.iPAP.disconnect()


#########################################################
# THIS TWO CLASSES ARE NEEDED BECAUSE IT IS NOT POSSIBLE
# TO ACCESS THE DEVICE FROM A DEVICE CALL
#########################################################
class FakedAttribute():
    def __init__(self, value):
        self.value = value

class FakedAttributeProxy():
    def __init__(self, controller, axis, attribute):
        self.ctrl = controller
        self.axis = axis
        self.attribute = attribute.replace('attr://','')
    def read(self):
        value = self.ctrl.GetExtraAttributePar(self.axis, self.attribute)
        return FakedAttribute(value)
        
