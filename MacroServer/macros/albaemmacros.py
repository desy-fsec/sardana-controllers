
from macro import *
#import sys
#import pyIcePAP
#import time
import PyTango
#from pylab import *
#import array
from AlbaEmLib import albaem 

#ActivealbaemDev is the serial devices ('ws/bl01/serial0')
class albaemMacro():
    def getActivealbaemDev(self):
        try:
            dev = self.getEnv('ActivealbaemDev')
            print dev
            mydev = albaem(self.getEnv('ActivealbaemDev'))
        except Exception, e:
            self.output('albaemMacro.getActivealbaemDev caused an exception')
            print e
            mydev = None
        return mydev

        
class albaemSetRanges(Macro, albaemMacro):
    """Sets the ranges of the different channels of the instrument. Value is a string like \'1 1mA 2 10uA 3 100nA 4 100pA\'"""
    env = ('ActivealbaemDev',)
    
    param_def = [['value', Type.String, '', 'channel and ranges string']]

    def run(self, value):
        myalbaem = self.getActivealbaemDev()
	ranges = myalbaem.extractMultichannel('?RANGE %s'%value,1)
	myalbaem.Stop()
        myalbaem.setRanges(ranges)
        myalbaem.Start()
        self.output('Ranges set to:%s', myalbaem.getRanges(['1','2','3','4']))
        return

class albaemSetEnables(Macro, albaemMacro):
    """Enables the different channels of the instrument. Value is a string like \'1 YES 2 YES 3 NO 4 NO\'"""
    env = ('ActivealbaemDev',)
    
    param_def = [['value', Type.String, '', 'channel and enable string']]

    def run(self, value):
        myalbaem = self.getActivealbaemDev()
	ranges = myalbaem.extractMultichannel('?ENABLE %s'%value,1)
	myalbaem.Stop()
        myalbaem.setEnables(ranges)
        myalbaem.Start()
        self.output('Enables set to:%s', myalbaem.getEnables(['1','2','3','4']))

class albaemSetFilters(Macro, albaemMacro):
    """Sets the filters of the different channels of the instrument. Value is a string like \'1 1 2 10 3 100  4 3200\'"""
    env = ('ActivealbaemDev',)
    
    param_def = [['value', Type.String, '', 'channel and filters string']]

    def run(self, value):
        myalbaem = self.getActivealbaemDev()
	filters = myalbaem.extractMultichannel('?FILTER %s'%value, 1)
	myalbaem.Stop()
        myalbaem.setFilters(filters)
        myalbaem.Start()
        self.output('Filter set to:%s', myalbaem.getFilters(['1','2','3','4']))
        return

class albaemSetInvs(Macro, albaemMacro):
    """Inverts the analog output of the channels of the instrument. Value is a string like \'1 YES 2 NO 3 YES 4 NO\'"""
    env = ('ActivealbaemDev',)
    
    param_def = [['value', Type.String, '', 'channel and inversion string']]

    def run(self, value):
        myalbaem = self.getActivealbaemDev()
	invs = myalbaem.extractMultichannel('?INV %s'%value, 1)
	myalbaem.Stop()
        myalbaem.setInvs(invs)
        myalbaem.Start()
        self.output('Inversion set to:%s', myalbaem.getInvs(['1','2','3','4']))
        return
class albaemSetAvsamples(Macro, albaemMacro):
    """Set the number of averaged adc samples for every measurment. Value is between 1 and 1000."""
    env = ('ActivealbaemDev',)
    
    param_def = [['value', Type.String, '', 'Number of samples to average']]

    def run(self, value):
        myalbaem = self.getActivealbaemDev()
	myalbaem.Stop()
        myalbaem.setAvsamples(int(value))
        myalbaem.Start()
        self.output('Avsamples set to:%s', myalbaem.getAvsamples())


class albaemGetState(Macro, albaemMacro):
    """Reads the state of the acquisition."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('State:%s', myalbaem.getState())

class albaemGetSrate(Macro, albaemMacro):
    """Reads the sample rate of the adc acquisition."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Sample rate set to:%s', myalbaem.getSrate())


class albaemGetAvsamples(Macro, albaemMacro):
    """Reads the number of averaged samples for every readout."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Avsamples set to:%s', myalbaem.getAvsamples())

class albaemGetEnables(Macro, albaemMacro):
    """Reads whether the channels of the instrument are enabled or not."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Enables set to:%s', myalbaem.getEnables(['1','2','3','4']))

class albaemGetFilters(Macro, albaemMacro):
    """Reads the filters of the channels of the instrument."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Filters set to:%s', myalbaem.getFilters(['1','2','3','4']))
class albaemRangeUp(Macro, albaemMacro):
    """Increases the range of one channel"""
    env = ('ActivealbaemDev',)
    param_def = [['value', Type.String, '', 'Number of samples to average']]
    def run(self, value):
	channel = int(value)
        myalbaem = self.getActivealbaemDev()
	ranges = myalbaem.getRanges(['1', '2', '3', '4'])
	for couple in ranges:
		if couple[0] == '%s'%channel:
			if couple[1] == '1mA':
				nextrange = '1mA'
			if couple[1] == '100uA':
				nextrange = '1mA'
			if couple[1] == '10uA':
				nextrange = '100uA'
			if couple[1] == '1uA':
				nextrange = '10uA'
			if couple[1] == '100nA':
				nextrange = '1uA'
			if couple[1] == '10nA':
				nextrange = '100nA'
			if couple[1] == '1nA':
				nextrange = '10nA'
			if couple[1] == '100pA':
				nextrange = '1nA'
	myalbaem.Stop()
	myalbaem.setRanges([['%s'%channel, nextrange]])			
        self.output('Ranges set to:%s', myalbaem.getRanges(['1','2','3','4']))
	myalbaem.Start()
class albaemRangeDown(Macro, albaemMacro):
    """Increases the range of one channel"""
    env = ('ActivealbaemDev',)
    param_def = [['value', Type.String, '', 'Number of samples to average']]
    def run(self, value):
	channel = int(value)
        myalbaem = self.getActivealbaemDev()
	ranges = myalbaem.getRanges(['1', '2', '3', '4'])
	for couple in ranges:
		if couple[0] == '%s'%channel:
			if couple[1] == '1mA':
				nextrange = '100uA'
			if couple[1] == '100uA':
				nextrange = '10uA'
			if couple[1] == '10uA':
				nextrange = '1uA'
			if couple[1] == '1uA':
				nextrange = '100nA'
			if couple[1] == '100nA':
				nextrange = '10nA'
			if couple[1] == '10nA':
				nextrange = '1nA'
			if couple[1] == '1nA':
				nextrange = '100pA'
			if couple[1] == '100pA':
				nextrange = '100pA'
	myalbaem.Stop()
	myalbaem.setRanges([['%s'%channel, nextrange]])			
        self.output('Ranges set to:%s', myalbaem.getRanges(['1','2','3','4']))
	myalbaem.Start()

class albaemGetRanges(Macro, albaemMacro):
    """Reads the ranges of the channels of the instrument."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Ranges set to:%s', myalbaem.getRanges(['1','2','3','4']))

class albaemGetInfo(Macro, albaemMacro):
    """Reads the config of the channels of the instrument."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Ranges set to:%s', myalbaem.getRanges(['1','2','3','4']))
        self.output('Filters set to:%s', myalbaem.getFilters(['1','2','3','4']))
        self.output('Inversion set to:%s', myalbaem.getInvs(['1','2','3','4']))
        self.output('Offsets set to:%s', myalbaem.getOffsets(['1','2','3','4']))
        self.output('Enables set to:%s', myalbaem.getEnables(['1','2','3','4']))
        self.output('Avsamples set to:%s', myalbaem.getAvsamples())
        self.output('State is to:%s', myalbaem.getState())



class albaemGetMeasure(Macro, albaemMacro):
    """Reads a measurement of the channel specified of the instrument."""
    env = ('ActivealbaemDev',)
    param_def = [['channel', Type.String, '', 'Channel of the measurement']]
    def run(self, channel):
        myalbaem = self.getActivealbaemDev()
        self.output('Meas of channel %s :%s'%(channel, myalbaem.getMeasure([channel])))

class albaemGetMeasures(Macro, albaemMacro):
    """Reads a measurement of the channel specified of the instrument."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Meas of channel %s :%s'%(channel, myalbaem.getMeasure(['1', '2', '3', '4'])))


class albaemGetInvs(Macro, albaemMacro):
    """Reads the inversion of the analog output of the channels of the instrument."""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
        self.output('Inversion set to:%s', myalbaem.getInvs(['1','2','3','4']))

class albaemStop(Macro, albaemMacro):
    """Stops data conversion in the instrument. No new data will be available"""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
	myalbaem.Stop()
        self.output('State:%s', myalbaem.getState())
class albaemStart(Macro, albaemMacro):
    """Starts data conversion in the instrument. New data will be available"""
    env = ('ActivealbaemDev',)
    param_def = []
    def run(self):
        myalbaem = self.getActivealbaemDev()
	myalbaem.Start()
        self.output('State:%s', myalbaem.getState())
        
class albaemSendCmd(Macro, albaemMacro):
    """Starts data conversion in the instrument. New data will be available"""
    env = ('ActivealbaemDev',)
    param_def = [['value', Type.String, '', 'Command to send']]
    def run(self, value):
        myalbaem = self.getActivealbaemDev()
	ans = myalbaem.ask(value)
        self.output('SEND:%s\tRCVD:%s'%(value, ans))
        
        
        
if __name__ == "__main__":
    # TWO BASIC PARAMETERS, unit address and channel 
    if len(sys.argv) < 2:
        print "usage: python albaemmacros.py"
							        
