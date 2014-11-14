#!/usr/bin/env python
#############################################################################
##
## file :    ZoomPseudoMotorl.py
##
## description : Zoom movement from encoder steps to um/div motor
##
## project :    Sardana/Pool/ctrls/PseudoMotors
##
## developers history: droldan, gjover, rhoms
##
## copyleft :    Cells / Alba Synchrotron
##               Bellaterra
##               Spain
##
#############################################################################
##
## This file is part of Sardana.
##
## This is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This software is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <http://www.gnu.org/licenses/>.
###########################################################################

import numpy as np
from sardana.pool.controller import PseudoMotorController

NaN = float('nan')


class ZoomPMController(PseudoMotorController):
    """Pseudo to convert Steps per Unit movement to um/pix

       length = movement length from rotaion axis projection point
       radius = shortest distance between movement and rotation axis
    """

    gender = "zoom"
    model = ""
    organization = "CELLS - ALBA"
    image = "energy.png"  # FIXME
    logo = "ALBA_logo.png"
    
    pseudo_motor_roles = ("zoom",)
    motor_roles = ("physical_motor",)
    
    class_prop = {'Unit2ZoomFormula':
                  {'Description' : ('The formula to transform from unit motor'
                                    ' to zoom. \ne.g. "(VALUE/10)*1e-06"'), 
                   'Type' : 'PyTango.DevString'},
                  'Zoom2UnitFormula':
                  {'Description' : ('The formula to transform from unit motor'
                                    ' to zoom. \ne.g. "(VALUE/10)*1e-06"'), 
                   'Type' : 'PyTango.DevString'},
                  'RatioXY':
                  {'Description' : 'Relation between pixel size (X/Y).', 
                   'Type' : 'PyTango.DevString'},
                  }
    
    axis_attributes = {}
    
    def CalcPhysical(self, index, pseudos, curr_physicals):
        return self.CalcAllPhysical(pseudos, curr_physicals)[index - 1]

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return self.CalcAllPseudo(physicals, curr_pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physicals):
        value = pseudos[0]
        try:
            position = eval(self.Zoom2UnitFormula.lower())
            return (position,)
        except Exception, e:
            self._log.error('calc_all_physical(): Exception %s' % (e))
            return (NaN,)

    def CalcAllPseudo(self, physicals, curr_pseudos):
        value = physicals[0]
        try:
            zoom = eval(self.Unit2ZoomFormula.lower())
            return (zoom,)
        except Exception, e:
            self._log.error('calc_all_pseudo(): Exception %s' % (e))
            return (NaN,)


