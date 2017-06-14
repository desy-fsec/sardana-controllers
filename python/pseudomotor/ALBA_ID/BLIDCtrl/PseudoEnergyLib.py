import math as m
import numpy as np
import time
import scipy
import scipy.optimize

# declaration of global variables
#general physical constants
MILI    = 1E-3
MICRO   = 1E-6
ECHARGE = 1.60217653E-19  #/C
LIGHTC = 299792458  # M/S
EMASS = 0.000510998918  # GeV 
EMASSKG = 9.10938188E-31 # Kg 
#H_PLANK = 6.62606957E-34 #J*s
H_PLANK = 4.135667516E-15 #eV*s
HC = H_PLANK*LIGHTC

BOREAS = "BOREAS"
CIRCE = "CIRCE"
NCD= "NCD"
XALOC = "XALOC"


#################################################################################

class EnergyID:
    """ """
    def __init__(self,bl_name=None):
        
        # Init constants
        if bl_name == CIRCE:
            self.initCIRCE()
        elif bl_name == BOREAS:
            self.initBOREAS()
        elif bl_name == NCD:
            self.initNCD()
        elif bl_name == XALOC:
            self.initXALOC()
        # Init harmonic and Offset
        self.harm = 5
        self.offset = 0
        self.OptimizeGap = 0.0
        self.OptimizePsi = 0.0
 
        
    def initCIRCE(self): 
        self.LambdaU =   0.06236
        self.Ax0 =  12.1836
        self.ax1 =  -80.483483
        self.ax2 =  187.3080884
        self.Az0 =  11.3026
        self.az1 =  -49.63614496
        self.az2 =  -28.35292685

        # OLD Eu62
        #self.LambdaU = 62.356*MILI;
        #self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        #self.ax1     = -7.34e-2/MILI
        #self.ax2     = + 7.66E-5/MILI**2
        #self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        #self.az1     = -5.000E-2/MILI
        #self.az2     = -1.84E-5/MILI**2

        self.Gamma   = 3/EMASS
        self.GapMin = 15.5*MILI
        self.GapMax = 275.5*MILI
        self.PhaseMin = -31.180*MILI
        self.PhaseMax = 31.180*MILI
        self.ErrThreshold = .1*MICRO
             
    def initBOREAS(self): 
        self.LambdaU =   0.07136
        self.Ax0 =  13.9369
        self.ax1 =  -73.08295964
        self.ax2 =  159.2223602
        self.Az0 =  12.6762
        self.az1 =  -43.65891256
        self.az2 =  -27.39457233

        ## OLD Eu71
        #self.LambdaU = 62.356*MILI;
        #self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        #self.ax1     = -7.34e-2/MILI
        #self.ax2     = + 7.66E-5/MILI**2
        #self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        #self.az1     = -5.000E-2/MILI
        #self.az2     = -1.84E-5/MILI**2

        self.Gamma   = 3/EMASS
        self.GapMin = 15.5*MILI
        self.GapMax = 273*MILI
        self.PhaseMin = -35.680*MILI
        self.PhaseMax = 35.680*MILI
        self.ErrThreshold = .1*MICRO

             
    def initNCD(self): 
        # specific for the ID
        self.LambdaU = 62.356*MILI;
        self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        self.ax1     = -7.34e-2/MILI
        self.ax2     = + 7.66E-5/MILI**2
        self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        self.az1     = -5.000E-2/MILI
        self.az2     = -1.84E-5/MILI**2
        self.Gamma   = 3/EMASS
        self.GapMin = 12*MILI
        self.GapMax = 250*MILI
        self.PhaseMin = -31.178*MILI
        self.PhaseMax = 31.178*MILI
        self.ErrThreshold = .1*MICRO

             
    def initXALOC(self): 
        # specific for the ID
        self.LambdaU = 62.356*MILI;
        self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        self.ax1     = -7.34e-2/MILI
        self.ax2     = + 7.66E-5/MILI**2
        self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        self.az1     = -5.000E-2/MILI
        self.az2     = -1.84E-5/MILI**2
        self.Gamma   = 3/EMASS
        self.GapMin = 12*MILI
        self.GapMax = 250*MILI
        self.PhaseMin = -31.178*MILI
        self.PhaseMax = 31.178*MILI
        self.ErrThreshold = .1*MICRO

    # DIRECT ## From Gap in mm to Energy in eV, Polarization angle
    def calculateEnergyPolarization(self, fGap = 0, fPhase = 0, harm = 5, offset = 0 ): 
        
        self.harm = harm
        self.offset = offset

        # We know gap and phase and we calculate Kz, Kx
        self.Kz, self.Kx  = self.calculateKfromGap(fGap,fPhase)
       
        # From Kz, Kx we calculate Energy in eV
        E1 = HC*(2.0*self.Gamma**2)/(self.LambdaU*(1.0+0.5*self.Kx**2+0.5*self.Kz**2))
        En = self.harm*E1 - self.offset

        # The Polarization angle
        if self.Kz!=0.0:
            Pn = m.atan(self.Kx/self.Kz)
        else:
            Pn = -1.0
       
        return En,Pn

    # DIRECT #
    def calculateKfromGap(self,GAP,PSI):
        Kz = (self.Az0*np.exp(self.az1*GAP + self.az2*GAP**2))*np.cos(m.pi*PSI/self.LambdaU)
        Kx = (self.Ax0*np.exp(self.ax1*GAP + self.ax2*GAP**2))*np.sin(m.pi*PSI/self.LambdaU)
        
        return Kz,Kx
    
    # INVERSE ## From Energy+Polarization to Gap in mm
    def calculateGapPhase(self, fEnergy = 0, fPolarization = 0, harm = 5, offset = 0 ): 
        try:
            self.harm = harm
            self.offset = offset
            # We know energy and polarization and we calculate Kx, Kz
            self.Kz, self.Kx = self.calculateKfromEnergy(fEnergy,fPolarization)
            #print "calculateGapPhase: Kz=%8.6f  Kx=%8.6f " % (self.Kz, self.Kx)

            if self.Kx==0:# linear horizontal
                GAP = self.calculate_gz(alpha=self.Kz/self.Az0)
                PSI = 0
                #return GAP, PSI
            elif self.Kz==0:# linear vertical
                GAP = self.calculate_gx(alpha=self.Kx/self.Ax0)
                PSI = 0.5*self.LambdaU
                #return GAP, PSI
            else:

                # this is to allow negative phase    
                XiSign = np.sign(self.Kx)    

                # set initial values
                G_L = self.GapMin; 
                G_Hx = (-self.ax1 - np.sqrt(self.ax1**2 + 4.0*self.ax2*np.log(np.abs(self.Kx)/self.Ax0)))/(2.0*self.ax2)
                G_Hz = (-self.az1 - np.sqrt(self.az1**2 + 4.0*self.az2*np.log(np.abs(self.Kz)/self.Az0)))/(2.0*self.az2)
                G_H = min(G_Hz,G_Hx) #-0.01*MICRO;
                
                PSI_ZL = XiSign*self.LambdaU/m.pi*np.real(np.arccos(self.Kz/(self.Az0*np.exp(self.az1*G_L + self.az2*G_L**2))))
                PSI_XL = self.LambdaU/m.pi*np.real(np.arcsin(self.Kx/(self.Ax0*np.exp(self.ax1*G_L + self.ax2*G_L**2))))
                DIF_L =   PSI_ZL - PSI_XL  
                
                PSI_ZH = XiSign*self.LambdaU/m.pi*np.real(np.arccos(self.Kz/(self.Az0*np.exp(self.az1*G_H + self.az2*G_H**2))))
                PSI_XH = self.LambdaU/m.pi*np.real(np.arcsin(self.Kx/(self.Ax0*np.exp(self.ax1*G_H + self.ax2*G_H**2))))
                DIF_H =   PSI_ZH - PSI_XH  
                
                # FB14Nov2013 to prevent unnecessary blocks
                ## if both extremes have the same sign, means that there is no solution    
                #if DIF_L*DIF_H > 0:
                    ##raise Exception("Error, there is no solution in the reachable gap interval")
                    #str_aux = "Error [4], there is no solution for Energy = %.3f and Polarization = %.6f" %(fEnergy, fPolarization)
                    #raise Exception(str_aux)
                    ##return  0,0
                
                # bucle to find the position  
                Err = max(np.abs(DIF_L),np.abs(DIF_H))
                if Err<=self.ErrThreshold:
                    #raise Exception("Error, there is no solution!!!")
                    str_aux = "Error [5], there is no solution for Energy = %.3f and Polarization = %.6f" %(fEnergy, fPolarization)
                    raise Exception(str_aux)
                
                G_New = -1
                #PSI_ZNew = -99999999999
                ct = 0
                while Err>self.ErrThreshold:
                    ct +=1
                    G_New = 0.5*(G_L + G_H)
                    #print "G_New",G_New
                    PSI_ZNew = XiSign*self.LambdaU/m.pi*np.real(np.arccos(self.Kz/(self.Az0*np.exp(self.az1*G_New + self.az2*G_New**2))))
                    PSI_XNew = self.LambdaU/m.pi*np.real(np.arcsin(self.Kx/(self.Ax0*np.exp(self.ax1*G_New + self.ax2*G_New**2))))
                    DIF_New =   PSI_ZNew - PSI_XNew
                    
                    if DIF_New*DIF_L >=0:
                        G_L = G_New
                        DIF_L = DIF_New
                    else:
                        G_H = G_New
                        DIF_H = DIF_New
                        
                    Err = max(np.abs(DIF_L),np.abs(DIF_H))
                    
                    if ct>1000: # this number is arbitrary, it should never happen, but we better have something
                        print "Error, the loop is not converging in 1000 iterations", Err
                        break 
                        raise Exception("Error, the loop is not converging in 1000 iterations")           
                        #return  0,0
                if ct >= 30:
                    print "Number of iterations", ct


                
                if G_New == -1:
                    raise Exception("Error, there is no solution!!!")

                GAP = G_New
                PSI = PSI_ZNew

            if GAP > self.GapMax:
                raise Exception("Error: the gap is greater than the maximum allowed") 
            elif GAP <self.GapMin:
                raise Exception("Error: the gap is less than the minimum allowed") 
            
            return GAP, PSI
        except Exception,e:
            #print "Error in calculateGapPhase algorithm:", str(e)
            #raise Exception("Check the range of values: "+str(e))
            raise
    

    # INVERSE #
    def calculateKfromEnergy(self,fEnergy,fPolarization):
        E1 = (fEnergy+self.offset)/self.harm
        K = np.real(np.sqrt(4.0*HC*self.Gamma**2/(self.LambdaU*E1)-2.0)) 

        Kx = K*np.sin(fPolarization)
        Kz = K*np.cos(fPolarization)
        return Kz,Kx

    def calculateGapPhaseFromOptimize(self,fEnergy,fPolarization, harm = 5, offset = 0 ): 
        
        self.harm = harm
        self.offset = offset
        self.Kz, self.Kx = self.calculateKfromEnergy(fEnergy,fPolarization)
        self.OptimizeGap = 0.0
        self.OptimizePsi = 0.0

        #if self.Kx == 0:# linear horizontal  
            #self.OptimizeGap = self.calculate_gz(alpha=self.Kz/self.Az0)
            #self.OptimizePsi = 0
        #elif self.Kz == 0:# linear vertical
            #self.OptimizeGap = self.calculate_gx(alpha=self.Kx/self.Ax0)
            #self.OptimizePsi = 0.5*self.LambdaU
        #else:
            #self.OptimizeGap, self.OptimizePsi = scipy.optimize.fsolve(self.func2, [0.01,0.001])
        
        self.OptimizeGap, self.OptimizePsi = scipy.optimize.fsolve(self.func2, [0.01,0.001])
        
        return self.OptimizeGap, self.OptimizePsi

    def func2(self, x):
        y = [self.Az0*np.exp(self.az1*x[0] + self.az2*x[0]**2)*np.cos(m.pi*x[1]/self.LambdaU) - self.Kz, 
             self.Ax0*np.exp(self.ax1*x[0] + self.ax2*x[0]**2)*np.sin(m.pi*x[1]/self.LambdaU) - self.Kx]
        return y

    def calculate_gx(self, alpha):#alpha=Kx/self.Ax0
        gx = (-self.ax1 - np.sqrt(self.ax1**2 + 4.0*self.ax2*np.log(alpha)))/(2.0*self.ax2) 
        return gx

    def calculate_gz(self, alpha):#alpha=Kz/self.Az0
        gz = (-self.az1 - np.sqrt(self.az1**2 + 4.0*self.az2*np.log(alpha)))/(2.0*self.az2) 
        return gz



###########################################################################


class EnergyIDPlus:
    """ """
    def __init__(self,bl_name=None):
        
        # Init constants
        if bl_name == CIRCE:
            self.initCIRCE()
        elif bl_name == BOREAS:
            self.initBOREAS()
        elif bl_name == NCD:
            self.initNCD()
        elif bl_name == XALOC:
            self.initXALOC()
        # Init harmonic and Offset
        self.harm = 5
        self.offset = 0
        self.OptimizeGap = 0.0
        self.OptimizePsi = 0.0   
        self.XiSign = np.sign(1)    
        self.parallelMode = True #True #False # True #False #
 
        
    def initCIRCE(self): 
        self.LambdaU =   0.06236
        self.Ax0 =  12.1836
        self.ax1 =  -80.483483
        self.ax2 =  187.3080884
        self.Az0 =  11.3026
        self.az1 =  -49.63614496
        self.az2 =  -28.35292685

        # OLD Eu62
        #self.LambdaU = 62.356*MILI;
        #self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        #self.ax1     = -7.34e-2/MILI
        #self.ax2     = + 7.66E-5/MILI**2
        #self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        #self.az1     = -5.000E-2/MILI
        #self.az2     = -1.84E-5/MILI**2

        self.Gamma   = 3/EMASS
        self.GapMin = 15.5*MILI
        self.GapMax = 275.5*MILI #210.0*MILI #
        self.PhaseMin = -31.180*MILI
        self.PhaseMax = 31.180*MILI
        self.ErrThreshold = .1*MICRO
             
    def initBOREAS(self): 
        self.LambdaU =   0.07136
        self.Ax0 =  13.9369
        self.ax1 =  -73.08295964
        self.ax2 =  159.2223602
        self.Az0 =  12.6762
        self.az1 =  -43.65891256
        self.az2 =  -27.39457233

        ## OLD EU71
        #self.LambdaU = 62.356*MILI;
        #self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        #self.ax1     = -7.34e-2/MILI
        #self.ax2     = + 7.66E-5/MILI**2
        #self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        #self.az1     = -5.000E-2/MILI
        #self.az2     = -1.84E-5/MILI**2

        self.Gamma   = 3/EMASS
        self.GapMin = 15.5*MILI
        self.GapMax = 273*MILI #225.0*MILI # 
        self.PhaseMin = -35.680*MILI
        self.PhaseMax = 35.680*MILI
        self.ErrThreshold = .1*MICRO

             
    def initNCD(self): 
        # specific for the ID
        self.LambdaU = 62.356*MILI;
        self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        self.ax1     = -7.34e-2/MILI
        self.ax2     = + 7.66E-5/MILI**2
        self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        self.az1     = -5.000E-2/MILI
        self.az2     = -1.84E-5/MILI**2
        self.Gamma   = 3/EMASS
        self.GapMin = 12*MILI
        self.GapMax = 250*MILI
        self.PhaseMin = -31.178*MILI
        self.PhaseMax = 31.178*MILI
        self.ErrThreshold = .1*MICRO

             
    def initXALOC(self): 
        # specific for the ID
        self.LambdaU = 62.356*MILI;
        self.Ax0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.9504
        self.ax1     = -7.34e-2/MILI
        self.ax2     = + 7.66E-5/MILI**2
        self.Az0     = ECHARGE/2/m.pi/EMASSKG/LIGHTC*self.LambdaU*1.934
        self.az1     = -5.000E-2/MILI
        self.az2     = -1.84E-5/MILI**2
        self.Gamma   = 3/EMASS
        self.GapMin = 12*MILI
        self.GapMax = 250*MILI
        self.PhaseMin = -31.178*MILI
        self.PhaseMax = 31.178*MILI
        self.ErrThreshold = .1*MICRO

    # DIRECT ## From Gap in mm to Energy in eV, Polarization angle
    def calculateEnergyPolarization(self, fGap = 0, fPhase = 0, harm = 5, offset = 0 ): 
        
        self.harm = harm
        self.offset = offset

        # We know gap and phase and we calculate Kz, Kx
        self.Kz, self.Kx  = self.calculateKfromGap(fGap,fPhase)
       
        # From Kz, Kx we calculate Energy in eV
        E1 = HC*(2.0*self.Gamma**2)/(self.LambdaU*(1.0+0.5*self.Kx**2+0.5*self.Kz**2))
        En = self.harm*E1 - self.offset

        # The Polarization angle
        if self.Kz!=0.0:
            #print "self.Kz, self.Kx", self.Kz, self.Kx
            Pn = m.atan(self.Kx/self.Kz)
        else:
            Pn = -1.0
       
        return En,Pn

    # DIRECT #
    def calculateKfromGap(self,GAP,PSI):
        Kz = (self.Az0*np.exp(self.az1*GAP + self.az2*GAP**2))*np.cos(m.pi*PSI/self.LambdaU)
        Kx = (self.Ax0*np.exp(self.ax1*GAP + self.ax2*GAP**2))*np.sin(m.pi*PSI/self.LambdaU)
        
        self.XiSign = np.sign(Kx)
        # If anti-parallel-mode the sin and cos appear with exponential 2
        if self.parallelMode == False:
            Kz = Kz*np.cos(m.pi*PSI/self.LambdaU)
            Kx = Kx*np.sin(m.pi*PSI/self.LambdaU)
        
        return Kz,Kx
    
    # INVERSE ## From Energy+Polarization to Gap in mm
    def calculateGapPhase(self, fEnergy = 0, fPolarization = 0, harm = 5, offset = 0 ): 
        try:
            self.harm = harm
            self.offset = offset
            # We know energy and polarization and we calculate Kx, Kz
            self.Kz, self.Kx = self.calculateKfromEnergy(fEnergy,fPolarization)
            #print "calculateGapPhase: Kz=%8.6f  Kx=%8.6f " % (self.Kz, self.Kx)

            if self.Kx==0:# linear horizontal
                GAP = self.calculate_gz(alpha=self.Kz/self.Az0)
                PSI = 0
                
                #return GAP, PSI
            elif self.Kz==0:# linear vertical
                GAP = self.calculate_gx(alpha=abs(self.Kx/self.Ax0))
                PSI = 0.5*self.LambdaU
                #return GAP, PSI
                #return GAP, PSI
            else:
                #if self.Kz<0.00001:
                    #print "ALERT Kz****************************************",self.Kz, fEnergy, fPolarization
                # this is to allow negative phase    
                #XiSign = np.sign(self.Kx)   #FB For antiparallel mode 

                # set initial values
                G_L = self.GapMin; 
                G_Hx = (-self.ax1 - np.sqrt(self.ax1**2 + 4.0*self.ax2*np.log(np.abs(self.Kx)/self.Ax0)))/(2.0*self.ax2)
                G_Hz = (-self.az1 - np.sqrt(self.az1**2 + 4.0*self.az2*np.log(np.abs(self.Kz)/self.Az0)))/(2.0*self.az2)
                G_H = min(G_Hz,G_Hx) #-0.01*MICRO;
                
                
                pCosZ = self.Kz/(self.Az0*np.exp(self.az1*G_L + self.az2*G_L**2))
                pSinX = self.Kx/(self.Ax0*np.exp(self.ax1*G_L + self.ax2*G_L**2))
                # If anti-parallel-mode the sin and cos appear with exponential 2
                if self.parallelMode == False:
                    pCosZ =  np.real(np.sqrt(pCosZ))
                    pSinX =  np.real(np.sqrt(pSinX))
                PSI_ZL = self.XiSign*self.LambdaU/m.pi*np.real(np.arccos(pCosZ))
                PSI_XL = self.LambdaU/m.pi*np.real(np.arcsin(pSinX))
                DIF_L =   PSI_ZL - PSI_XL  
                
                pCosZ = self.Kz/(self.Az0*np.exp(self.az1*G_H + self.az2*G_H**2))
                pSinX = self.Kx/(self.Ax0*np.exp(self.ax1*G_H + self.ax2*G_H**2))
                # If anti-parallel-mode the sin and cos appear with exponential 2
                if self.parallelMode == False:
                    pCosZ =  np.real(np.sqrt(pCosZ))
                    pSinX =  np.real(np.sqrt(pSinX))
                PSI_ZH = self.XiSign*self.LambdaU/m.pi*np.real(np.arccos(pCosZ))
                PSI_XH = self.LambdaU/m.pi*np.real(np.arcsin(pSinX))
                DIF_H =   PSI_ZH - PSI_XH  
                
                # FB14Nov2013 to prevent unnecessary blocks
                ## if both extremes have the same sign, means that there is no solution    
                #if DIF_L*DIF_H > 0:
                    ##raise Exception("Error, there is no solution in the reachable gap interval")
                    #str_aux = "Error [1], there is no solution for Energy = %.3f and Polarization = %.6f" %(fEnergy, fPolarization)
                    #raise Exception(str_aux)
                    ##return  0,0
                
                # bucle to find the position  
                Err = max(np.abs(DIF_L),np.abs(DIF_H))
                if Err<=self.ErrThreshold:
                    #raise Exception("Error, there is no solution!!!")
                    str_aux = "Error [2], there is no solution for Energy = %.3f and Polarization = %.6f" %(fEnergy, fPolarization)
                    raise Exception(str_aux)
                
                G_New = -1
                #PSI_ZNew = -99999999999
                ct = 0
                while Err>self.ErrThreshold:
                    ct +=1
                    G_New = 0.5*(G_L + G_H)
                    #print "G_New",G_New
                    pCosZ = self.Kz/(self.Az0*np.exp(self.az1*G_New + self.az2*G_New**2))
                    pSinX = self.Kx/(self.Ax0*np.exp(self.ax1*G_New + self.ax2*G_New**2))
                    # If anti-parallel-mode the sin and cos appear with exponential 2
                    if self.parallelMode == False:
                        pCosZ =  np.real(np.sqrt(pCosZ))
                        pSinX =  np.real(np.sqrt(pSinX))
                    PSI_ZNew = self.XiSign*self.LambdaU/m.pi*np.real(np.arccos(pCosZ))
                    PSI_XNew = self.LambdaU/m.pi*np.real(np.arcsin(pSinX))
                    DIF_New =   PSI_ZNew - PSI_XNew
                    
                    if DIF_New*DIF_L >=0:
                        G_L = G_New
                        DIF_L = DIF_New
                    else:
                        G_H = G_New
                        DIF_H = DIF_New
                        
                    Err = max(np.abs(DIF_L),np.abs(DIF_H))
                    
                    if ct>1000: # this number is arbitrary, it should never happen, but we better have something
                        print "Error, the loop is not converging in 1000 iterations", Err
                        break 
                        raise Exception("Error, the loop is not converging in 1000 iterations")           
                        #return  0,0
                #if ct >= 30:
                    #print "Number of iterations", ct


                
                if G_New == -1:
                    #raise Exception("Error, there is no solution!!!")
                    str_aux = "Error [3], there is no solution for Energy = %.3f and Polarization = %.6f" %(fEnergy, fPolarization)
                    raise Exception(str_aux)

                GAP = G_New
                PSI = PSI_ZNew#abs(PSI_ZNew)*self.XiSign#FB

            if GAP > self.GapMax:
                raise Exception("Error: the gap is greater than the maximum allowed") 
            elif GAP <self.GapMin:
                raise Exception("Error: the gap is less than the minimum allowed") 
            
            return GAP, PSI
        except Exception,e:
            #print "Error in calculateGapPhase algorithm:", str(e)
            #raise Exception("Check the range of values: "+str(e))
            raise
    

    # INVERSE #
    def calculateKfromEnergy(self,fEnergy,fPolarization):
        E1 = (fEnergy+self.offset)/self.harm
        K = np.real(np.sqrt(4.0*HC*self.Gamma**2/(self.LambdaU*E1)-2.0)) 

        Kx = K*np.sin(fPolarization)
        Kz = K*np.cos(fPolarization)
        self.XiSign = np.sign(Kx)
        
        #print "(inv) self.Kz, self.Kx", self.Kz, self.Kx
        return Kz,Kx

    def calculateGapPhaseFromOptimize(self,fEnergy,fPolarization, harm = 5, offset = 0 ): 
        
        self.harm = harm
        self.offset = offset
        self.Kz, self.Kx = self.calculateKfromEnergy(fEnergy,fPolarization)
        self.OptimizeGap = 0.0
        self.OptimizePsi = 0.0

        #if self.Kx == 0:# linear horizontal  
            #self.OptimizeGap = self.calculate_gz(alpha=self.Kz/self.Az0)
            #self.OptimizePsi = 0
        #elif self.Kz == 0:# linear vertical
            #self.OptimizeGap = self.calculate_gx(alpha=self.Kx/self.Ax0)
            #self.OptimizePsi = 0.5*self.LambdaU
        #else:
            #self.OptimizeGap, self.OptimizePsi = scipy.optimize.fsolve(self.func2, [0.01,0.001])
        
        self.OptimizeGap, self.OptimizePsi = scipy.optimize.fsolve(self.func2, [0.01,0.001])
        
        return self.OptimizeGap, self.OptimizePsi

    def func2(self, x):
        # If anti-parallel-mode the sin and cos appear with exponential 2
        if self.parallelMode == True:
            y = [self.Az0*np.exp(self.az1*x[0] + self.az2*x[0]**2)*np.cos(m.pi*x[1]/self.LambdaU) - self.Kz, 
                 self.Ax0*np.exp(self.ax1*x[0] + self.ax2*x[0]**2)*np.sin(m.pi*x[1]/self.LambdaU) - self.Kx]
        elif self.parallelMode == False:
            y = [self.Az0*np.exp(self.az1*x[0] + self.az2*x[0]**2)*np.cos(m.pi*x[1]/self.LambdaU)*np.cos(m.pi*x[1]/self.LambdaU) - self.Kz, 
                 self.Ax0*np.exp(self.ax1*x[0] + self.ax2*x[0]**2)*np.sin(m.pi*x[1]/self.LambdaU)*np.sin(m.pi*x[1]/self.LambdaU) - self.Kx]
        return y

    def calculate_gx(self, alpha):#alpha=Kx/self.Ax0
        gx = (-self.ax1 - np.sqrt(self.ax1**2 + 4.0*self.ax2*np.log(alpha)))/(2.0*self.ax2) 
        return gx

    def calculate_gz(self, alpha):#alpha=Kz/self.Az0
        gz = (-self.az1 - np.sqrt(self.az1**2 + 4.0*self.az2*np.log(alpha)))/(2.0*self.az2) 
        return gz


if __name__ == "__main__":
    ti = EnergyID(BOREAS)
    ti_Plus = EnergyIDPlus(BOREAS)
    ti.GapMax = 0.227000
    ti_Plus.GapMax = 0.227000
    #ti_Plus.parallelMode = False
   
    #GAP0,PSI0 = 0.025678, 0.018462
    #print "Initial Gap and Phase: GAP0=%8.1f um PSI0=%8.1f um "% (GAP0/MICRO, PSI0/MICRO)
    #ENERGY1, POL1 = ti.calculateEnergyPolarization(GAP0,PSI0, ti.harm, ti.offset)
    #print "Energy1=%8.1f eV Polarization1=%8.1f" % (ENERGY1, POL1)
    #GAP1,PSI1 = ti.calculateGapPhase(ENERGY1,POL1, 5,0)
    #print "GAP1=%8.1f um PSI1=%8.1f um Kz=%.6f, Kx=%.6f" % (GAP1/MICRO, PSI1/MICRO,ti.Kz,ti.Kx)
    #ENERGY2, POL2 = ti.calculateEnergyPolarization(GAP1,PSI1, , ti.harm, ti.offset)
    #print "Energy2=%8.1f eV Polarization2=%8.1f" % (ENERGY2, POL2)
   

    error_in_nicomize = error_in_optimization = error_in_nicomize_Plus = error_in_optimization_Plus = 0
    error_algorithmA = error_algorithmB = 0
    gap_min_error = ti.GapMax
    gap_min_error_Plus = ti_Plus.GapMax
    
    __RANDOM__ = True
    __RANDOM_0__ = False
    __RANDOM_MINUS__ = False
    __RANDOM_PLUS__ = False
    __FROM_ARRAY__ = False
    #arr = [[0.015000,0.015000],[0.1723453,0.000000],[0.1723453, 0.031178],[0.1460836,-0.0311584],[0.025933,-0.0000019],[0.1668406,0.0000108],[0.0460836,0.0311588]]  
    arr = [[0.045000,0.000000],[0.045000,0.023349],[0.045000,0.031180],
            [0.023000,0.000000],[0.023000,0.0205359],[0.023000,0.031179999]]  

    minimo1 = 300000.0
    maximo1 = 0.0
    number_of_intervals = 1000
    factor = 1.000
    
    for i in range(number_of_intervals):
            # (1) Initial Gap and Phase
        try:
            if __RANDOM__ == True:
                GAP0 =  factor*np.random.rand()*(ti.GapMax-ti.GapMin)+ti.GapMin
                PSI0 = 1.0*(np.random.rand()-0.5)*ti.LambdaU  
                try:
                  if ti.parallelMode == False:
                     PSI0 = abs(PSI0)
                 
                except Exception, e:
                  pass 
                try:
                  if ti_Plus.parallelMode == False:
                     PSI0 = abs(PSI0)
                 
                except Exception, e:
                  pass
            # -25um Y +25um
            elif __RANDOM_0__ == True:
                GAP0 =  factor*np.random.rand()*(ti.GapMax-ti.GapMin)+ti.GapMin
                PSI0 = (np.random.rand()-0.2)*0.000050      
            ## -pi+25um
            elif __RANDOM_MINUS__ == True:
                GAP0 =  np.random.rand()*(ti.GapMax-ti.GapMin)+ti.GapMin
                PSI0 = np.random.rand()*0.000025- 0.5*ti.LambdaU       
            ## -pi+25um
            elif __RANDOM_PLUS__ == True:
                GAP0 =  factor*np.random.rand()*(ti.GapMax-ti.GapMin)+ti.GapMin
                PSI0 =  0.5*ti.LambdaU - np.random.rand()*0.000025      
            ## Forced Gap AND Phase
            elif __FROM_ARRAY__ == True:
                GAP0 = arr[i][0]
                PSI0 = arr[i][1]

            # (2) Calculate Energy and Polarity
            ENERGY1, POL1 = ti.calculateEnergyPolarization(GAP0, PSI0, ti.harm, ti.offset)
            ENERGY1_Plus, POL1_Plus = ti_Plus.calculateEnergyPolarization(GAP0, PSI0, ti_Plus.harm, ti_Plus.offset)
            dE = ENERGY1 - ENERGY1_Plus
            dP = POL1 - POL1_Plus
            if dE != 0 or dP !=0:
                print "[A] The two algorithms give different values: dEnergy=%f, dPol=%f" %(dE, dP)
                error_algorithmA += 1
                    
            # (3a) Nico algorithm
            GAP2,PSI2 = ti.calculateGapPhase(ENERGY1,POL1, ti.harm, ti.offset)
            GAP2_Plus,PSI2_Plus = ti_Plus.calculateGapPhase(ENERGY1_Plus,POL1_Plus, ti_Plus.harm, ti_Plus.offset)
            dG = GAP2 - GAP2_Plus
            dP = PSI2 - PSI2_Plus
            if dG != 0 or dP !=0:
                print "[B] The two algorithms give different values: dGap=%f, dPhase=%f" %(dG, dP)
                error_algorithmB += 1
            if ENERGY1 < minimo1:
                    minimo1 = ENERGY1
            if ENERGY1 > maximo1:
                    maximo1 = ENERGY1
            
            #print "3: GAP2, PSI2   ", GAP2/MICRO,PSI2/MICRO
            if abs((GAP2-GAP0)/MICRO) >= 1.0 or  abs((PSI2-PSI0)/MICRO) >= 1.0:
                print "***Energy, POL", ENERGY1, POL1
                print "GAP=%8.1f (%8.1f) um PSI=%8.1f (%8.1f) um\n" % (GAP0/MICRO, GAP2/MICRO,PSI0/MICRO,PSI2/MICRO) 
                if GAP0 < gap_min_error:
		    gap_min_error = GAP0

                error_in_nicomize +=1
		
            if abs((GAP2_Plus-GAP0)/MICRO) >= 1.0 or  abs((PSI2_Plus-PSI0)/MICRO) >= 1.0:
                print "***Energy_Plus, POL_Plus", ENERGY1_Plus, POL1_Plus
                print "GAP=%8.1f (_Plus %8.1f) um PSI=%8.1f (_Plus %8.1f) um\n" % (GAP0/MICRO, GAP2/MICRO,PSI0/MICRO,PSI2/MICRO) 
                if GAP0 < gap_min_error_Plus:
		    gap_min_error_Plus = GAP0
               
                error_in_nicomize_Plus +=1

            # (3b) scipy algorithm
            GAP3,PSI3 =ti.calculateGapPhaseFromOptimize(ENERGY1,POL1, ti.harm, ti.offset)
            GAP3_Plus,PSI3_Plus =ti_Plus.calculateGapPhaseFromOptimize(ENERGY1_Plus,POL1_Plus, ti_Plus.harm, ti_Plus.offset)

            if abs((GAP3 - GAP0)/MICRO) > 1.0 or abs((PSI3 - PSI0)/MICRO) > 1.0:
                error_in_optimization += 1
	
            if abs((GAP3_Plus - GAP0)/MICRO) > 1.0 or abs((PSI3_Plus - PSI0)/MICRO) > 1.0:
                error_in_optimization_Plus += 1
		
		
            if __FROM_ARRAY__ == True:
                print "[__FROM_ARRAY__ %.0f] Energy=%8.6f Pol=%8.6f GAP=%8.1f (%8.1f) um PSI=%8.1f (%8.1f) um Kz=%.6f, Kx=%.6f" % (i, ENERGY1, POL1, GAP0/MICRO, GAP2/MICRO, PSI0/MICRO, PSI2/MICRO,ti.Kz,ti.Kx)
        except Exception, e:
            print str(e)
            
    if number_of_intervals > 0:
        # (4) Results
        print "\nERRORS: Nicomize %.0f Optimize %.0f" %(error_in_nicomize, error_in_optimization)
        print "ERRORS: Nicomize_Plus %.0f Optimize_Plus %.0f" %(error_in_nicomize_Plus, error_in_optimization_Plus)
	print "GapMinError",   gap_min_error/MICRO 
	print "GapMinError_Plus",   gap_min_error_Plus /MICRO
	
        print "\nERRORS in algorithm A (%d) B (%d)" %(error_algorithmA, error_algorithmB)
	




