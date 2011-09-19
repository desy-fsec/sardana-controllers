import PyTango 
from macro import *

TIMEOUT_LIM = 1
    
def create_motor_info_dict(motor, direction):
    """Creates a dictionary with motor informations (which is required by homing functions).
    It has follwing keys('motor','direction','homed','status','position','home_ice_pos','encin').
    Motor and direction values are set with the funcion arguments
    
    :param motor: (motor obj) motor to be homed 
    :param direction: (int) homing direction - in pool sense <-1,1> 

    :return: (dictionary) dictionary with motor info"""

    return {'motor':motor, 
            'direction':direction,
            'homed':False,
            'status':None,
            'position':None,
            'home_ice_pos':None,
            'encin':None}

def populate_homing_commands(motors, directions, group=False, strict=False):
    """Populates a set of icepap homing commands: homing command, homing status command,
    homing position command, homing encoder command, abort command.
    
    :param motors: (list<motor obj>) list of motors to be homed 
    :param directions: (list<int>) list of homing directions - in pool sense <-1,1> 
    :param group: group homing
    :param strict: strict homing
    :return: (list<str>) list of homing commands"""

    homing_cmd = '#home'
    homing_status_cmd = '?homestat'
    homing_pos_cmd = '?homepos'
    homing_encin_cmd = '?homeenc encin'
    abort_cmd = '#abort'
    if group == True: homing_cmd += ' group'
    if strict == True: homing_cmd += ' strict'
    for m,d in zip(motors,directions):
        icepap_axis = m.getAxis()
        icepap_direction = m.getSign() * d
        homing_cmd += ' %d %d' % (icepap_axis, icepap_direction)
        homing_status_cmd += ' %s' % icepap_axis
        homing_pos_cmd += ' %s' % icepap_axis
        homing_encin_cmd += ' %s' % icepap_axis
        abort_cmd += ' %s' % icepap_axis
    return (homing_cmd, homing_status_cmd, homing_pos_cmd, homing_encin_cmd, abort_cmd)

def output_homing_status(macro, motorsInfoList):
    """Flushes homing status to the door output attribute.
    Status is represented in a table with homed state, home icepap position, home status, and motor positions as
    columns and motors as rows.
    
    :param macro: (macro obj) macro which will perform homing
    :param motorsInfoList: (list<dict>) list of motors info dictionary"""

    rowHead = []
    colHead = [['homed'], ['home icepap pos'], ['status'], ['position']]
    data = [[],[],[],[]]
    for motInfo in motorsInfoList:
        rowHead.append(motInfo['motor'].alias())
        data[0].append(str(motInfo['homed']))
        data[1].append(str(motInfo['home_ice_pos']))
        data[2].append(str(motInfo['status']))
        data[3].append(str(motInfo['position']))
        
    macro.output(colHead)
    macro.output(rowHead)
    macro.output(data)
    table = Table(data, elem_fmt=['%*s'], term_width=None,
                  col_head_str=colHead, col_head_fmt='%*s', col_head_width=15,
                  row_head_str=rowHead, row_head_fmt='%-*s', row_head_width=15, 
                  col_sep='|', row_sep='_', col_head_sep='-', border='=')
    macro.outputBlock(table.genOutput())
    macro.flushOutput()

def home(macro, motorsInfoList):
    """Performs icepap homing routine. 

    :param macro: (macro obj) macro which will perform homing
    :param motorsInfoList: (list<dict>) list of motors info dictionaries

    :return: (boolean) True if all motors finds home, False in all other cases"""
    someMotor = motorsInfoList[0]['motor'] 
    pool = someMotor.getPoolObj()
    ctrlName = someMotor.getControllerName()
    macro.debug('Pool: %s, Controller: %s' % (repr(pool), ctrlName))

    motors = [i.get('motor') for i in motorsInfoList]
    hmDirections = [i.get('direction') for i in motorsInfoList]
    HM_CMD, HM_STATUS_CMD, HM_POS_CMD, HM_ENCIN_CMD, ABORT_CMD = populate_homing_commands(motors, hmDirections, group=False, strict=False)
    macro.debug('HM_CMD: %s', HM_CMD)
    macro.debug('HM_STATUS_CMD: %s', HM_STATUS_CMD)
    macro.debug('HM_POS_CMD: %s', HM_POS_CMD)
    macro.debug('HM_ENCIN_CMD: %s', HM_ENCIN_CMD)

    ans = pool.SendToController([ctrlName , HM_CMD])
    if ans.startswith('HOME ERROR'):
        macro.error('Could not start icepap homing routine: %s', HM_CMD)
        macro.error('Icepap response: %s', ans)
        return False
    timeouts = 0
    try:
        while (True):
            macro.checkPoint()
            ans = pool.SendToController([ctrlName, HM_STATUS_CMD])
            homeStats = ans.split()[1::2]
            macro.debug('Home stats: %s' % repr(homeStats))
            #updating motor info dictionaries
            for i,motInfo in enumerate(motorsInfoList):
                motor = motInfo['motor']
                motInfo['position'] = motor.getAttribute('Position').getDisplayValue()
                macro.debug('Motor: %s, position: %s', motor.alias(), motInfo['position'])
                homingStatus = homeStats[i]
                motInfo['status'] = homingStatus
                if homingStatus == 'FOUND':
                    motInfo['homed'] = True
                    axis = motor.getAxis()
                    ans = pool.SendToController([ctrlName, '?homepos %d' % axis])
                    homeIcePos = ans.split()[1]
                    motInfo['home_ice_pos'] = homeIcePos
                    ans = pool.SendToController([ctrlName, '?homeenc encin %d' % axis])
                    encin = ans.split()[1]
                    motInfo['encin'] = encin
            #refreshing output table
            output_homing_status(macro, motorsInfoList)
            #checking ending condition
            if not any([stat == 'MOVING' for stat in homeStats]):
                if any([stat == 'NOTFOUND' for stat in homeStats]):
                    return False
                else:   
                    return True
            time.sleep(1)
            timeouts = 0
    except PyTango.DevFailed, e:
        timeouts += 1
        if timeouts > TIMEOUT_LIM:  
            pool.SendToController([ctrlName, ABORT_CMD])
            macro.abort()

def home_group(macro, motorsInfoList):
    """Performs icepap group homing routine. 

    :param macro: (macro obj) macro which will perform homing
    :param motorsInfoList: (list<dict>) list of motors info dictionaries

    :return: (boolean) True if all motors finds home, False in all other cases"""
    someMotor = motorsInfoList[0]['motor'] 
    pool = someMotor.getPoolObj()
    ctrlName = someMotor.getControllerName()
    macro.debug('Pool: %s, Controller: %s' % (repr(pool), ctrlName))

    motors = [i.get('motor') for i in motorsInfoList]
    hmDirections = [i.get('direction') for i in motorsInfoList]
    macro.debug('1')
    HM_CMD, HM_STATUS_CMD, HM_POS_CMD, HM_ENCIN_CMD, ABORT_CMD = populate_homing_commands(motors, hmDirections, group=True, strict=False)
    macro.debug('2')
    macro.debug('HM_CMD: %s', HM_CMD)
    macro.debug('HM_STATUS_CMD: %s', HM_STATUS_CMD)
    macro.debug('HM_POS_CMD: %s', HM_POS_CMD)
    macro.debug('HM_ENCIN_CMD: %s', HM_ENCIN_CMD)

    ans = pool.SendToController([ctrlName , HM_CMD])
    if ans.startswith('HOME ERROR'):
        macro.error('Could not start icepap homing routine: %s', HM_CMD)
        macro.error('Icepap response: %s', ans)
        return False
    timeouts = 0
    try:
        while (True):
            macro.checkPoint()
            ans = pool.SendToController([ctrlName, HM_STATUS_CMD])
            homeStats = ans.split()[1::2]
            macro.debug('Home stats: %s' % repr(homeStats))
            #updating motor info dictionaries
            for i,motInfo in enumerate(motorsInfoList):
                motor = motInfo['motor']
                motInfo['position'] = motor.getAttribute('Position').getDisplayValue()
                macro.debug('Motor: %s, position: %s', motor.alias(), motInfo['position'])
                homingStatus = homeStats[i]
                motInfo['status'] = homingStatus
                if homingStatus == 'FOUND':
                    motInfo['homed'] = True
                    axis = motor.getAxis()
                    ans = pool.SendToController([ctrlName, '?homepos %d' % axis])
                    homeIcePos = ans.split()[1]
                    motInfo['home_ice_pos'] = homeIcePos
                    ans = pool.SendToController([ctrlName, '?homeenc encin %d' % axis])
                    encin = ans.split()[1]
                    motInfo['encin'] = encin
            #refreshing output table
            output_homing_status(macro, motorsInfoList)
            #checking ending condition
            if not any([stat == 'MOVING' for stat in homeStats]):
                if any([stat == 'NOTFOUND' for stat in homeStats]):
                    return False
                else:   
                    return True
            time.sleep(1)
            timeouts = 0
    except PyTango.DevFailed, e:
        timeouts += 1
        if timeouts > TIMEOUT_LIM:  
            pool.SendToController([ctrlName, ABORT_CMD])
            macro.abort()

def home_strict(macro, motorsInfoList):
    """Performs icepap strict homing routine. 

    :param macro: (macro obj) macro which will perform homing
    :param motorsInfoList: (list<dict>) list of motors info dictionaries

    :return: (boolean) True when first motors finds home, False in all other cases"""

    someMotor = motorsInfoList[0]['motor'] 
    pool = someMotor.getPoolObj()
    ctrlName = someMotor.getControllerName()
    macro.debug('Pool: %s, Controller: %s' % (repr(pool), ctrlName))

    motors = [i.get('motor') for i in motorsInfoList]
    hmDirections = [i.get('direction') for i in motorsInfoList]
    HM_CMD, HM_STATUS_CMD, HM_POS_CMD, HM_ENCIN_CMD, ABORT_CMD = populate_homing_commands(motors, hmDirections, group=True, strict=True)
    macro.debug('HM_CMD: %s', HM_CMD)
    macro.debug('HM_STATUS_CMD: %s', HM_STATUS_CMD)
    macro.debug('HM_POS_CMD: %s', HM_POS_CMD)
    macro.debug('HM_ENCIN_CMD: %s', HM_ENCIN_CMD)

    ans = pool.SendToController([ctrlName , HM_CMD])
    if ans.startswith('HOME ERROR'):
        macro.error('Could not start icepap homing routine: %s', HM_CMD)
        macro.error('Icepap response: %s', ans)
        return False
    timeouts = 0
    try:
        while (True):
            macro.checkPoint()
            ans = pool.SendToController([ctrlName, HM_STATUS_CMD])
            homeStats = ans.split()[1::2]
            macro.debug('Home stats: %s' % repr(homeStats))
            #updating motor info dictionaries
            for i,motInfo in enumerate(motorsInfoList):
                motor = motInfo['motor']
                motInfo['position'] = motor.getAttribute('Position').getDisplayValue()
                macro.debug('Motor: %s, position: %s', motor.alias(), motInfo['position'])
                homingStatus = homeStats[i]
                motInfo['status'] = homingStatus
                if homingStatus == 'FOUND':
                    motInfo['homed'] = True
                    axis = motor.getAxis()
                    ans = pool.SendToController([ctrlName, '?homepos %d' % axis])
                    homeIcePos = ans.split()[1]
                    motInfo['home_ice_pos'] = homeIcePos
                    ans = pool.SendToController([ctrlName, '?homeenc encin %d' % axis])
                    encin = ans.split()[1]
                    motInfo['encin'] = encin
            #refreshing output table
            output_homing_status(macro, motorsInfoList)
            #checking ending condition
            if not any([stat == 'MOVING' for stat in homeStats]):
                if any([stat == 'FOUND' for stat in homeStats]):
                    return True
                else:   
                    return False
            time.sleep(1)
            timeouts = 0
    except PyTango.DevFailed, e:
        timeouts += 1
        if timeouts > TIMEOUT_LIM:  
            pool.SendToController([ctrlName, ABORT_CMD])
            macro.abort()

def home_group_strict(macro, motorsInfoList):
    """Performs icepap strict homing routine. 

    :param macro: (macro obj) macro which will perform homing
    :param motorsInfoList: (list<dict>) list of motors info dictionaries

    :return: (boolean) True when first motors finds home, False in all other cases"""

    someMotor = motorsInfoList[0]['motor'] 
    pool = someMotor.getPoolObj()
    ctrlName = someMotor.getControllerName()
    macro.debug('Pool: %s, Controller: %s' % (repr(pool), ctrlName))

    motors = [i.get('motor') for i in motorsInfoList]
    hmDirections = [i.get('direction') for i in motorsInfoList]
    HM_CMD, HM_STATUS_CMD, HM_POS_CMD, HM_ENCIN_CMD, ABORT_CMD = populate_homing_commands(motors, hmDirections, group=True, strict=True)
    macro.debug('HM_CMD: %s', HM_CMD)
    macro.debug('HM_STATUS_CMD: %s', HM_STATUS_CMD)
    macro.debug('HM_POS_CMD: %s', HM_POS_CMD)
    macro.debug('HM_ENCIN_CMD: %s', HM_ENCIN_CMD)

    ans = pool.SendToController([ctrlName , HM_CMD])
    if ans.startswith('HOME ERROR'):
        macro.error('Could not start icepap homing routine: %s', HM_CMD)
        macro.error('Icepap response: %s', ans)
        return False
    timeouts = 0
    try:
        while (True):
            macro.checkPoint()
            ans = pool.SendToController([ctrlName, HM_STATUS_CMD])
            homeStats = ans.split()[1::2]
            macro.debug('Home stats: %s' % repr(homeStats))
            #updating motor info dictionaries
            for i,motInfo in enumerate(motorsInfoList):
                motor = motInfo['motor']
                motInfo['position'] = motor.getAttribute('Position').getDisplayValue()
                macro.debug('Motor: %s, position: %s', motor.alias(), motInfo['position'])
                homingStatus = homeStats[i]
                motInfo['status'] = homingStatus
                if homingStatus == 'FOUND':
                    motInfo['homed'] = True
                    axis = motor.getAxis()
                    ans = pool.SendToController([ctrlName, '?homepos %d' % axis])
                    homeIcePos = ans.split()[1]
                    motInfo['home_ice_pos'] = homeIcePos
                    ans = pool.SendToController([ctrlName, '?homeenc encin %d' % axis])
                    encin = ans.split()[1]
                    motInfo['encin'] = encin
            #refreshing output table
            output_homing_status(macro, motorsInfoList)
            #checking ending condition
            if not any([stat == 'MOVING' for stat in homeStats]):
                if any([stat == 'FOUND' for stat in homeStats]):
                    return True
                else:   
                    return False
            time.sleep(1)
            timeouts = 0

    except PyTango.DevFailed, e:
        timeouts += 1
        if timeouts > TIMEOUT_LIM:  
            pool.SendToController([ctrlName, ABORT_CMD])
            macro.abort()