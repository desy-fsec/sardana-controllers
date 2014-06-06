#!/usr/bin/env python

from MythenLib import Mythen, UDP_PORT, TCP_PORT

import time

MYTHEN_IP_OFF = 'bl22mythen-office'
MYTHEN_IP_BL = 'bl22mythen'


if __name__ == '__main__':
    mythen = Mythen(MYTHEN_IP_OFF,UDP_PORT)
    
    print mythen.getVersion()
    print mythen.getTau()
    print mythen.getSettingsMode()
    print mythen.getReadOut()
    print mythen.getStatus()
    print mythen.getBadChannelInterpolation()
    print mythen.getBadChannels()
    print mythen.getFlatField()
    print mythen.getFlatFieldCorrection()
    print mythen.getBitsReadOut()
    print mythen.getActiveModules()
    print mythen.getRateCorrection()
    print mythen.getSettings()
    print mythen.getTime()
    print mythen.getThreshold()
   
#     mythen.setTime(2)
#     print  mythen.getTime()
#     mythen.startAcquisition()
#     print mythen.getReadOut()
#     print mythen.getStatus()
    
    
