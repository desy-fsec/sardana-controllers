from pool import PseudoCounterController
from pool import PoolUtil

class LI_BCM_PCCtrl(PseudoCounterController):
    """ The LINAC Beam Charge Monitor Pseudo Counter Controller.""" 


    class_prop = {'gap_motor_dev':{'Description':'The gap motor used for the operations.'
                                   ,'Type' : 'PyTango.DevString'},
                  'offset_motor_dev':{'Description':'The offset motor used for the operations.'
                                      ,'Type' : 'PyTango.DevString'},
                  'ibend_motor_dev':{'Description':'The bending current motor used for the operations.'
                                     ,'Type' : 'PyTango.DevString'}
                  }
    # THEY USED TO BE:
    #           gap: pm/lt02_hslit/1
    #           offset: pm/lt02_hslit/2
    #           ibend: motor/lt01_pc_bend1/1
    
    counter_roles = ('bcm1', 'bcm2')
    pseudo_counter_roles = ('cr', 'crgap', 'e', 'egap', 'gap', 'offset', 'ibend', 'crnorm')


    gender = 'PseudoCounter'
    model  = 'BCM_PC'
    image = ''
    icon = ''
    organization = 'CELLS - ALBA'
    logo = 'ALBA_logo.png'

    def __init__(self, inst, props):
        PseudoCounterController.__init__(self, inst, props)
        util = PoolUtil()
        try:
            self.gap_motor = util.get_device(self.inst_name, self.gap_motor_dev)
            self.offset_motor = util.get_device(self.inst_name, self.offset_motor_dev)
            self.ibend_motor = util.get_device(self.inst_name, self.ibend_motor_dev)
        except Exception,e:
            self._log.error('Could not connect to devices %s, %s and %s' %(self.gap_motor_dev,self.offset_motor_dev,self.ibend_motor_dev))

    def calc(self,index,counter_values):
        bcm1 = counter_values[0]
        bcm2 = counter_values[1]
        if index == 1:
            return  self.cr(bcm1, bcm2)
        elif index == 2:
            return self.crgap(bcm1, bcm2)
        elif index == 3:
            return self.e()
        elif index == 4:
            return self.egap()
        elif index == 5:
            return self.gap()
        elif index == 6:
            return self.offset()
        elif index == 7:
            return self.ibend()
        elif index == 8:
            return self.crnorm(bcm1, bcm2)
        
        return None

    def cr(self, bcm1, bcm2):
        return bcm2 / bcm1

    def crgap(self, bcm1, bcm2):
        cr = self.cr(bcm1, bcm2)
        gap = self.gap()
        return cr / gap

    def e(self):
        # E = (ibend() * 0.688901) + 0.235063;
        # New version:
        # E = ((0.705787 * ibend) + 0.244807) * (1 + (offset / 1013))
        ibend = self.ibend()
        offset = self.offset()
        return ((0.705787 * ibend) + 0.244807) * (1 + (offset / 1013))

    def egap(self):
        e = self.e()
        gap = self.gap()
        return e / gap

    def gap(self):
        return self.gap_motor.read_attribute('Position').value
    
    def offset(self):
        return self.offset_motor.read_attribute('Position').value
    
    def ibend(self):
        return self.ibend_motor.read_attribute('Position').value
    
    def crnorm(self, bcm1, bcm2):
        # crnorm = cr / ((gap / 1013) * E)
        cr = self.cr(bcm1, bcm2)
        gap = self.gap()
        e = self.e()
        return cr / ((gap / 1013) * e)
    
