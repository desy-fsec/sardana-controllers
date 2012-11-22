from sardana import pool
from sardana.pool.controller import PseudoMotorController
from detector import detcalc

class BL13EHDetSamDisController(PseudoMotorController):
  """ Calculate detector-sample distance based on dettaby.
  """

  pseudo_motor_roles = ('detsamdis',)
  motor_roles = ('dettaby',)

  def __init__(self, inst, props, *args, **kwargs):
    PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

  def CalcPhysical(self, index, pseudos, curr_physicals):
    detsamdis, = pseudos
    return detcalc.detsamdis_dettaby(detsamdis, request='dettaby')

  def CalcPseudo(self, index, physicals, curr_pseudos):
    dettaby, = physicals
    return detcalc.detsamdis_dettaby(dettaby, request='detsamdis')

class BL13EHResolutionCompleteController(PseudoMotorController):
  """ Calculate complete resolution at detector based on dettaby.
  """

  pseudo_motor_roles = ('rescomp',)
  motor_roles = ('dettaby',)

  def __init__(self, inst, props, *args, **kwargs):
    PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

  def CalcPhysical(self, index, pseudos, curr_physicals):
    rescomp, = pseudos
    return detcalc.resdetdis(rescomp, request='dettaby', request2='complete')

  def CalcPseudo(self, index, physicals, curr_pseudos):
    dettaby, = physicals
    return detcalc.resdetdis(dettaby, request='resolution', request2='complete')

class BL13EHResolutionEdgeController(PseudoMotorController):
  """ Calculate edge resolution at detector based on dettaby.
  """

  pseudo_motor_roles = ('resedge',)
  motor_roles = ('dettaby',)

  def __init__(self, inst, props, *args, **kwargs):
    PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

  def CalcPhysical(self, index, pseudos, curr_physicals):
    resedge, = pseudos
    return detcalc.resdetdis(resedge, request='dettaby', request2='edge')

  def CalcPseudo(self, index, physicals, curr_pseudos):
    dettaby, = physicals
    return detcalc.resdetdis(dettaby, request='resolution', request2='edge')

