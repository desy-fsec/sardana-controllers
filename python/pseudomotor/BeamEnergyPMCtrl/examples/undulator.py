
import numpy as np
from scipy.constants import physical_constants

# Units um, keV, s

def gap(energy, harmonic, tune, harmonicAutoSet):
    hcva = physical_constants[
        'inverse meter-electron volt relationship'][0]

    Gamma  = 5845.97
    LambdaU = 0.0216
    a0 = -178.683137165
    a1 = 101031.437305031
    a2 = -268554.955894147
    a3 = 333043.58574148
    a4 = -223412.253880588
    a5 = 78201.083309632
    a6 = -11222.656555176

    harmonics = [harmonic]
    if harmonicAutoSet:
        harmonics = [11, 9, 7, 5, 3]

    for n in harmonics:
        E1 = energy*1000.0/n
        K = np.real(np.sqrt(4.0 * hcva * Gamma ** 2 
                            / (LambdaU * E1) - 2.0))
        gap = (a0 
               + a1 * K 
               + a2 * K ** 2 
               + a3 * K ** 3 
               + a4 * K ** 4 
               + a5 * K ** 5 
               + a6 * K ** 6)
        if gap > 5700:
            break

    return gap, n
