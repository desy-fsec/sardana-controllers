from PyTango import DevState
from sardana.pool.controller import MotorController
from sardana.pool import PoolUtil
import time
from threading import Timer

TANGO_DEV = 'TangoDevice'


class OxfordCryostream700Ctrl(MotorController):
    """This class is the Tango Sardana motor controller for the
       Tango OxfordCryostream700 device. Each 'axis' is represents,
       a single device, the position equates to the temperature"""

    axis_attributes = {TANGO_DEV: {
        'Type': 'PyTango.DevString',
        'Description': 'Tango Device Server name.',
        'R/W Type': 'PyTango.READ_WRITE'
    }}

    gender = "Cryostream"
    model = "Oxford Cryostream 700"
    organization = "Oxford"

    RESTART_INTERVAL = 20.0

    def __init__(self, inst, props):
        MotorController.__init__(self, inst, props)
        self.extra_attributes = {}
        self.proxy = {}
        self.velocity = {}
        self.restarted = {}
        self.delay_timer = {}

    def getProxy(self, axis, raiseOnConnError=True):
        proxy = self.proxy.get(axis)
        if not proxy:
            devName = self.extra_attributes[axis][TANGO_DEV]
            if devName is not None:
                proxy = PoolUtil().get_device(self.GetName(), devName)
                self.proxy[axis] = proxy
                if proxy is None and raiseOnConnError:
                    raise Exception(
                        "Proxy for '%s' could not be created" % devName)
                if self.velocity[axis] == 0.0:
                    try:
                        self.velocity[axis] = \
                            float(proxy.read_attribute("RampRate").value)
                        if self.velocity[axis] == 0.0:
                            self.velocity[axis] = 360.0
                    except Exception as e:
                        if raiseOnConnError:
                            raise e
                        else:
                            msg = "Cryostream '%s' is not available" % devName
                            self._log.error(msg)
        return proxy

    def AddDevice(self, axis):
        self.extra_attributes[axis] = {}
        self.extra_attributes[axis][TANGO_DEV] = None
        self.velocity[axis] = 0.0
        self.restarted[axis] = [0, 0]
        self.delay_timer[axis] = None

    def DeleteDevice(self, axis):
        if axis in self.proxy:
            del self.proxy[axis]
        if axis in self.extra_attributes:
            del self.extra_attributes[axis]
        if axis in self.velocity:
            del self.velocity[axis]
        if axis in self.restarted:
            del self.restarted[axis]
        if axis in self.delay_timer:
            self.delay_timer[axis].cancel()
            del self.delay_timer[axis]

    def StateOne(self, axis):
        diff = time.time() - self.restarted[axis][0]
        if diff < OxfordCryostream700Ctrl.RESTART_INTERVAL:
            state = DevState.ON
            status = "The device is in StartUp State"
        else:
            try:
                proxy = self.getProxy(axis)
                state = proxy.state()
                status = proxy.status()
                phase = proxy.read_attribute("Phase").value
            except Exception as e:
                return DevState.FAULT, str(e), 0
            self.restarted[axis] = [0, 0]
            if state == DevState.RUNNING and phase == "Hold":
                state = DevState.ON
            elif state == DevState.RUNNING:
                state = DevState.MOVING
            elif state == DevState.OFF:
                state = DevState.ON
        return (state, status)

    def ReadOne(self, axis):
        diff = time.time() - self.restarted[axis][0]
        if diff < OxfordCryostream700Ctrl.RESTART_INTERVAL:
            return self.restarted[axis][1]
        proxy = self.getProxy(axis)
        return proxy.read_attribute("GasTemp").value

    def StartOne(self, axis, position):
        # test for pending actions
        if self.delay_timer[axis] is not None \
                and self.delay_timer[axis].isAlive():
            self.delay_timer[axis].cancel()
            self.delay_timer[axis] = None
        elif self.delay_timer[axis] is not None \
                and not self.delay_timer[axis].isAlive():
            self.delay_timer[axis] = None
        diff = time.time() - self.restarted[axis][0]
        if diff < OxfordCryostream700Ctrl.RESTART_INTERVAL:
            self.delay_timer[axis] = \
                Timer(OxfordCryostream700Ctrl.RESTART_INTERVAL - diff,
                      self.StartOne, [axis, position])
            self.delay_timer[axis].start()
            return
        self.restarted[axis] = [0, 0]
        # take action
        proxy = self.getProxy(axis)
        state = proxy.state()
        if state in [DevState.ON, DevState.RUNNING]:
            proxy.command_inout("Ramp", [self.velocity[axis], position])
        # Restart if device is shutdown and recall afterwards
        elif state == DevState.OFF:
            current_pos = proxy.read_attribute("GasTemp").value
            proxy.command_inout("Restart")
            self.restarted[axis] = [time.time(), current_pos]
            self.delay_timer[axis] = \
                Timer(OxfordCryostream700Ctrl.RESTART_INTERVAL,
                      self.StartOne, [axis, position])
            self.delay_timer[axis].start()

    def SetAxisPar(self, axis, name, value):
        proxy = self.getProxy(axis)
        if proxy is not None:
            name = name.lower()
            if name == "acceleration" or name == "deceleration":
                pass
            elif name == "base_rate":
                pass
            elif name == "velocity":
                self.velocity[axis] = value
                phase = proxy.read_attribute("Phase").value
                if phase == "Ramp":
                    position = proxy.read_attribute("TargetTemp").value
                    self.StartOne(axis, position)
            elif name == "step_per_unit":
                pass

    def GetAxisPar(self, axis, name):
        value = float("nan")
        proxy = self.getProxy(axis)
        if proxy is not None:
            name = name.lower()
            if name == "acceleration":
                if proxy.state() in [DevState.ON, DevState.RUNNING]:
                    value = 1.0
                else:
                    value = OxfordCryostream700Ctrl.RESTART_INTERVAL
            elif name == "deceleration":
                value = 1.0
            elif name == "base_rate":
                if proxy.state() in [DevState.ON, DevState.RUNNING]:
                    value = 360.0
                else:
                    value = 0.0
            elif name == "velocity":
                value = self.velocity[axis]
            elif name == "step_per_unit":
                value = 1.0
        return value

    def GetAxisExtraPar(self, axis, name):
        if name in [TANGO_DEV, ]:
            return self.extra_attributes[axis][name]

    def SetAxisExtraPar(self, axis, name, value):
        if name in [TANGO_DEV, ]:
            self.extra_attributes[axis][name] = value
            if axis in self.proxy:
                del self.proxy[axis]

    def AbortOne(self, axis):
        self.StopOne(axis)

    def StopOne(self, axis):
        # test for pending actions and cancel them
        if self.delay_timer[axis] is not None \
                and self.delay_timer[axis].isAlive():
            self.delay_timer[axis].cancel()
            self.delay_timer[axis] = None
        # take action
        proxy = self.getProxy(axis)
        state = proxy.state()
        if state == DevState.RUNNING:
            proxy.command_inout("Hold")

    def DefinePosition(self, axis, position):
        raise Exception('not implemented')
