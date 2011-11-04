from macro import Macro, Type, Hookable
import time


class repeat(Hookable, Macro):
    """This macro executes as many repetitions of it's body hook macros as specified by nr parameter.
       If nr parameter has negative value, repetitions will be executed until you stop repeat macro."""

    #hints = { 'allowsHooks': ('body', 'break', 'continue') }
    hints = { 'allowsHooks': ('body',) }
    
    param_def = [
       ['nr', Type.Integer, None, 'Nr of iterations' ]
    ]
    
    def prepare(self, nr):
        #self.breakHooks = self.getHooks("break")
        #self.continueHooks = self.getHooks("continue")
        self.bodyHooks = self.getHooks("body")
    
    def __loop(self):
        self.checkPoint()
        for bodyHook in self.bodyHooks:
            bodyHook()
        
    def run(self, nr):
        if nr < 0:            
            while True: 
                self.__loop()
        else:
            for i in range(nr):
                self.__loop()
                progress = ((i+1)/float(nr))*100
                yield progress
                
class dwell(Macro):
    """This macro waits for a time amount specified by dtime parameter. (python: time.sleep(dtime))"""
    
    param_def = [
       ['dtime', Type.Float, None, 'Dwell time in seconds' ]
    ]
    
    def run(self, dtime):
        time.sleep(dtime)