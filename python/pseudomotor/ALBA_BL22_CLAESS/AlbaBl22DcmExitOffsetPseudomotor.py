import math
import PyTango
from sardana.pool.controller import PseudoMotorController, Description, Type, \
    DefaultValue, Access, DataAccess


class DCM_ExitOffset_Controller(PseudoMotorController):
    """This pseudomotor controller does the calculation of Bragg
    and 2nd Xtal perpendicular position according to desired energy in eV.
    It works only with ClaesDcmTurboPmacCtrl motors"""

    pseudo_motor_roles = ('exitOffset',)
    motor_roles = ('perp',)

    class_prop = {
        'PmacDevice': {Type: str,
                       Description: 'Pmac device name'}
        }

    axis_attributes = {'BraggOffset': {Type: float,
                                       Description: 'User bragg offset',
                                       Access: DataAccess.ReadWrite},
                       'BraggStepPerUnit': {Type: float,
                                            Description: 'Bragg step per '
                                                         'units',
                                            Access: DataAccess.ReadWrite,
                                            DefaultValue: 200000
                                            }
                       }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        try:
            self.pmac_eth = PyTango.DeviceProxy(self.PmacDevice)
        except Exception as e:
            self._log.error("Couldn't create DeviceProxy for %s "
                            "motor." % self.PmacDevice)
            raise e
        self._bragg_spu = 200000
        self._bragg_offset = 0.075

    def calc_physical(self, index, pseudos):
        self._log.debug("Entering calc_physical")
        ret = self.calc_all_physical(pseudos)[index - 1]
        self._log.debug("Leaving calc_physical")
        return ret

    def calc_pseudo(self, index, physicals):
        self._log.debug("Entering calc_pseudo")
        ret = self.calc_all_pseudo(physicals)[index - 1]
        self._log.debug("Leaving calc_pseudo")
        return ret

    def calc_all_physical(self, pseudos):
        self._log.debug("Entering calc_all_physical")
        exitOffset, = pseudos
        bragg_deg = self._get_bragg_pos()
        bragg_rad = math.radians(bragg_deg)
        perp = exitOffset / 2 / math.cos(bragg_rad)
        self._log.debug("Leaving calc_all_physical")
        return (perp,)

    def calc_all_pseudo(self, physicals):
        self._log.debug("Entering calc_all_pseudo")
        perp_mm, = physicals
        bragg_deg = self._get_bragg_pos()
        bragg_rad = math.radians(bragg_deg)
        exitOffset = 2 * perp_mm * math.cos(bragg_rad)
        self._log.debug("Leaving calc_all_pseudo")
        return (exitOffset,)

    def _get_bragg_pos(self):
        try:
            mot_pos_ans = self.pmac_eth.command_inout("SendCtrlChar", "P")
        except PyTango.DevFailed as e:
            self._log.error("_get_bragg_pos: SendCtrlChar('P') command called "
                            "on PmacEth DeviceProxy failed. \nException: %s",
                            e)
            raise
        mot_pos_float_array = [float(s) for s in mot_pos_ans.split()]
        bragg_pos_step = mot_pos_float_array[0]  # bragg is the first motor
        bragg_pos = bragg_pos_step / self._bragg_spu + self._bragg_offset
        return bragg_pos

    def getBraggOffset(self, axis):
        return self._bragg_offset

    def setBraggOffset(self, axis, value):

        self._bragg_offset = value

    def getBraggStepPerUnit(self, axis):
        return self._bragg_spu

    def setBraggStepPerUnit(self, axis, value):
        self._bragg_spu = value