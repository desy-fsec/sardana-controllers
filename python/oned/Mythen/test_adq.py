#!/usr/bin/env python

from MythenLib import Mythen, UDP_PORT, TCP_PORT

import time

MYTHEN_IP_OFF = 'bl22mythen-office'
MYTHEN_IP_BL = 'bl22mythen'


if __name__ == '__main__':
    mythen = Mythen(MYTHEN_IP_OFF,UDP_PORT)
    count = 0
    mythen.setTime(2)
    mythen.startAcquisition()
    t1 = time.time()
    while mythen.getStatus() == 'RUNNING':
        time.sleep(0.1)
        count +=1
    print time.time()-t1
    print count

    print mythen.getReadOut()
    print mythen.getStatus()
    
    
