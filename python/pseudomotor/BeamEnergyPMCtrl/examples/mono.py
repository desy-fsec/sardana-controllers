# Units mm, keV, s

# Gap between DCM crystals
DELTA = 30 # mm

def e_corr(e):
    ''' Returns corrected enery from calculated energy'''
    return e

def e_ucorr(e):
    ''' Returns uncorredted energy corresponding to the actual energy'''
    return e

def d_spacing(temp):
    ''' Retuns crystal d_spacing for the given temperature'''
    return 0.3135e-6 # mm
