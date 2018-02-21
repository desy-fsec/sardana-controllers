##############################################################################
##
# This file is part of Sardana
##
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
##
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
##
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
##
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

# import socket
# import errno
import time
# import math
import numpy
from pyIcePAP import EthIcePAP, IcepapAnswers, IcepapRegisters, IcepapInfo

from PyTango import AttributeProxy

from sardana import State, DataAccess
from sardana.pool.controller import MotorController, Type, Access, \
    Description, DefaultValue, Memorize, NotMemorized, MaxDimSize

# from sardana.pool import PoolUtil

ReadOnly = DataAccess.ReadOnly
ReadWrite = DataAccess.ReadWrite


class IcepapController(MotorController):
    """
    This class is the Sardana motor controller for the ICEPAP motor controller.
    Appart from the standard Pool motor interface per axis, it provides extra
    attributes for some firmware attributes of the driver.
    """

    # ctrl_features = ['Encoder','Home_speed','Home_acceleration']

    # The properties used to connect to the IcePAP motor controller
    ctrl_properties = {
        'Host': {Type: str, Description: 'The host name'},
        'Port': {Type: int, Description: 'The port number',
                 DefaultValue: 5000},
        'Timeout': {Type: int, Description: 'Connection timeout',
                    DefaultValue: 3}
    }

    ctrl_attributes = {
        'Pmux': {
            Type: str,
            Description: 'Attribute to set/get the PMUX configuration. See '
                         'IcePAP user manual pag. 107',
            Access: DataAccess.ReadWrite,
            Memorize: NotMemorized},
    }
    # The axis extra attributes that correspond to extra features from the
    # Icepap drivers
    axis_attributes = {
        'Indexer': {Type: str, Access: ReadWrite},
        'PowerOn': {Type: bool, Access: ReadWrite},
        'InfoA': {Type: str, Access: ReadWrite},
        'InfoB': {Type: str, Access: ReadWrite},
        'InfoC': {Type: str, Access: ReadWrite},
        'EnableEncoder_5V': {Type: bool, Access: ReadWrite},
        # Fulvio requires this closed loop boolean attribute
        'ClosedLoop': {Type: bool, Access: ReadWrite},
        # Julio Lidon points out that this info is very useful:
        # ?POS : AXIS INDEXER POSERR SHFTENC TGTENC ENCIN INPOS ABSENC
        # ?ENC : AXIS INDEXER EXTERR SHFTENC TGTENC ENCIN INPOS ABSENC
        'PosAxis': {Type: float, Access: ReadOnly},
        'PosIndexer': {Type: float, Access: ReadOnly},
        # 'PosPosErr':{Type:str,Access:ReadOnly},
        'PosShftEnc': {Type: float, Access: ReadOnly},
        'PosTgtEnc': {Type: float, Access: ReadOnly},
        'PosEncIn': {Type: float, Access: ReadOnly},
        'PosInPos': {Type: float, Access: ReadOnly},
        'PosAbsEnc': {Type: float, Access: ReadOnly},
        'PosMotor': {Type: float, Access: ReadOnly},
        'EncAxis': {Type: float, Access: ReadOnly},
        'EncIndexer': {Type: float, Access: ReadOnly},
        # 'EncExtErr':{Type:str,Access:ReadOnly},
        'EncShftEnc': {Type: float, Access: ReadOnly},
        'EncTgtEnc': {Type: float, Access: ReadOnly},
        'EncEncIn': {Type: float, Access: ReadOnly},
        'EncInPos': {Type: float, Access: ReadOnly},
        'EncAbsEnc': {Type: float, Access: ReadOnly},
        # 12/08/2009 REQUESTED FROM LOTHAR, A COMPLETE MESSAGE ABOUT WHAT
        # IS HAPPENING
        'StatusDriverBoard': {Type: str, Access: ReadOnly},
        # 12/08/2009 GOOD TO KNOW WHAT IS REALLY HAPPENING TO THE AXIS
        # POWER STATE
        'PowerInfo': {Type: str, Access: ReadOnly},
        # 19/03/2010 USAGE OF THE FSTATUS MULTICOMMAND FOR THE TRITON
        'MotorEnabled': {Type: bool, Access: ReadWrite},
        # 30/03/2010 ADD ALL INFO FROM STATUS AS EXTRA ATTRIBUTES
        'Status5vpower': {Type: bool, Access: ReadOnly},
        'StatusAlive': {Type: bool, Access: ReadOnly},
        'StatusCode': {Type: int, Access: ReadOnly},
        'StatusPowerOn': {Type: bool, Access: ReadOnly},
        'StatusDisable': {Type: str, Access: ReadOnly},
        'StatusHome': {Type: bool, Access: ReadOnly},
        'StatusIndexer': {Type: str, Access: ReadOnly},
        'StatusInfo': {Type: int, Access: ReadOnly},
        'StatusLim+': {Type: bool, Access: ReadOnly},
        'StatusLim-': {Type: bool, Access: ReadOnly},
        'StatusMode': {Type: str, Access: ReadOnly},
        'StatusMoving': {Type: bool, Access: ReadOnly},
        'StatusOutOfWin': {Type: bool, Access: ReadOnly},
        'StatusPresent': {Type: bool, Access: ReadOnly},
        'StatusReady': {Type: bool, Access: ReadOnly},
        'StatusSettling': {Type: bool, Access: ReadOnly},
        'StatusStopCode': {Type: str, Access: ReadOnly},
        'StatusVersErr': {Type: bool, Access: ReadOnly},
        'StatusWarning': {Type: bool, Access: ReadOnly},
        'StatusDetails': {Type: str, Access: ReadOnly},
        # 30/03/2010 ADD THE POSSIBILITY OF HAVING AN EXTERNAL ENCODER SOURCE
        # WITH SPECIFIC FORMULA
        'UseEncoderSource': {Type: bool, Access: ReadWrite},
        'EncoderSource': {Type: str, Access: ReadWrite},
        'EncoderSourceFormula': {Type: str, Access: ReadWrite},
        'Encoder': {Type: float, Access: ReadOnly},
        # 29/07/2010 ALLOW THE USER TO SPECIFY THE SPEED AS A 'FREQUENCY'
        # OF THE MOTOR STEPS
        'Frequency': {Type: float, Access: ReadWrite},
        # 27/07/2016 ALLOW TO SET EcamDat by intervals or table
        'EcamDatInterval': {Type: [float], Access: ReadWrite},
        'EcamDatTable': {Type: [float], Access: ReadWrite, MaxDimSize: 20477},
        # 11/01/2018 ALLOW TO SET SyncAux
        'SyncAux': {Type: [str],
                    Description: 'Internal auxiliary synchronization line. '
                                 'It can use the same signals sources than '
                                 'InfoX.',
                    Access: ReadWrite},
        'EcamOut': {Type: str,
                    Description: 'Ecam signal output [OFF, PULSE, LOW, HIGH]',
                    Access: ReadWrite},
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

    def __init__(self, inst, props, *args, **kwargs):
        """ Do the default init plus the icepap connection
        @param inst instance name of the controller
        @param properties of the controller
        """
        MotorController.__init__(self, inst, props, *args, **kwargs)
        self.iPAP = EthIcePAP(self.Host, self.Port, self.Timeout)
        # Use a secondary socket to execute slow commands (i.e. EcamData) and
        # avoid possible blocking issues. Its use is highly recommended.
        #
        # Now used by ecamdatintervals and ecamdattable extra axis attributes
        #
        self.iPAP2 = EthIcePAP(self.Host, self.Port, self.Timeout)

        # DO NOT CONNECT BY DEFAULT SINCE THIS CAN RAISE A TANGO TIMEOUT
        # EXCEPTION IN THE POOL COMMAND CreateController.
        # self.iPAP.connect()
        self.attributes = {}
        self.stateMultiple = []
        self.positionMultiple = []
        self.moveMultipleValues = []

    def AddDevice(self, axis):
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
        self.attributes[axis]['encoder_source_tango_attribute'] = \
            FakedAttributeProxy(self, axis, 'attr://EncEncIn')

        if self.iPAP.connected:
            drivers_alive = self.iPAP.getDriversAlive()
            if axis in drivers_alive:
                self._log.info('Added axis %d.' % axis)
            else:
                self.attributes[axis]["MotorEnabled"] = False
                self._log.warning('Added axis %d BUT NOT ALIVE -> '
                                  'MotorEnabled set to False.' % axis)
        else:
            self._log.error('AddDevice(%d). No connection to %s.' %
                            (axis, self.Host))

    def DeleteDevice(self, axis):
        """ Nothing special to do. """
        pass

    def PreStateAll(self):
        """ If there is no connection, to the Icepap system, return False"""
        self.stateMultiple = []
        if not self.iPAP.connected:
            return False

    def PreStateOne(self, axis):
        """ Store all positions in a variable and then react on the StateAll
        method.
        @param axis to get state
        """
        if self.attributes[axis]['MotorEnabled'] is True:
            self.stateMultiple.append(axis)

    def StateAll(self):
        """
        Get State of all axis with just one command to the Icepap Controller.
        """
        if self.iPAP.connected:
            try:
                ans = self.iPAP.getMultipleStatus(self.stateMultiple)
                for axis, status in ans:
                    self.attributes[axis]['status_value'] = status
            except Exception as e:
                self._log.error('StateAll(%s) Hint: some driver board not '
                                'present?.\nException:\n%s' %
                                (str(self.stateMultiple), str(e)))
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('StateAll(). No connection to %s.' % (self.Host))
            pass

    def StateOne(self, axis):
        """
        Connect to the hardware and check the state. If no connection
        available, return ALARM.
        @param axis to read the state
        @return the state value: {ALARM|ON|MOVING}
        """

        name = self.GetAxisName(axis)
        if axis not in self.stateMultiple:
            self._log.warning('StateOne(%s(%s)) Not enabled. Check the Driver '
                              'Board is present in %s.', name, axis, self.Host)
            self.attributes[axis]["last_state_value"] = State.Alarm
            return State.Alarm, 'Motor Not Enabled or Not Present', 0

        status_template = "STATE(%s) PWR(%s) RDY(%s) MOVING(%s) " \
                          "SETTLING(%s) STPCODE(%s) LIM+(%s) LIM-(%s)"
        # status_state = '?'
        # status_power = '?'
        # status_ready = '?'
        # status_moving = '?'
        # status_settling = '?'
        # status_stopcode = '?'
        # status_limpos = '?'
        # status_limneg = '?'

        if self.iPAP.connected:
            try:
                register = self.attributes[axis]['status_value']
                status_dict = self.iPAP.decodeStatus(register)
                previous_state = self.attributes[axis]["last_state_value"]

                if status_dict is None:
                    self.attributes[axis]["last_state_value"] = State.Alarm
                    return State.Alarm, 'Status Register not available', 0

                # CHECK POWER LED
                poweron = status_dict['poweron'][0]
                disable, status_power = status_dict['disable']
                if poweron == 1:
                    state = State.On
                    status_state = 'ON'
                else:
                    state = State.Alarm
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
                if switchstate != 0 and state == State.On:
                    state = State.Alarm
                    status_state = 'ALARM_LIMIT_SWITCH'

                # CHECK READY
                # Not used because slave axis are 'BUSY' (NOT READY) and
                # should not be an alarm
                ready, status_ready = status_dict['ready']
                # if ready == 0 and state == State.On:
                #     state = State.Alarm
                #     status_state = 'ALARM_NOT_READY'

                # CHECK MOTION
                moving, status_moving = status_dict['moving']
                settling, status_settling = status_dict['settling']
                if moving == 1 or settling == 1:
                    state = State.Moving
                    status_state = 'MOVING'

                # STOP CODE
                status_stopcode = status_dict['stopcode'][1]

                # CHECK CONFIG MODE BUT THIS IS VERY LOW_PERFORMANCE
                # (INDIVIDUAL QUERY PER AXIS) TWO OPTIONS, PUT CONFIG MODE
                # IN STATUS REGISTER OR PROVIDE MULTI_AXIS COMMAND FOR MODE
                # - SOMETHING LIKE ?FMODE
                # if self.iPAP.getMode(axis) == IcepapMode.CONFIG:
                #     state = State.Alarm
                #     status_state = 'ALARM_CONFIG'

                status_string = status_template % (status_state,
                                                   status_power,
                                                   status_ready,
                                                   status_moving,
                                                   status_settling,
                                                   status_stopcode, upper,
                                                   lower)
                if previous_state != State.Alarm and state == State.Alarm:
                    dump = self.iPAP.debug_internals(axis)
                    self._log.warning('StateOne(%s(%s)).State change from %s '
                                      'to %s. Icepap internals dump:\n%s',
                                      name, axis, previous_state,
                                      State[state], dump)
                self.attributes[axis]["last_state_value"] = state

                return state, status_string, switchstate
            except Exception:
                self._log.error('StateOne(%s(%d)) Exception:', name, axis,
                                exc_info=1)
                raise

        else:
            # To prevent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('StateOne(%d). No connection to %s.' %
            #                 (axis, self.Host))
            pass

        return State.Alarm, 'Icepap Not Connected', 0

    def PreReadAll(self):
        """ If there is no connection, to the Icepap system, return False"""
        self.positionMultiple = []
        if not self.iPAP.connected:
            return False

    def PreReadOne(self, axis):
        self.attributes[axis]["position_value"] = None
        # THERE IS AN IMPROVEMENT HERE, WE COULD GROUP ALL THE AXIS WHICH HAVE
        # A COMMON TANGO DEVICE IN THE POSITION SOURCE AND QUERY ALL AT ONCE
        # THE ATTRIBUTES RELATED TO THOSE AXIS OF COURSE THIS MEANS THAT
        # ReadAll HAS ALSO TO BE REIMPLEMENTED AND self.positionMultiple HAS
        # TO BE SPLITTED IN ORDER TO QUERY SOME AXIS TO ICEPAP
        # SOME OTHERS TO ONE DEVICE, SOME OTHERS TO ANOTHER DEVICE, ETC....
        if self.attributes[axis]['MotorEnabled'] is True and not \
                self.attributes[axis]['use_encoder_source']:
            self.positionMultiple.append(axis)

    def ReadAll(self):
        """ We connect to the Icepap system for each axis. """
        if self.iPAP.connected:
            try:
                ans = self.iPAP.getMultiplePositionFromBoard(
                    self.positionMultiple)
                # ans = self.iPAP.getMultiplePosition(self.positionMultiple)
                for axis, position in ans:
                    self.attributes[axis]['position_value'] = long(position)
            except Exception as e:
                self._log.error('ReadAll(%s) Hint: some driver board not '
                                'present?.\nException:\n%s' %
                                (str(self.positionMultiple), str(e)))
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('ReadAll(). No connection to %s.' % (self.Host))
            pass

    def ReadOne(self, axis):
        """ Read the position of the axis.
        @param axis to read the position
        @return the current axis position
        """
        name = self.GetAxisName(axis)
        log = self._log
        if axis not in self.positionMultiple:
            # IN CASE OF EXTERNAL SOURCE, JUST READ IT AND EVALUATE THE FORMULA
            if self.attributes[axis]['use_encoder_source']:
                return self.GetAxisExtraPar(axis, 'Encoder')
            else:
                log.warning('ReadOne(%s(%d)) Not enabled. Check the Driver '
                            'Board is present in %s.', name, axis, self.Host)
                raise Exception('ReadOne(%s(%d)) Not enabled: No position '
                                'value available' % (name, axis))

        if self.iPAP.connected:
            try:
                pos = self.attributes[axis]['position_value']
                return (1.0 * pos) / self.attributes[axis]["step_per_unit"]
            except Exception:
                log.error('ReadOne(%s(%d)) Exception:', name, axis, exc_info=1)
                raise
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # log.error('ReadOne(%s(%d)). No connection to %s.', name, axis,
            #           self.Host)
            pass
        return None

    def PreStartAll(self):
        """ If there is no connection, to the Icepap system, return False"""
        self.moveMultipleValues = []
        if not self.iPAP.connected:
            return False

    def PreStartOne(self, axis, pos):
        """ Store all positions in a variable and then react on the StartAll
        method.
        @param axis to start
        @param pos to move to
        """
        if self.iPAP.connected:
            desired_absolute_steps_pos = long(pos * self.attributes[axis][
                "step_per_unit"])
            # CHECK IF THE POSITION SOURCE IS SET, IN THAT CASE POS HAS TO BE
            # RECALCULATED USING SOURCE + FORMULA
            if self.attributes[axis]['use_encoder_source']:
                current_source_pos = self.GetAxisExtraPar(axis, 'Encoder')
                position_increment = pos - current_source_pos
                steps_increment = long(position_increment * self.attributes[
                    axis]["step_per_unit"])
                current_steps_pos = long(self.iPAP.getPositionFromBoard(axis))
                desired_absolute_steps_pos = current_steps_pos + \
                    steps_increment
            try:
                self.moveMultipleValues.append((axis,
                                                desired_absolute_steps_pos))
                return True
            except Exception as e:
                self._log.error('PreStartOne(%d,%f).\nException:\n%s' %
                                (axis, pos, str(e)))
                raise
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('PreStartOne(%d,%f). No connection to %s.' %
            #                 (axis,pos,self.Host))
            pass

    def StartOne(self, axis, pos):
        pass

    def StartAll(self):
        """ Move all axis at all position with just one command to the Icepap
        Controller. """
        if self.iPAP.connected:
            try:
                self.iPAP.moveMultipleGrouped(self.moveMultipleValues)
                self._log.info('moveMultiple: '+str(self.moveMultipleValues))
                self.moveMultipleValues = []
            except Exception as e:
                self._log.error('StartAll(%s).\nException:\n%s' %
                                (str(self.moveMultipleValues), str(e)))
                raise
        else:
            # To provent huge logs, do not log this error until log levels can
            # be changed in per-controller basis
            # self._log.error('StartAll(). No connection to %s.' % (self.Host))
            pass

    def SetPar(self, axis, name, value):
        """ Set the standard pool motor parameters.
        @param axis to set the parameter
        @param name of the parameter
        @param value to be set
        """

        if name.lower() == "step_per_unit":
            self.attributes[axis]["step_per_unit"] = float(value)

        if self.iPAP.connected:
            try:
                if name.lower() == "velocity":
                    value_steps = value * self.attributes[axis][
                        "step_per_unit"]
                    # setting the velocity changes the icepap acceleration time
                    # for protection. We compensate this by restoring the
                    # acceleration time back to the original value after
                    # setting the new velocity
                    accel_time = self.GetPar(axis, "acceleration")
                    self.iPAP.setSpeed(axis, value_steps)
                    self.iPAP.setAcceleration(axis, accel_time)
                elif name.lower() == "base_rate":
                    pass
                    # ONLY ALLOWED WHEN CONFIGURING THE MOTOR (IcepapCMS)
                    # self._log.error('SetPar(%d,%s,%s).\nThis is a '
                    #                 'configuration parameter set by an '
                    #                 'expert with IcepapCMS\n' %
                    #                 (axis,name,str(value)))
                    # raise Exception('This is a configuration parameter set'
                    #                 'by an expert with IcepapCMS')
                elif name.lower() == "acceleration" or name == "deceleration":
                    self.iPAP.setAcceleration(axis, value)
                elif name.lower() == "step_per_unit":
                    self.attributes[axis]["step_per_unit"] = float(value)
            except Exception as e:
                self._log.error('SetPar(%d,%s,%s).\nException:\n%s' %
                                (axis, name, str(value), str(e)))
                raise
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('SetPar(%d,%s,%s). No connection to %s.' %
            #                 (axis, name, str(value), self.Host))
            pass

    def GetPar(self, axis, name):
        """ Get the standard pool motor parameters.
        @param axis to get the parameter
        @param name of the parameter to get the value
        @return the value of the parameter
        """

        if name.lower() == "step_per_unit":
            return float(self.attributes[axis]["step_per_unit"])

        if self.iPAP.connected:
            try:
                if name.lower() == "velocity":
                    freq = self.iPAP.getSpeed(axis)
                    freq_float = 1.0 * float(freq)
                    return float(freq_float / self.attributes[axis][
                        "step_per_unit"])
                elif name.lower() == "base_rate":
                    return 0
                    # start_vel = self.iPAP.getCfgParameter(axis, "STRTVEL")
                    # strt_vel_float = 1.0 * float(start_vel)
                    # return float(strt_vel_float / self.attributes[axis][
                    # "step_per_unit"])
                elif name.lower() == "acceleration" or name.lower() == \
                        "deceleration":
                    return float(self.iPAP.getAcceleration(axis))
                elif name.lower() == "step_per_unit":
                    return float(self.attributes[axis]["step_per_unit"])
            except Exception as e:
                self._log.error('GetPar(%d,%s).\nException:\n%s' %
                                (axis, name, str(e)))
                raise
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('GetPar(%d,%s). No connection to %s.' % (axis,
            # name,self.Host))
            pass

        return None

    def GetAxisExtraPar(self, axis, name):
        """ Get Icepap driver particular parameters.
        @param axis to get the parameter
        @param name of the parameter to retrive
        @return the value of the parameter
        """
        if self.iPAP.connected:
            name = name.lower()
            try:
                if name == "indexer":
                    # return self.iPAP.getIndexerSource(axis)
                    return self.iPAP.getIndexer(axis)
                elif name == "enableencoder_5v":
                    ans = self.iPAP.getAuxPS(axis)
                    return ans == IcepapAnswers.ON
                elif name.startswith("info"):
                    name = name.upper()
                    # result = self.iPAP.getInfoSource(axis, name)
                    result = self.iPAP.getInfo(axis, name)
                    return result
                elif name == "poweron":
                    ans = self.iPAP.getPower(axis)
                    return ans == IcepapAnswers.ON
                # Fulvio requires this closed loop boolean attribute
                elif name == "closedloop":
                    ans = self.iPAP.getClosedLoop(axis)
                    if ans.count("OFF") > 0:
                        return False
                    return True
                # Julio Lidon points out that this info is very useful:
                # ?POS : AXIS INDEXER POSERR SHFTENC TGTENC ENCIN INPOS ABSENC
                # ?ENC : AXIS INDEXER EXTERR SHFTENC TGTENC ENCIN INPOS ABSENC
                elif name == "posaxis":
                    ans = self.iPAP.getPositionFromBoard(axis, "AXIS")
                    return float(ans)
                elif name == "posindexer":
                    ans = self.iPAP.getPositionFromBoard(axis, "INDEXER")
                    return float(ans)
                # elif name == "posposerr":
                #     ans = self.iPAP.getPosition(axis,"POSERR")
                #     return ans
                elif name == "posshftenc":
                    ans = self.iPAP.getPositionFromBoard(axis, "SHFTENC")
                    return float(ans)
                elif name == "postgtenc":
                    ans = self.iPAP.getPositionFromBoard(axis, "TGTENC")
                    return float(ans)
                elif name == "posencin":
                    ans = self.iPAP.getPositionFromBoard(axis, "ENCIN")
                    return float(ans)
                elif name == "posinpos":
                    ans = self.iPAP.getPositionFromBoard(axis, "INPOS")
                    return float(ans)
                elif name == "posabsenc":
                    ans = self.iPAP.getPositionFromBoard(axis, "ABSENC")
                    return float(ans)
                elif name == "posmotor":
                    ans = self.iPAP.getPositionFromBoard(axis, "MOTOR")
                    return float(ans)
                elif name == "encaxis":
                    ans = self.iPAP.getEncoder(axis, "AXIS")
                    return float(ans)
                elif name == "encindexer":
                    ans = self.iPAP.getEncoder(axis, "INDEXER")
                    return float(ans)
                # elif name == "encexterr":
                #     ans = self.iPAP.getEncoder(axis,"EXTERR")
                #     return ans
                elif name == "encshftenc":
                    ans = self.iPAP.getEncoder(axis, "SHFTENC")
                    return float(ans)
                elif name == "enctgtenc":
                    ans = self.iPAP.getEncoder(axis, "TGTENC")
                    return float(ans)
                elif name == "encencin":
                    ans = self.iPAP.getEncoder(axis, "ENCIN")
                    return float(ans)
                elif name == "encinpos":
                    ans = self.iPAP.getEncoder(axis, "INPOS")
                    return float(ans)
                elif name == "encabsenc":
                    ans = self.iPAP.getEncoder(axis, "ABSENC")
                    return float(ans)
                elif name == "powerinfo":
                    ans = self.iPAP.isg_powerinfo(axis)
                    return ans
                elif name == 'motorenabled':
                    return self.attributes[axis]["MotorEnabled"]
                elif name == "statusdriverboard":
                    ans = self.iPAP.decodeStatus(self.attributes[axis][
                                                     "status_value"])
                    return str(ans)
                elif name == "statusdetails":
                    ans = self.iPAP.getVStatus(axis)
                    return str(ans)
                elif name.startswith('status'):

                    # We apply getStatusFromBoard to update all status
                    self.attributes[axis]['status_value'] = \
                        self.iPAP.getStatusFromBoard(axis)

                    # register = self.iPAP.getStatusFromBoard(axis)
                    register = self.attributes[axis]['status_value']

                    if register is None:
                        register = self.iPAP.getStatusFromBoard(axis)
                    status_dict = self.iPAP.decodeStatus(register)
                    status_key = name.replace('status', '')
                    if status_key in ['disable', 'indexer', 'mode',
                                      'stopcode']:
                        return status_dict[status_key][1]
                    elif status_key == 'info':
                        return int(status_dict[status_key][0])
                    elif status_key == 'code':
                        return int(register, 16)
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
                        enc_src_tango_attr = self.attributes[axis][
                            'encoder_source_tango_attribute']
                        if enc_src_tango_attr is not None:
                            value = enc_src_tango_attr.read().value
                            eval_globals = numpy.__dict__
                            eval_locals = {'VALUE': value, 'value': value}
                            enc_src_formula = self.attributes[axis][
                                'encoder_source_formula']
                            current_source_pos = eval(enc_src_formula,
                                                      eval_globals,
                                                      eval_locals)
                            return float(current_source_pos)
                        else:
                            return float('NaN')
                    except Exception as e:
                        msg = 'Encoder(%d). Could not read from encoder ' \
                              'source (%s)\nException:\n%s' % \
                              (axis, self.attributes[axis]['encoder_source'],
                               str(e))

                        self._log.error(msg)
                        raise e
                elif name == 'frequency':
                    return float(self.iPAP.getSpeed(axis))
                elif name == 'ecamdatinterval':
                    return self.iPAP2.getEcamDatIntervals(axis)
                elif name == 'ecamdattable':
                    # return self.iPAP2.getEcamDat(axis)
                    raise Exception("Requesting the EcamDat table may cause a "
                                    "Timeout error"
                                    "at the icepap level. Use the pyIcePAP "
                                    "module to access these values.")
                elif name == 'syncaux':
                    return self.iPAP.getSyncAux(axis)
                elif name == 'ecamout':
                    config = self.iPAP.getEcamConfig(axis)
                    if config[0] == 'ON':
                        result = config[1]
                    else:
                        result = config[0]
                    return result
                else:
                    axis_name = self.GetAxisName(axis)
                    raise Exception("GetAxisExtraPar(%s(%s), %s): "
                                    "Error getting %s, not implemented"
                                    % (axis_name, axis, name, name))
            except Exception as e:
                if name in ["encshftenc", "enctgtenc", "posshftenc",
                            "postgtenc"]:
                    # IN SOME CASES THIS VALUES ARE NOT ACCESSIBLE
                    return
                self._log.error('GetAxisExtraPar(%d,%s).\nException:\n%s' %
                                (axis, name, str(e)))
                raise
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('GetAxisExtraPar(%d,%s). No connection to %s.' %
            #                 (axis,name,self.Host))
            pass

    def SetAxisExtraPar(self, axis, name, value):
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
                        # self.iPAP.setIndexerSource(axis, value)
                        self.iPAP.setIndexer(axis, value)
                    else:
                        axis_name = self.GetAxisName(axis)
                        raise Exception("SetAxisExtraPar(%s(%s), %s): "
                                        "Error setting %s, value not in %s" %
                                        (axis_name, axis, name, name,
                                         IcepapRegisters.IndexerRegisters))
                elif name == "enableencoder_5v":
                    if value:
                        self.iPAP.setAuxPS(axis, IcepapAnswers.ON)
                    else:
                        self.iPAP.setAuxPS(axis, IcepapAnswers.OFF)
                elif name == "poweron":
                    if value:
                        # IN SOME CASES THE POWER CAN BE AUTOMATICALLY
                        # SWITCHED OFF BECAUSE CLOSE LOOP FAILURE
                        # POWER ON IS ONLY POSSIBLE IF ENCODERS ARE SYNCHED
                        # IT SHOULD BE BETTER CHECKING A FUTURE
                        # 'DoEsyncWhenPowerOn' EXTRA ATTRIBUTE
                        # self.iPAP.syncEncoders(axis)
                        self.iPAP.setPower(axis, IcepapAnswers.ON)
                    else:
                        self.iPAP.setPower(axis, IcepapAnswers.OFF)
                # Fulvio requires this closed loop boolean attribute
                elif name == "closedloop":
                    if value:
                        self.iPAP.setClosedLoop(axis, "ON")
                    else:
                        self.iPAP.setClosedLoop(axis, "OFF")
                elif name == 'motorenabled':
                    self.attributes[axis]["MotorEnabled"] = value

                elif name.startswith("info"):
                    axis_name = self.GetAxisName(axis)
                    name = name.upper()
                    value = value.split()
                    src = value[0].upper()

                    if src not in IcepapInfo.Sources:
                        raise Exception("SetAxisExtraPar(%s(%s), %s): "
                                        "Error setting %s. [Source = (%s), "
                                        "Polarity= (%s)]"
                                        % (axis_name, axis, name, name,
                                           IcepapInfo.Sources,
                                           IcepapInfo.Polarity))
                    polarity = "NORMAL"
                    if len(value) > 1:
                        polarity = value[1].upper()
                        if polarity not in IcepapInfo.Polarity:
                            raise Exception("SetAxisExtraPar(%s(%s), %s): "
                                            "Error setting %s. "
                                            "[Source = (%s), "
                                            "Polarity= (%s)]" %
                                            (axis_name, axis, name, name,
                                             IcepapInfo.Sources,
                                             IcepapInfo.Polarity))
                    # self.iPAP.setInfoSource(axis, name, src, polarity)

                    self.iPAP.setInfo(axis, name, src, polarity)
                elif name == 'useencodersource':
                    self.attributes[axis]['use_encoder_source'] = value
                elif name == 'encodersource':
                    self.attributes[axis]['encoder_source'] = value
                    self.attributes[axis]['encoder_source_tango_attribute'] \
                        = None
                    try:
                        if value != '':
                            try:
                                # check if it is an internal attribute
                                enc_src_name = 'encoder_source_tango_attribute'
                                if value.lower().startswith('attr://'):
                                    # 2012/03/27 Improve attr:// syntax to
                                    # allow reading of other axis of the same
                                    # system without
                                    # having to access them via tango://
                                    value_contents = value[7:]
                                    if ':' not in value_contents:
                                        self.attributes[axis][enc_src_name] = \
                                            FakedAttributeProxy(self, axis,
                                                                value)
                                    else:
                                        other_axis, other_value = \
                                            value_contents.split(':')
                                        other_axis = int(other_axis)
                                        other_value = 'attr://'+other_value
                                        self.attributes[axis][enc_src_name] = \
                                            FakedAttributeProxy(self,
                                                                other_axis,
                                                                other_value)
                                else:
                                    self.attributes[axis][enc_src_name] = \
                                        AttributeProxy(value)
                            except Exception as e:
                                self._log.error('SetAxisExtraPar(%d,%s).'
                                                '\nException:\n%s' %
                                                (axis, name, str(e)))
                                self.attributes[axis]['use_encoder_source'] \
                                    = False
                    except Exception as e:
                        raise e

                elif name == 'encodersourceformula':
                    self.attributes[axis]['encoder_source_formula'] = value
                elif name == 'frequency':
                    self.iPAP.setSpeed(axis, value)
                elif name == 'ecamdatinterval':
                    start_pos, end_pos, nintervals = value
                    self.iPAP2.sendEcamDatIntervals(axis, start_pos, end_pos,
                                                    nintervals)
                elif name == 'ecamdattable':
                    # 2017/Oct/27 - in some cases, we get an exception when
                    # setting PULSE signal
                    # 2017/Oct/27
                    # TODO for long tables, sometimes we get:
                    # N:ECAM ERROR Not initialised ECAM data
                    # NOTE: IN PARAMETRIC TRAJECTORIES, THE SOURCE OF THE
                    # TABLE MAY NOT BE AXIS (default) BUT PARAM
                    # sendEcamDat(axis, source=SOURCE, position_list=value)
                    try:
                        self.iPAP2.sendEcamDat(axis, position_list=value)
                    except Exception as e:
                        self._log.error('SetAxisExtraPar(%d,%s,%s).\n'
                                        'Exception:\n%s' %
                                        (axis, name, str(value), str(e)))
                        self._log.error('Since it is a known bug... just '
                                        'retry once more time.. :-(')
                        # JUST try again... :-(
                        self.iPAP2.sendEcamDat(axis, position_list=value)
                elif name == 'syncaux':
                    signal = value[0]
                    polarity = 'normal'
                    if len(value) > 1:
                        polarity = value[1]
                    self.iPAP.setSyncAux(axis, signal, polarity)
                elif name == 'ecamout':
                    if value.lower == 'off':
                        self.iPAP.setEcamConfig(axis, False)
                    else:
                        self.iPAP.setEcamConfig(axis, True, value)
                else:
                    axis_name = self.GetAxisName(axis)
                    raise Exception("SetAxisExtraPar(%s(%s), %s): "
                                    "Error setting %s, not implemented"
                                    % (axis_name, axis, name, name))
            except Exception as e:
                self._log.error('SetAxisExtraPar(%d,%s,%s).\nException:\n%s' %
                                (axis, name, str(value), str(e)))
                raise
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('SetAxisExtraPar(%d,%s,%s). No connection to'
            #                 ' %s.' % (axis,name,str(value),self.Host))
            pass

    def StopOne(self, axis):
        if self.iPAP.connected:
            self.iPAP.stop(axis)
            # not sure about that, it comes from AbortOne implementation
            time.sleep(0.050)
            # due to the IcePAP firmware bug:
            # axes with velocity to acceleration time factor less that 18
            # are not stoppable
            try:
                vel = float(self.iPAP.getSpeed(axis))
                acc = float(self.iPAP.getAcceleration(axis))
                factor = vel / acc
            except Exception, e:
                msg = 'Problems while trying to determine velocity to ' + \
                      'acceleration factor'
                self._log.error('StopOne(%d): %s. Trying to abort...' %
                                (axis, msg))
                self._log.debug(e)
                self.AbortOne(axis)
                raise Exception(msg)
            if factor < 18:
                self.AbortOne(axis)
        else:
            # To provent huge logs, do not log this error until log levels can
            # be changed in per-controller basis
            # self._log.error('StopOne(%d). No connection to %s.' % \
            #                                                 (axis,self.Host))
            pass

    def AbortOne(self, axis):
        if self.iPAP.connected:
            # self.iPAP.abortMotor(axis)
            self.iPAP.abort(axis)
            time.sleep(0.050)
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('AbortOne(%d). No connection to %s.' %
            #                 (axis, self.Host))
            pass

    def DefinePosition(self, axis, position):
        if self.iPAP.connected:
            position = long(position * self.attributes[axis]["step_per_unit"])
            self.iPAP.setPosition(axis, position)
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('DefinePosition(%d,%f). No connection to %s.'
            #                  % (axis,position,self.Host))
            pass

    # def GOAbsolute(self, axis, finalpos):
    #     if self.iPAP.connected:
    #         ret = self.iPAP.move(axis, finalpos)
    #     else:
    #         self._log.error('GOAbsolute(%d,%f). No connection to %s.' %
    #                         (axis,finalPos,self.Host))

    def SendToCtrl(self, cmd):
        """ Send the icepap native commands.
        @param cmd: command to send to the Icepap controller
        @return the result received
        """
        if self.iPAP.connected:
            res = None
            cmd = cmd.upper()
            if cmd.find("?") >= 0 or cmd.find("#") >= 0:
                res = self.iPAP.sendWriteReadCommand(cmd)
            elif cmd.find("HELP") >= 0:
                res = self.iPAP.sendWriteReadCommand(cmd)
            else:
                self.iPAP.sendWriteCommand(cmd)
            if res is not None:
                return res
            # added by zreszela on 8.02.2013
            else:
                return ""
        else:
            # To provent huge logs, do not log this error until log levels
            # can be changed in per-controller basis
            # self._log.error('SendToCtrl(%s). No connection to %s.' % (cmd,
            #  self.Host))
            return 'SendToCtrl(%s). No connection to %s.' % (cmd, self.Host)

    def SetCtrlPar(self, parameter, value):
        param = parameter.lower()
        if param == 'pmux':
            value = value.lower()
            if 'remove' in value:
                args = value.split()
                dest = ''
                if len(args) > 1:
                    dest = args[-1]
                self.iPAP.clearPmux(dest=dest)
            else:
                args = value.split()
                if len(args) == 1:
                    self.iPAP.setPmux(source=args[0])
                else:
                    hard = 'hard' in args
                    if hard:
                        args.pop(args.index('hard'))
                    pos = 'pos' in args
                    if pos:
                        args.pop(args.index('pos'))
                    aux = 'aux' in value
                    if aux:
                        args.pop(args.index('aux'))

                    source = args[0]
                    dest = ''
                    if len(args) == 2:
                        dest = args[1]
                    if not any([pos, aux]):
                        self.iPAP.setPmux(source=source, dest=dest)
                    else:
                        self.iPAP.setPmux(source=source, dest=dest, pos=pos,
                                          aux=aux, hard=hard)
        else:
            super(IcepapController, self).SetCtrlPar(parameter, value)

    def GetCtrlPar(self, parameter):
        param = parameter.lower()
        if param == 'pmux':
            value = '{0}'.format(self.iPAP.getPmux())
        else:
            value = super(IcepapController, self).GetCtrlPar(parameter)
        return value

    def __del__(self):
        if self.iPAP.connected:
            self.iPAP.disconnect()


#########################################################
# THIS TWO CLASSES ARE NEEDED BECAUSE IT IS NOT POSSIBLE
# TO ACCESS THE DEVICE FROM A DEVICE CALL
#########################################################
class FakedAttribute(object):
    def __init__(self, value):
        self.value = value


class FakedAttributeProxy(object):
    def __init__(self, controller, axis, attribute):
        self.ctrl = controller
        self.axis = axis
        self.attribute = attribute.replace('attr://', '')

    def read(self):
        value = self.ctrl.GetAxisExtraPar(self.axis, self.attribute)
        return FakedAttribute(value)
