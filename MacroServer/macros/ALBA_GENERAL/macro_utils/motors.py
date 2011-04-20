import PyTango

def moveToPosHardLim(macro, motors_pos_dict):
    try:
        motors = motors_pos_dict.keys()
        positions = motors_pos_dict.values()
        #Checking positive limits state (maybe they were already active)
        motorsOnPosLim = []
        for m in motors:
            if m.Limit_switches[1]:
                macro.debug('Motor %s is already at the positive limit.', m.alias())
                motorsOnPosLim.append(m)
        if len(motorsOnPosLim): return motorsOnPosLim
        macro.debug('Moving motors: %s towards positive limit...', 
                   repr([m.alias() for m in motors_pos_dict.keys()]))
        for m,p in zip(motors,positions):
            macro.debug('Moving motor %s to position: %f).', m.alias(), p)
        motion = macro.getMotion(motors)
        motion.move(positions)
        macro.checkPoint()
        #Checking stop code (if we reached positive limits)
        motorsWhichReachedPosLim = []
        for m in motors:
            if m.StatusStopCode == 'Limit+ reached':
                macro.debug('Motor %s reached its positive limit.', m.alias())
                motorsWhichReachedPosLim.append(m)
        return motorsWhichReachedPosLim
    except PyTango.DevFailed, e: 
        macro.error(repr(e))
        macro.error('Moving motors: %s to positive limits was interupted.', repr(motors))
        raise e
        
def moveToNegHardLim(macro, motors_pos_dict):
    try:
        motors = motors_pos_dict.keys()
        positions = motors_pos_dict.values()
        #Checking negative limits state (maybe they were already active)
        motorsOnNegLim = []
        for m in motors:
            #macro.output(type(m.getAttribute('StatusLim-')))
            if m.Limit_Switches[2]:
                macro.debug('Motor %s is already at the negative limit.', m.alias())
                motorsOnNegLim.append(m)
        if len(motorsOnNegLim): return motorsOnNegLim
        macro.debug('Moving motors: %s towards negative limit...', 
                   repr([m.alias() for m in motors_pos_dict.keys()]))
        for m,p in zip(motors,positions):
            macro.debug('Moving motor %s to position: %f).', m.alias(), p)
        motion = macro.getMotion(motors)
        motion.move(positions)
        macro.checkPoint()
        #Checking stop code (if we reached negative limits)
        motorsWhichReachedNegLim = []
        for m in motors:
            if m.StatusStopCode == 'Limit- reached':
                macro.debug('Motor %s reached its negative limit.', m.alias())
                motorsWhichReachedNegLim.append(m)
        return motorsWhichReachedNegLim
    except PyTango.DevFailed, e: 
        macro.error(repr(e))
        macro.error('Moving motors: %s to negative limits was interupted.', repr(motors))
        raise e  