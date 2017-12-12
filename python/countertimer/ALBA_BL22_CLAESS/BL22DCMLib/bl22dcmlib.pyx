# distutils: extra_compile_args = -fopenmp
# distutils: extra_link_args = -fopenmp

from cython cimport boundscheck, wraparound
from cython.parallel cimport prange
import numpy as np

cdef extern from "math.h" nogil:
    double sin(double x)
    double asin(double x)

cdef double degrees(double radian) nogil:
    return radian * 180 / 3.14159265359

cdef double radians(double degree) nogil:
    return degree * 3.14159265359 / 180

cdef double energy2bragg (double energy, double vcm_pitch, double d,
                   double offset) nogil:
    """
    Method to calculate the bragg angle
    :param energy: Energy in eV
    :param vcm_pitch_rad: VCM pitch angle in rad
    :param d: constant d of the crystal
    :param offset: offset of the crystal
    :return: bragg angle in degree
    """
    cdef double bragg_rad, bragg_deg, hc = 12398.419 #eV *Angstroms


    bragg_rad = asin(hc/2/d/energy) + 2 * vcm_pitch + offset
    bragg_deg = degrees(bragg_rad)
    return bragg_deg


cdef double bragg2energy (double bragg, double vcm_pitch, double d,
                   double offset) nogil:
    """
    Method to calculate the bragg angle
    :param bragg: Bragg angle in degree
    :param vcm_pitch_rad: VCM pitch angle in rad
    :param d: constant d of the crystal
    :param offset: offset of the crystal
    :return: Energy in eV
    """

    cdef double bragg_rad, energy, hc = 12398.419 #eV *Angstroms


    bragg_rad = radians(bragg)
    t = (2 * d * sin(bragg_rad - 2 * vcm_pitch - offset))
    if t == 0:
        energy = 0
    else:
        energy = hc / t

    return energy



cdef long bragg2encoder(double bragg, double bragg_spu, double bragg_offset,
                        long bragg_pos, long bragg_enc) nogil:
    """
    Function to calculate the encoder value for one bragg angle.
    :param bragg: Bragg angle in degrees
    :param bragg_spu: Bragg step per unit (Sardana)
    :param bragg_offset: Bragg offset (Sardana)
    :param bragg_pos: Pmac internal offset of the bragg motor
    :param bragg_enc: Pmac internal value of the encoder
    :return: encoder value
    """


    cdef:
        long braggMotorOffsetEncCounts, enc_value
        double offset
        long PMAC_OVERFLOW = 8388608 #2**23 encoder register 24 bits overflow

    if bragg_enc < 0:
        bragg_enc = 2 * PMAC_OVERFLOW + bragg_enc

    braggMotorOffsetEncCounts = <long> (bragg_offset * bragg_spu)
    offset = bragg_pos - bragg_enc + braggMotorOffsetEncCounts

    enc_value = <long> ((bragg * bragg_spu) - offset)

    if enc_value > PMAC_OVERFLOW:
        enc_value = enc_value - 2 * PMAC_OVERFLOW
    elif enc_value > -PMAC_OVERFLOW:
        enc_value = enc_value + 2 * PMAC_OVERFLOW

    return enc_value


cdef double encoder2bragg(long encoder, double bragg_spu, double bragg_offset,
                          long bragg_pos, long bragg_enc) nogil:
    """
    Function to calcule the bragg angle value for one encoder.

    :param encoder: Encoder value
    :param bragg_spu: Bragg step per unit (Sardana)
    :param bragg_offset: Bragg offset (Sardana)
    :param bragg_pos: Pmac internal offset of the bragg motor
    :param bragg_enc: Pmac internal value of the encoder
    :return: Bragg angle in degrees
    """


    #translations from raw counts to degrees
    #getting an offset between position and encoder register (offset = 2683367)

    cdef:
        double braggMotorOffsetEncCounts, enc_value, d
        double offset
        long PMAC_OVERFLOW = 8388608 #2**23 encoder register 24 bits overflow

    braggMotorOffsetEncCounts = <double> (bragg_offset * bragg_spu)
    if bragg_enc < 0:
        bragg_enc = 2 * PMAC_OVERFLOW + bragg_enc

    offset = <double>(bragg_pos - bragg_enc + braggMotorOffsetEncCounts)

    enc_value = <double> (encoder + offset)
    if enc_value > PMAC_OVERFLOW:
        enc_value = enc_value - 2 * PMAC_OVERFLOW
    elif enc_value > -PMAC_OVERFLOW:
        enc_value = enc_value + 2 * PMAC_OVERFLOW


    return enc_value/bragg_spu


cdef long energy2encoder (double energy, double vcm_pitch_rad, double d,
                          double offset, double bragg_spu,
                          double bragg_offset, long bragg_pos, long bragg_enc)\
        nogil:
    """
    Function to convert from energy to encoder value

    :param energy: Energy in eV
    :param vcm_pitch_rad: VCM pitch angle in rad
    :param d: constant d of the crystal
    :param offset: offset of the crystal
    :param bragg_spu: Bragg step per unit (Sardana)
    :param bragg_offset: Bragg offset (Sardana)
    :param bragg_pos: Pmac internal offset of the bragg motor
    :param bragg_enc: Pmac internal value of the encoder
    :return: encoder value
    """

    cdef:
        double bragg
        long encoder

    bragg = energy2bragg(energy, vcm_pitch_rad, d, offset)
    encoder = bragg2encoder(bragg, bragg_spu, bragg_offset, bragg_pos,
                            bragg_enc)
    return encoder


cdef double encoder2energy (long encoder, double vcm_pitch_rad, double d,
                          double offset, double bragg_spu,
                          double bragg_offset, long bragg_pos, long bragg_enc)\
        nogil:

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

    cdef double bragg, energy
    bragg = encoder2bragg(encoder,bragg_spu, bragg_offset, bragg_pos,
                          bragg_enc)
    energy = bragg2energy(bragg, vcm_pitch_rad, d, offset)
    return energy



@boundscheck(False)
@wraparound(False)
cpdef enegies4encoders(long[:] encoders, double vcm_pitch_rad, double d,
                       double offset, double bragg_spu,
                       double bragg_offset, long bragg_pos, long bragg_enc):

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
    cdef:
        long i, N
        double[:] values

    N = encoders.shape[0]
    values = np.zeros(N, dtype=np.float64)

    for i in prange(N, nogil=True):
        values[i] = encoder2energy(encoders[i], vcm_pitch_rad, d, offset,
                                   bragg_spu, bragg_offset, bragg_pos,
                                   bragg_enc)
    return np.asarray(values)

@boundscheck(False)
@wraparound(False)
cpdef encoders4energies(double[:] energies, double vcm_pitch_rad, double d,
                       double offset, double bragg_spu,
                       double bragg_offset, long bragg_pos, long bragg_enc):

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
    cdef:
        long i, N
        double[:] values

    N = energies.shape[0]
    values = np.zeros(N, dtype=np.int32)

    for i in prange(N, nogil=True):
        values[i] = energy2encoder(energies[i], vcm_pitch_rad, d, offset,
                                   bragg_spu, bragg_offset, bragg_pos,
                                   bragg_enc)
    return np.asarray(values)

cpdef getbragg(long encoder, double bragg_spu, double bragg_offset,
                          long bragg_pos, long bragg_enc):
    return encoder2bragg(encoder, bragg_spu, bragg_offset,
                         bragg_pos, bragg_enc)