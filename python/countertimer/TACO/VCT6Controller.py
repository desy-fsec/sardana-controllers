##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################

import time
from sardana import State
from sardana.pool.controller import CounterTimerController

from TacoDevice import *
from array import array
#from numpy import *
from ctypes import *


class Channel:
    
    def __init__(self,ind,taco):
        self.is_counting = False
        self.channel = TacoDevice(taco[ind+1])
        self.cardName = taco[0]
        self.ctrlChannel = ind
        if ind == 0:
            self.cardChannel = 1
            self.master = 0
            self.masterChn = 1
            self.intClock = 0
            self.frec = 1
            self.countinousRun = 0
            self.externalStart = 0
            self.externalStop = 0
        else:
            self.cardChannel = ind+1
            self.master = 1
            self.masterChn = 1
            self.intClock = 1
            self.frec = 0
            self.countinousRun = 0
            self.externalStart = 0
            self.externalStop = 0
        #_prop = [self.master, self.masterChn, self.intClock, self.frec, self.countinousRun, self.externalStart, self.externalStop]
        #_array =  array('h', _prop)
        ##_array =  array( _prop, int8)
        #self.prop = _array.tolist()
        self.prop = [self.master, self.masterChn, self.intClock, self.frec, self.countinousRun, self.externalStart, self.externalStop]
        #self.prop = [self.master, self.masterChn, self.intClock, self.frec, self.countinousRun, self.externalStart, self.externalStop]

       
class VCT6Controller(CounterTimerController):
    "This class is the Tango Sardana CounterTimer controller for VCT6 card using TacoDevice"

    gender = "Simulation"
    model  = "Basic"
    organization = "CELLS - ALBA"
    image = "dummy_ct_ctrl.png"
    logo = "ALBA_logo.png"


    ctrl_properties = { 'tacodevice' : { 'Type' : 'DevString', 'Description' : 'Taco device ("id00/vct6card_lid00a/00")' } }
    MaxDevice = 6
    FrecClock = {"100KHz": 0,
                 "1MHz": 1,
                 "8MHz": 2,
                 "16MHz": 3}

    ExpFrecValue = {0: 100000,
                    1: 1000000,
                    2: 8000000,
                    3: 16000000}

    YesNo = {'Yes': 1,
             'No': 0}

    axis_attributes = \
        { 'Card': { 'Type' : str,
                         'Description' : 'Card name'},
          'CardChannel': { 'Type' :  int,
                         'Description' : 'Card channel'},
          'CtrlChannel': { 'Type' : int,
                         'Description' : 'Ctrl channel'},
          'Master': { 'Type' : int,
                         'Description' : '0/1 master/slave',
                         'DefaultValue' : 1},
          'MasterChn': { 'Type' : int,
                         'Description' : '0-7 where 1-6 mean the master is in the same board and 0 or 7 it is gated by the external input INH',
                         'DefaultValue' : 1},
          'IntClock': { 'Type' : int,
                         'Description' : '0/1 internal/external',
                         'DefaultValue' : 1},
          'Frec': { 'Type' : str,
                         'Description' : '1KHz, 1MHz, 8MHz or 16MHz',
                         'DefaultValue' : "1KHz"},
          'CountinousRun': { 'Type' : int,
                         'Description' : '1/0 yes/no',
                         'DefaultValue' : 0},
          'ExternalStart': { 'Type' : int,
                         'Description' : '1/0 yes/no',
                         'DefaultValue' : 0},
          'ExternalStop': { 'Type' : int,
                         'Description' : '1/0 yes/no',
                         'DefaultValue' : 0},
          'Properties' : { 'Type' :   (int,), 
                         'Description' : 'Properties'}
            }       
#    StoppedMode = 0
#    TimerMode = 1
#    MonitorMode = 2
#    CounterMode = 3

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.channels = self.MaxDevice*[None,]

        self.dev = TacoDevice(self.tacodevice)
        self.taco = self.dev.GetDevList("")
        self._master = 0
        self.reset()
        
    def reset(self):
        self.start_time = None
        self.integ_time = None
        self.monitor_count = None
        self.read_channels = {}
        self.counting_channels = {}
        
    def AddDevice(self,ind):      
        self.channels[ind] = Channel(ind, self.taco)
        
    def DeleteDevice(self,ind):
        self.channels[ind] = None

    def PreStateAll(self):
        pass
    
    def PreStateOne(self, ind):
        pass
    
    def StateAll(self):
        pass
    
    def StateOne(self, ind):     
        sta = State.On
        status = "Stopped"
        if ind in self.counting_channels:
            now = time.time()
            elapsed_time = now - self.start_time
            self._updateChannelState(ind, elapsed_time)

            specsta = self.channels[ind].channel.DevState()
            specstatus = self.channels[ind].channel.DevStatus()
            if (specsta==42):
                sta = State.Moving
                status = "Acquiring"
            elif (specsta==2):
                sta = State.On
                status = "Stopped"
            elif (specsta==11):
                sta = State.Alarm
                status = "Not completely initialized"
            elif (specsta==23):
                sta = State.Alarm
                status = "Badly initialized"

        return sta, status
        
    def _updateChannelState(self, ind, elapsed_time):
        channel = self.channels[ind]
        if self.integ_time is not None:
            # counting in time
            if elapsed_time >= self.integ_time:
                self._finish(elapsed_time)
        elif self.monitor_count is not None:
            # monitor counts
            v = int(elapsed_time*100*ind)
            if v >= self.monitor_count:
                self._finish(elapsed_time)
    
    def _finish(self, elapsed_time, ind=None):
        if ind is None:
            for ind, channel in self.counting_channels.items():
                channel.is_counting = False
        else:
            if ind in self.counting_channels:
                channel = self.counting_channels[ind]
                channel.is_counting = False
            else:
                channel = self.channels[ind-1]
                channel.is_counting = False
        self.counting_channels = {}
                
    def PreReadAll(self):
        pass
    
    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        self.channels[self._master].channel.DevCntReadAll()
    
    def ReadOne(self, ind):
        v = self.channels[ind].channel.DevCntRead()
        return v
    
    def PreStartAll(self):
        self.counting_channels = {}
    
    def PreStartOne(self, ind, value=None):
        channel = self.channels[ind]
        self.counting_channels[ind] = channel
        return True
    
    def StartOne(self, ind, value=None):
        self.counting_channels[ind].is_counting = True
        if self.channels[ind].channel is None:
            return
#        if ind == 0:
#            self.channels[ind].channel.DevCntInit(0,1,0,1,0,0,0)
#        else:
#            self.channels[ind].channel.DevCntInit(1,1,1,0,0,0,0)
        #a = self._UpdateProp(ind)
#        self.channels[ind].channel.DevCntInit(a)
        self.channels[ind].channel.DevCntInit(self.channels[ind].prop)

        self.channels[ind].channel.DevCntStart()
    
    def StartAll(self):
        self.start_time = time.time()
    
    def LoadOne(self, ind, value):
        if value > 0:
            self.integ_time = value
            self.monitor_count = None
        else:
            self.integ_time = None
            self.monitor_count = -value

        self._master = ind
        time = self.ExpFrecValue[self.channels[ind].frec]*value
        self.channels[ind].channel.DevCntPresetValue(int(time))
    
    def AbortOne(self, ind):
        self.channels[ind].channel.DevCntStop()   
# --------------------------------------------------------------------------
# SetAxisExtraPar/GetAxisExtraPar() 
# -------------------------------------------------------------------------- 

    def _UpdateProp(self,ind):

        chn = self.channels[ind]
        #chn.prop = [chn.master, chn.masterChn, chn.intClock, chn.frec, chn.countinousRun, chn.externalStart, chn.externalStop]
        chn.prop = [chn.master, chn.masterChn, chn.intClock, chn.frec, chn.countinousRun, chn.externalStart, chn.externalStop]
        #_prop = [chn.master, chn.masterChn, chn.intClock, chn.frec, chn.countinousRun, chn.externalStart, chn.externalStop]
        #_array =  array('h', _prop)
 
        ##_array = array([chn.master, chn.masterChn, chn.intClock, chn.frec, chn.countinousRun, chn.externalStart, chn.externalStop], int8 ) 
        #chn.prop = _array.tolist()
        ##return _array
        #return _array.tolist()

    def _SetProp(self,ind, value):
        chn = self.channels[ind]
        chn.master = value[0] 
        chn.masterChn = value[1]
        chn.intClock = value[2]
        chn.frec = value[3]
        chn.countinousRun = value[4]
        chn.externalStart = value[5]
        chn.externalStop = value[6]
   
    def SetAxisExtraPar(self,ind,name,value):
        c = self.channels[ind]
#        if name == 'Channel':
#           self.channels[ind].channel = TacoDevice(self.taco[value])
        if name == 'Properties':
            self._SetProp(ind, value)
        if name == 'MasterChn':
            c.masterChn = value
        if name == 'IntClock':
            c.intClock = value
        if name == 'Frec':
            self.defaultfrec = False
            c.frec = self.FrecClock[value]
        if name == 'CountinousRun':
            c.countinousRun = value
        if name == 'ExternalStart':
            c.externalStart = value
        if name == 'ExternalStop':
            #c.externalStop = self.YesNo[value]
            c.externalStop = value
        if name == 'Master':
            c.master = value
        self._UpdateProp(ind)

    def GetAxisExtraPar(self, ind, name):
        if name == 'Card':
            return self.channels[ind].cardName
        if name == 'CardChannel':
            return self.channels[ind].cardChannel
        if name == 'CtrlChannel':
            return self.channels[ind].ctrlChannel
        if name == 'Master':
            return self.channels[ind].master
        if name == 'MasterChn':
            return self.channels[ind].masterChn
        if name == 'IntClock':
            return self.channels[ind].intClock
        if name == 'Frec':
            if self.channels[ind].frec == 0:
                return "100KHz"
            elif self.channels[ind].frec == 1:
                return "1MHz"
            elif self.channels[ind].frec == 2:
                return "8MHz"
            else:
                return "16MHz"   
        if name == 'CountinousRun':
            return self.channels[ind].countinousRun
        if name == 'ExternalStart':
            return self.channels[ind].externalStart
        if name == 'ExternalStop':
            #if self.channels[ind].externalStop == 0:
            #    return 'No'
            #else:
            #    return 'Yes'
            return self.channels[ind].externalStop
        if name == 'Properties':
            return self.channels[ind].prop         
