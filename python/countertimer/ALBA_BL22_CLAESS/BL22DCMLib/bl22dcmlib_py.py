import numpy as np
from math import sin

PMAC_OVERFLOW = 8388608  # 2**23 encoder register 24 bits overflow
hc = 12398.419  # eV *Angstroms


def degrees(radian):
    return radian * 180 / 3.14159265359


def radians(degree):
    return degree * 3.14159265359 / 180


def encoder2bragg(encoder, bragg_spu, bragg_offset,
                  bragg_pos, bragg_enc):
    """
    Function to calcule the bragg angle value for one encoder.

    :param encoder: Encoder value
    :param bragg_spu: Bragg step per unit (Sardana)
    :param bragg_offset: Bragg offset (Sardana)
    :param bragg_pos: Pmac internal offset of the bragg motor
    :param bragg_enc: Pmac internal value of the encoder
    :return: Bragg angle in degrees
    """

    # translations from raw counts to degrees
    # getting an offset between position and encoder register (offset =
    # 2683367)


    braggMotorOffsetEncCounts = bragg_offset * bragg_spu

    bragg_pos += braggMotorOffsetEncCounts
    delta_encoder = abs(encoder - bragg_enc)
    if delta_encoder >= PMAC_OVERFLOW:
        if encoder < bragg_enc:
            new_encoder = PMAC_OVERFLOW + abs(-8388606.5 - encoder)
            delta_encoder = abs(new_encoder - bragg_pos)
            enc_value = bragg_pos + delta_encoder
        else:
            new_encoder = -8388606.5 - (PMAC_OVERFLOW - encoder)
            delta_encoder = abs(new_encoder - bragg_enc)
            enc_value = bragg_pos - delta_encoder
    else:
        if encoder < bragg_enc:
            enc_value = bragg_pos - delta_encoder
        else:
            enc_value = bragg_pos + delta_encoder

    return enc_value/bragg_spu


def bragg2energy(bragg, vcm_pitch, d, offset):
    """
    Method to calculate the bragg angle
    :param bragg: Bragg angle in degree
    :param vcm_pitch_rad: VCM pitch angle in rad
    :param d: constant d of the crystal
    :param offset: offset of the crystal
    :return: Energy in eV
    """

    bragg_rad = radians(bragg)
    t = (2 * d * sin(bragg_rad - 2 * vcm_pitch - offset))
    if t == 0:
        energy = 0
    else:
        energy = hc / t

    return energy


def encoder2energy(encoder, vcm_pitch_rad, d, offset, bragg_spu,
                   bragg_offset, bragg_pos, bragg_enc):

    """
    Function to convert from encoder to energy value

    :param encoder: encoder value
    :param vcm_pitch_rad: VCM pitch angle in rad
    :param d: constant d of the crystal
    :param offset: offset of the crystal
    :param bragg_spu: Bragg step per unit (Sardana)
    :param bragg_offset: Bragg offset (Sardana)
    :param bragg_pos: Pmac internal offset of the bragg motor
    :param bragg_enc: Pmac internal value of the encoder
    :return: Energy in eV
    """

    bragg = encoder2bragg(encoder,bragg_spu, bragg_offset, bragg_pos,
                          bragg_enc)
    energy = bragg2energy(bragg, vcm_pitch_rad, d, offset)
    return energy


def enegies4encoders(encoders,vcm_pitch_rad, d, offset, bragg_spu,
                     bragg_offset, bragg_pos, bragg_enc):

    """
    Function to transform an encoder array to energies array

    :param encoders: numpy array of encoder value
    :param vcm_pitch_rad: VCM pitch angle in rad
    :param d: constant d of the crystal
    :param offset: offset of the crystal
    :param bragg_spu: Bragg step per unit (Sardana)
    :param bragg_offset: Bragg offset (Sardana)
    :param bragg_pos: Pmac internal offset of the bragg motor
    :param bragg_enc: Pmac internal value of the encoder
    :return: numpy array with energies values in eV
    """

    N = encoders.shape[0]
    values = np.zeros(N, dtype=np.float64)

    for i in xrange(N):
        values[i] = encoder2energy(encoders[i], vcm_pitch_rad, d, offset,
                                   bragg_spu, bragg_offset, bragg_pos,
                                   bragg_enc)
    return np.asarray(values)


def getbragg(encoder, bragg_spu, bragg_offset,
             bragg_pos, bragg_enc):
    return encoder2bragg(encoder, bragg_spu, bragg_offset,
                         bragg_pos, bragg_enc)