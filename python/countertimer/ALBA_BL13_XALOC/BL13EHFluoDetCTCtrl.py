import PyTango
from sardana import pool
from sardana import State
from sardana.pool.controller import CounterTimerController

import numpy
from xflasfluodet import XFlashFluoDetComm

class BL13EHFluoDetCTController(CounterTimerController):
    
    # Four devices: timer, fluocts, scatteringcts, totalcts, deadtime
    MaxDevice = 5

    axis_attributes ={'Spectrum': 
                      {'Type':(float,),
                       'Description':'Fluorescence spectrum',
                       'R/W Type':'read_write'},
                      'SpectrumXScale': 
                      {'Type':(float,),
                       'Description':'Fluorescence spectrum X axis scale',
                       'R/W Type':'read_write'},
                      'FluoRoiCenter':
                      {'Type':float,
                       'Description':'Center of Fluorescence ROI',
                       'R/W Type':'read_write'},
                      'EdgeRoiCenter':
                      {'Type':float,
                       'Description':'Center of Scattering edge ROI',
                       'R/W Type':'read_write'},
                      'binning':
                      {'Type':int,
                       'Description':'Spectrum binning (read time: 1:4.69sec 2:2.57sec 4:1.49sec)',
                       'R/W Type':'read_write'},
                      }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self,inst,props, *args, **kwargs)
        self.fluodet = XFlashFluoDetComm()
        self.spectrum = None
        self.spectrum_xscale = None
        self.running = False
        self.binning = 4
        self.fluoroi_center = 0
        self.edgeroi_center = 0
        
    def AddDevice(self, axis):  
        pass
        
    def DeleteDevice(self, axis):
        pass
        
    def PreStateOne(self, axis):
        pass
    
    def StateAll(self):
        pass
    
    def StateOne(self, axis):
        if self.fluodet.getAcqState() == 'RUNNING':
            return State.Running, 'Device is Running.'
        self.running = False
        return State.On, 'Device is ON.'

    def PreReadAll(self): 
        pass

    def PreReadOne(self, axis):
        pass
        
    def ReadAll(self):
        pass

    def ReadOne(self, axis):
        if axis == 1:
            # return self.fluodet.getRunningTime()
            # sometimes it returns <no data> so we just skip this communication
            return self.acq_time
        elif axis == 2:
            return self.fluodet.getEnergyCounts(self.fluoroi_center)
        elif axis == 3:
            return self.fluodet.getEnergyCounts(self.edgeroi_center)
        elif axis == 4:
            return self.fluodet.getTotalCounts()
        elif axis == 5:
            return self.fluodet.getDeadTime()

    def PreStartAllCT(self):
        pass
        
    def PreStartOneCT(self, axis):
        return True

    def StartOneCT(self, axis):
        pass

    def StartAllCT(self):
        # Should start acquisition
        self.spectrum = None
        self.spectrum_xscale = None
        self.running = True
        self.fluodet.start(self.acq_time)

    def LoadOne(self, axis, value):
        self.acq_time = value

    def AbortOne(self, axis):
        self.abort()

    def GetAxisExtraPar(self, axis, name):
        name_lower = name.lower()
        if name_lower == "spectrum":
            if self.spectrum == None and self.running == False:
                self.spectrum = self.fluodet.getFluoSpectrum_synch(binning=self.binning)
            return self.spectrum
        elif name_lower == "spectrumxscale":
            if self.spectrum == None and self.running == False:
                self.spectrum_xscale = self.fluodet.getSpectrumScale(binning=self.binning)
            else:
                self.spectrum_xscale = self.fluodet.getSpectrumScale(binning=self.binning)
            return self.spectrum_xscale
        elif name_lower == 'fluoroicenter':
            return self.fluoroi_center
        elif name_lower == 'edgeroicenter':
            return self.edgeroi_center
        elif name_lower == 'binning':
            return self.binning

    def SetAxisExtraPar(self,axis, name, value):
        name_lower = name.lower()
        if name_lower == 'fluoroicenter':
            self.fluoroi_center = value
        elif name_lower == 'edgeroicenter':
            self.edgeroi_center = value
        elif name_lower == 'binning':
            self.binning = value
