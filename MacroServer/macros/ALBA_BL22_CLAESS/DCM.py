import time
import PyTango

from macro import Macro, Type

class DCM_startup(Macro):
    """ After each power-up (or PMAC reset) the system must execute a start-up procedure during which
    the Bragg motor is phased (Forced or Soft Phased), motors are homed to their home positions and
    motors assigned into appropriate PMAC coordinate system. 
    
    This macro will call Pmac's PLC - AN AUTOMATED SYSTEM STARTUP PLC (PLC 6) which has
    been created to automate the execution of all these tasks in correct sequence. This will reduce
    downtime and also reduce possibility of error from the operators. 
 
    """
    param_def = [
        ['phasing_mode', Type.String, None, 'Phasing mode: soft or forced']
    ]
    
#    result_def = [
#        ['homed',  Type.Bool, None, 'Motor homed state']
#    ]
    env = ('PmacEth',)
    
    def prepare(self, phasing_mode):
        phasing_mode = phasing_mode.lower()
        if not phasing_mode in ["soft", "forced"]:
            self.error("""phasing_mode parameter is expected to be 'soft' or 'forced'""")
            return False
        PMAC_DEVICE_NAME = self.getEnv("PmacEth")
        try:
            self.pmacEth = PyTango.DeviceProxy(PMAC_DEVICE_NAME)
        except DevFailed,e:
            self.error("PmacEth DeviceProxy cannot be created. PmacEth environment variable is wrong")
            
        
    def run(self, phasing_mode):
#        This can be used to check state of motors (in position)
#        self.pool = self.motor.getPoolObj()
#        bragg_mot = self.pool.getPoolElement("dcm_bragg")
#        perp_mot = self.pool.getPoolElement("dcm_perp")
        
        self.pmacEth.command_inout("EnablePLC", 6)
        self.debug("""Command 'EnablePLC 6' was send to Pmac""")
        time.sleep(2)
        #ReadyForPhasing - P199 variable
        p199 = self.pmacEth.command_inout("GetPVariable", 199)
        self.debug("ReadyForPhasing (P199) = %f" % p199)
        if p199 != 1.0:
            self.error("DCM is not ready for phasing, exiting...")
            return False
        phasing_mode = phasing_mode.lower()
        if phasing_mode == "soft":
            #SoftPhasing - P57
            self.pmacEth.command_inout("SetPVariable", [57,1])
            self.debug("""Command 'P57=1 (SoftPhasing=1' was send to Pmac""")
        else:
            #ForcedPhasing - P58
            self.pmacEth.command_inout("SetPVariable", [58,1])
            self.debug("""Command 'P58=1 (ForcedPhasing=1)' was send to Pmac""")
        
        p96 = 0.0; p86 = 1.0
        while (p96==0.0 and p86==1.0):
            time.sleep(1)
            p96 = self.pmacEth.command_inout("GetPVariable",96)
            p86 = self.pmacEth.command_inout("GetPVariable",86)
        if p96:
            self.debug("AutoStartupCompleted flag was set.")
        if not p86:
            self.debug("SystemStartupFlag was reset.")
        #@todo: Maybe we should also check if all motions are stopped

        #SystemHomed - P73
        p73 = self.pmacEth.command_inout("GetPVariable", 73)
        if p73:
            self.info("System homed successfully. DCM is ready for working. Exiting...")
            return
        else:
            #p117 Bragg Phased Flag
            p117 = self.pmacEth.command_inout("GetPVariable", 117)
            #p69 Process Timeout Flag
            p69 = self.pmacEth.command_inout("GetPVariable", 69)
            #m68 Process Skipped Flag
            m68 = self.pmacEth.command_inout("GetMVariable", 68)
            if not p117:
                self.warning("Bragg motor phasing failed.")
            if p69:
                self.warning("Process timeout.")
            if m68:
                self.warning("Process skipped.")    
            self.info("System could not be homed. DCM is not ready for working. Please rerun macro. Exiting...")
            return
                
    def on_abort(self):
        pass
    
class DCM_pre_energy_move(Macro):
    """ This macro should be run before every energy move. 
    However before scanning it is enough to run it only once. 
    It aborts all motion and checks correct coordinate system definition:
        &1#1->X#3->Y"""
        
    env = ('PmacEth',)
    
    def prepare(self):
        PMAC_DEVICE_NAME = self.getEnv("PmacEth")
        try:
            self.pmacEth = PyTango.DeviceProxy(PMAC_DEVICE_NAME)
        except DevFailed,e:
            self.error("PmacEth DeviceProxy cannot be created. PmacEth environment variable is wrong.")
            
    def run(self):
        self.pmacEth.command_inout("SendCtrlChar", "A")
        self.info("All motion activities were aborted.")
        bragg_ans = self.pmacEth.command_inout("OnlineCmd", "&1#1->")
        bragg_ok =bragg_ans.endswith("X") 
        if bragg_ok:
            self.debug("Bragg motor (first axis) is correctly assigned to the coordinate system.")
        else:
            self.warning("Bragg motor (first axis) is not correctly assigned to the coordinate system.")
        perp_ans = self.pmacEth.command_inout("OnlineCmd", "&1#3->")
        perp_ok = perp_ans.endswith("Y") 
        if perp_ok:
            self.debug("Perpendicular motor (third axis) is correctly assigned to the coordinate system.")
        else:
            self.warning("Perpendicular motor (third axis) is not correctly assigned to the coordinate system.")
        if bragg_ok and perp_ok:
            self.info("All motors are correctly assigned to coordinate system. DCM ready for energy move.")
            return
        else:
            self.error("Coordination system needs to be reassigned. Doing it now...")
        self.pmacEth.command_inout("OnlineCmd","undefine all")
        self.pmacEth.command_inout("OnlineCmd", "&1#1->X#3->Y")
        self.info("Coordination system reassigned.")
        return5
        
            
            
            
        
         

