"""
    Macro for testing the Movable Masks in FE09
"""

from macro import *
import time

class scanMM(Macro):
    hints = { 'allowsHooks':('post-move') } #needed for gui?
    
    param_def = [ [ 'motor1', Type.Motor, None, 'Motor 1' ],
                  [ 'startPos', Type.Float, None, 'startPos1' ],
                  [ 'endPos', Type.Float, None, 'endPos1' ],
                  [ 'nIntervals', Type.Integer, None, 'Number of intervals' ],
                  [ 'integrationTime', Type.Float, None, 'Integration time' ],
                  [ 'motor2', Type.Motor, None, 'Motor 2' ],
                  [ 'fixedPos', Type.Float, None, 'Fixed Pos' ],
                  [ 'sleepTime', Type.Float, None, 'sleep time' ],
                ]

    def prepare(self, motor1,startPos,endPos,nIntervals,integrationTime,motor2,fixedPos,sleepTime):
        """Check that parameters for the macro are correct"""
        self.output("\n\n~~~~~ Preparing scanMM macro ~~~~")
        self.motor2 = motor2
        self.sleepTime = sleepTime
        self.fixedPos = fixedPos
        
    def myHook(self):
        self.motor2.move([self.fixedPos])
        time.sleep(self.sleepTime)
    
    def run(self, motor1,startPos,endPos,nIntervals,integrationTime,motor2,fixedPos,sleepTime):
        #"""Run macro"""       
        myMacro, pars = self.createMacro("ascan",motor1,startPos,endPos,nIntervals,integrationTime)
        myMacro.hooks = [(self.myHook, ['post-move'])]
        self.runMacro(myMacro)