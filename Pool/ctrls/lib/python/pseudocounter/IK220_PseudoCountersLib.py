from pool import PseudoCounterController, PoolUtil
import time
import array

class IK220_channels(PseudoCounterController):
    """ A pseudo counter ctrl with all IK220 channels."""

    class_prop = {'ik220_devname':{'Description':'The IK220 Tango Device.',
                               'Type' : 'PyTango.DevString'}
                  }
                                                              
    counter_roles = ()
    pseudo_counter_roles = ('chan1', 'chan2', 'chan3', 'chan4','chan5', 'chan6', 'chan7', 'chan8', 'mean1', 'mean2')

    def __init__(self, inst, props):
        PseudoCounterController.__init__(self, inst, props)
        util = PoolUtil()
        self.ik220_dev = util.get_device(self.inst_name,self.ik220_devname)


    def calc(self,index, counter_values):
        """ Return the corresponding value for the given index. """
        try:
            angles = self.ik220_dev.read_attribute('Angles').value
            if index == 9:
                return sum(angles[:4])/4
            elif index == 10:
                return sum(angles[4:8])/4
            else:
                return angles[index - 1]
        except:
            return 1e-100
                    

class ND287_channels(PseudoCounterController):
    """ A pseudo counter ctrl with all ND287 channels. """

    
    class_prop = {'serial_devname':{'Description':'The PySerial Tango Device.',
                               'Type' : 'PyTango.DevString'}
                  }
                                                              
    counter_roles = ()
    pseudo_counter_roles = ('chan1', 'chan2', 'mean')
    
    def __init__(self, inst, props):
        PseudoCounterController.__init__(self, inst, props)
        util = PoolUtil()
        self.serial_dev = util.get_device(self.inst_name,self.serial_devname)
        try:
            self.serial_dev.open()
        except:
            pass
    
    def calc(self, index, counter_values):
        try:
            commands = ['A0100','T0107','A0100','T0107','T0107','T0107','T0107']
            sequence = '\x1b'+'\r\x1b'.join(commands)+'\r'
            cmd_list = array.array('B',sequence).tolist()
            self.serial_dev.write(cmd_list)
            time.sleep(0.5)
            ans_list = self.serial_dev.readline()
            values = array.array('B',ans_list).tostring()
            values = values.replace('\x00','')
            values = values.replace('\x02','')
            values = values.replace('\x06','')
            
            splitted = values.split('\r\n')
            chans = [float(splitted[0]), float(splitted[1]) ]
            
            if index == 3 :
                return sum(chans)/2
            else:
                return chans[index - 1]
        except Exception,e:
            print "Some exception found while getting values from nd287",e
            return 1e-100           

