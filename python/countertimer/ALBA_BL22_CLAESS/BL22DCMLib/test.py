import numpy as np
import pyximport
pyximport.install()
import bl22dcmlib



if __name__ == '__main__':
    rawCounts = np.array([-6377058])
    vcm_pitch_rad = 0.0038024892218247778
    xtal_d = 3.1354161
    xtal_offset = -0.0108829885249638
    bragg_spu = 200000.0
    bragg_offset = 0.075
    bragg_pos = 10400677.0
    bragg_enc = -6377058.0
    print bl22dcmlib.enegies4encoders(rawCounts, vcm_pitch_rad,
                                               xtal_d,
                                               xtal_offset, bragg_spu,
                                               bragg_offset, bragg_pos,
                                               bragg_enc)

    print bl22dcmlib.getbragg(rawCounts[0], bragg_spu,
                                               bragg_offset, bragg_pos,
                                               bragg_enc)
    
    rawCounts = np.array([3478717])
    vcm_pitch_rad = 0.003305760724198934
    xtal_d = 1.637418
    xtal_offset = -0.0124741939806131
    bragg_spu = 200000.0
    bragg_offset = 0.075
    bragg_pos = 3479236.5
    bragg_enc = 3478717.0

    print 'Should be:', 12380.0021692
    print bl22dcmlib.enegies4encoders(rawCounts, vcm_pitch_rad,
                                               xtal_d,
                                               xtal_offset, bragg_spu,
                                               bragg_offset, bragg_pos,
                                               bragg_enc)
    print 'Should be:', 17.4711775
    print bl22dcmlib.getbragg(rawCounts[0], bragg_spu,
                                               bragg_offset, bragg_pos,
                                               bragg_enc)

    rawCounts = np.array([8381945])
    vcm_pitch_rad = 0.0038029889762572888
    xtal_d = 3.1354161
    xtal_offset = -0.0108689042918572
    bragg_spu = 200000.0
    bragg_offset = 0.075
    bragg_pos = 8382465.0
    bragg_enc = 8381947.0

    print 'Should be:', 2944.88038418
    print bl22dcmlib.enegies4encoders(rawCounts, vcm_pitch_rad,
                                      xtal_d,
                                      xtal_offset, bragg_spu,
                                      bragg_offset, bragg_pos,
                                      bragg_enc)

    print 'Should be:', 41.987325
    print bl22dcmlib.getbragg(rawCounts[0], bragg_spu,
                              bragg_offset, bragg_pos, bragg_enc)
