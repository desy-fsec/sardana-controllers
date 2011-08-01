from pool import PseudoCounterController
from pool import PoolUtil

class MOPIFilterThicknessPCCtrl(PseudoCounterController):
    """ The MOPI Filter Thickness Pseudo Counter Controller.""" 


    class_prop = {'mopi_lon_dev':{'Description':'The mopi lon motor used for the operations.'
                                   ,'Type' : 'PyTango.DevString'},
                  'mopi_filt_dev':{'Description':'The mopi filt motor used for the operations.'
                                      ,'Type' : 'PyTango.DevString'}
                  }
    
    pseudo_counter_roles = ('mopi_filter_thickness',)

    gender = 'PseudoCounter'
    model  = ''
    image = ''
    icon = ''
    organization = 'CELLS - ALBA'
    logo = 'ALBA_logo.png'

    def __init__(self, inst, props):
        PseudoCounterController.__init__(self, inst, props)
        self.mopi_lon_motor = None
        self.mopi_filt_motor = None

    def calc(self, index, counter_values):
        if self.mopi_lon_motor == None or self.mopi_filt_motor == None:
            util = PoolUtil()
            try:
                self.mopi_lon_motor = util.get_device(self.inst_name, self.mopi_lon_dev)
                self.mopi_filt_motor = util.get_device(self.inst_name, self.mopi_filt_dev)
            except Exception,e:
                self._log.error('Could not connect to devices %s and %s' %(self.mopi_lon_dev, self.mopi_filt_dev))

        mopi_lon = self.mopi_lon_motor.read_attribute('Position').value
        mopi_filt = self.mopi_filt_motor.read_attribute('Position').value

        # IF CHAIN FROM RT TICKET: RT#17856
        # https://rt.cells.es/Ticket/Display.html?id=17856
        x = mopi_lon - mopi_filt + 56.5

        if x > 100:
            thickness = 0
        elif x > 90:
            thickness = 5
        elif x > 0:
            thickness = 0.1 + 0.0544 * x
        else:
            thickness = 0

        return thickness
