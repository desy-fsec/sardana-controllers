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

    axis_attributes = {
        CALIBRATION:
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
        positions = self._positions
        calibration = self._calibration
        cm = CalibrationMatrix(calibration)

        llabels = len(self._labels)
        lcalibration = cm.axis_dim

        if llabels == lcalibration:
            idx = cm.get_pseudo_pos_index(physical_pos)
            self._log.debug("Index found is %s" % idx)
            return positions[int(idx)]
        else:
            msg = "labels = %s, points per axis = %s" % (llabels, lcalibration)
            self._log.error(msg)
            raise Exception('CalcPseudo failed.\n%s' % msg)

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        positions = self._positions
        calibration = self._calibration
        cm = CalibrationMatrix(calibration)

        llabels = len(self._labels)
        lcalibration = cm.axis_dim

        value = pseudo_pos[0]
        pos_list = []

        if llabels == lcalibration:
            # Get index position corresponding to pseudo position
            try:
                index = positions.index(value)
            except Exception:
                raise Exception('Non valid pseudo position.')

            # Create list of physical positions from calibration
            for cal in cm.axis_cal:
                pos_list.append(cal[index].value)
            msg = 'Index %s generated position list = %s' %\
                  (index, repr(pos_list))
            self._log.debug(msg)
            return pos_list

    def getNlabels(self, axis):
        labels = self._labels
        return len(labels)


class CalibrationMatrix(object):
    def __init__(self, calibrations):
        # Extract calibration by axis as arrays of fuzzy points.
        self.axis_cal = []
        for c in calibrations:
            cal = []
            for point in c:
                # A calibration list of triplets MUST exist for each motor role
                if len(point) == 3:
                    cal.append(FuzzyPoint(*point))
                else:
                    msg = "Position point has no valid structure" \
                          " min/pos/max\n dimension is %s" % len(p)
                    raise Exception(msg)
            # append new axis calibration
            self.axis_cal.append(cal)

        # Store ALL calibration dimensions
        lcal = []
        for c in self.axis_cal:
            lcal.append(len(c))

        # Each calibration MUST have the same number of positions
        if not all(lcal[0] == c for c in lcal):
            msg = "Inconsistent axes dimensions.\n%s" % repr(lcal)
            raise Exception(msg)

        self.n_axis = len(self.axis_cal)
        self.axis_dim = lcal[0]

    def get_pseudo_pos_index(self, positions):
        # Each calibration MUST return the same position i.e. the same index
        # Collect the calibration index for each motor role
        for i in range(self.axis_dim):
            found = []
            for pos, cal in zip(positions, self.axis_cal):
                res = cal[i].includes(pos)
                found.append(res)
            if all(found):
                return i
        return float('NaN')

    def __repr__(self):
        _str = ""
        for e, c in enumerate(self.axis_cal):
            _str += "\naxis %-2s --> " % e
            for p in c:
                _str += "%-20s " % p
        return _str


class FuzzyPoint(object):
    def __init__(self, min, value, max):
        self.min = min
        self.value = value
        self.max = max

    def includes(self, value):
        return self.min <= value <= self.max

    def __repr__(self):
        return "[%s, %s, %s]" % (self.min, self.value, self.max)


def main(pt):

    cm = CalibrationMatrix([[[0.9, 1.0, 1.1], [1.9, 2.0, 2.1], [2.9, 3.0, 3.1]],
                            [[9.0, 10.0, 11.0], [19.0, 20.0, 21.0],
                             [29.0, 30.0, 31.0]]])
    print "\nCalibration matrix:"
    print cm
    print "\nPseudo = %s\n" % cm.get_pseudo_pos_index(pt)


if __name__ == "__main__":
    p = [3.0, 30.0]
    main(p)
