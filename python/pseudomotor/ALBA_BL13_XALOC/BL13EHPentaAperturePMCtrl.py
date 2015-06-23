from sardana.pool.poolcontrollers.DiscretePseudoMotorController import (
    DiscretePseudoMotorController)

from sardana import DataAccess
from sardana.pool.controller import Type, Access, Description

CALIBRATION = 'Calibration'
LABELS = 'Labels'
NLABELS = 'Nlabels'

class BL13EHPentaApertureController(DiscretePseudoMotorController):
    """
    Discrete controller which provides a pseudomotor as a function of
    role1 and role2 physical motors. It is based on the
    DiscretePseudoMotorController class.
    """
    gender = "ExtendedDiscretePseudoMotorController"
    model = "PseudoMotor"
    organization = "Sardana team"

    pseudo_motor_roles = ('pseudo',)
    motor_roles = ('role1', 'role2',)

    axis_attributes = {CALIBRATION:
                           {Type: str,
                            Description: '3-level nested list. List of valid' \
                                         'positions for each pseudomotor role and each' \
                                         'position element is a list which provides' \
                                         '[min, cal, max] for each motor role',
                            Access: DataAccess.ReadWrite,
                            'fget': 'get%s' % CALIBRATION,
                            'fset': 'set%s' % CALIBRATION},
                       LABELS:
                           {Type: str,
                            Description: 'String list of elements with shape' \
                                         '<str:value>. The <str> represents the pseudo-' \
                                         'motor position with value <value>',
                            Access: DataAccess.ReadWrite,
                            'fget': 'get%s' % LABELS,
                            'fset': 'set%s' % LABELS},
                       NLABELS:
                           {Type: int,
                            Description: 'Number of labels available',
                            Access: DataAccess.ReadOnly,
                            'fget': 'get%s' % NLABELS}
                       }

    def CalcPseudo(self, axis, physical_pos, curr_pseudo_pos):
        llabels = len(self._labels)
        positions = self._positions
        calibration = self._calibration
        lcalibration = self._CheckCalibrationMatrix(calibration)

        # case 0: nothing to translate, only round about integer each attribute value
        if llabels == 0:
            raise Exception('Invalid label configuration')
        # case 1: only uses the labels. Available positions in POSITIONS
        elif lcalibration == 0:
            index = []
            for pos in physical_pos:
                try:
                    index.append(positions.index(int(pos)))
                except:
                    raise Exception('Index is out of range.')
            if self._CheckIndexPos(index, physical_pos):
                msg = 'New pseudo position from index: %s' % index[0]
                self._log.info()
                return index[0]
            else:
                raise Exception('Invalid index for pseudo position.')
                # case 1+fussy: the physical position must be in one of the defined
        # ranges, and the DiscretePseudoMotor position is defined in labels
        elif llabels == lcalibration:
            # Each calibration MUST return the same position i.e. the same index
            # Collect the calibration index for each motor role
            index = []
            for pos, cal in zip(physical_pos, calibration):
                for fussyPos in cal:
                    if pos >= fussyPos[0] and pos <= fussyPos[2]:
                        index.append(cal.index(fussyPos))
            if self._CheckIndexPos(index, physical_pos):
                msg = 'New position from calibration: %s' % (positions[index[0]])
                self._log.info(msg)
                return positions[index[0]]
            else:
                raise Exception('Invalid values returned from calibration.')
        else:
            raise Exception('CalcPseudo failed.')

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        # If Labels is well defined, the write value must be one this struct
        llabels = len(self._labels)
        positions = self._positions
        calibration = self._calibration
        lcalibration = self._CheckCalibrationMatrix(calibration)
        value = pseudo_pos[0]
        pos_list = []

        # case 0: nothing to translate:
        # Return a list with the same value to each physical
        if llabels == 0:
            for m in range(len(self.motor_roles)):
                pos_list.append(value)
            return pos_list
        # case 1: only uses the labels. Available positions in POSITIONS
        elif lcalibration == 0:
            for pos in positions:
                try:
                    pos.index(value)
                except:
                    raise Exception('Invalid position index.')
                pos_list.append(value)
            return pos_list
        # case 1+fussy: the write to the to the DiscretePseudoMotorController
        # is translated to the central position of the calibration.
        elif llabels == lcalibration:
            index = None
            # Get index position corresponding to pseudo position
            try:
                index = positions.index(value)
            except:
                raise Exception('Non valid pseudo position.')

            # Create list of physical positions from calibration
            for cal in calibration:
                pos_list.append(cal[index][1])
            msg = 'Index %s generated position list = %s' %\
                  (index, repr(pos_list))
            self._log.debug(msg)
            return pos_list

    def _CheckCalibrationMatrix(self, calibration):
        # Check the integrity of the calibration matrix
        # A calibration list of triplets MUST exist for each motor role
        # Each calibration list MUST have the same number of elements and
        # the same length as the pseudomotor labels.
        # Returns the length of each calibration (which MUST have the same value)
        lcal_list = []
        if len(calibration) == len(self.motor_roles):
            for cal in calibration:
                lcal_list.append(len(cal))
            if all(lcal_list[0] == c for c in lcal_list):
                return lcal_list[0]
        else:
            raise Exception('Invalid calibration matrix.')

    def _CheckIndexPos(self, index, target_pos):
        return (
            len(index) == len(target_pos) and all(index[0] == i for i in index))


    def getNlabels(self,axis):
        #hackish until we support DevVarDoubleArray in extra attrs
        pos = self._positions
        n = len(pos)
        self._log.debug('Available pseudo positions (%s) = %s' % (n, repr(pos)))
        return n