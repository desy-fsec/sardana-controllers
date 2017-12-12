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
