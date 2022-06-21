from openpyxl import load_workbook, Workbook
import numpy as np
from commons import genUserDateList as DL
import os,sys
from commons.utils import addsep

xlsfile=os.getenv("RIVERDATA")
if xlsfile is None: 
    print("Error: Environment variables RIVERDATA - indicating the name of xls river file - must be defined.")
    sys.exit(1)

meteodir=os.getenv("RIVERMETEODIR")
if meteodir is None: 
    print("Error: Environment variables RIVERMETEODIR - indicating where to find discharge files - must be defined.")
    sys.exit(1)

if len(meteodir) > 1: meteodir=addsep(meteodir)

wb = load_workbook(filename=xlsfile, read_only=False,data_only=True)
sh_var = wb['biogeochemical_variable']
sh_loc = wb['river_locations']


#TIMELIST=['20011224-12:00:00', '20011228-12:00:00']
#DL.readTimeString(TIMELIST[0])


# read values of variable to be used at river location
NVAR=sh_var.max_row-1 # 51 + 1
IDvar=np.zeros(NVAR)
#CONCvar=np.zeros(NVAR)
NAMEvar=[]
UNITvar=[]
for row_index in range(NVAR):
    IDvar[row_index]=  sh_var.cell(row=row_index+2,column=1).value
    NAMEvar.append(str(sh_var.cell(row=row_index+2,column=2).value))
    UNITvar.append(str(sh_var.cell(row=row_index+2,column=3).value))
    #CONCvar[row_index]=sh_var.cell(row_index+1,3).value


class River():
    def __init__(self,ROW):
        ''' ROW is a row of an Excel file ordered in the same way of this contructor'''
        self.ind         = int(ROW[0])
        self.name        = str(ROW[1])
        self.type_of_ave = str(ROW[2])
        self.iLon        = int(ROW[3])
        self.iLat        = int(ROW[4])
        self.side        = str(ROW[5])
        self.nVcells     = int(ROW[6])
        self.nHcells     = int(ROW[7])
        self.Q_mean      = ROW[8]
        self.applied_ratio=False
        self.Conc = np.zeros((NVAR,),np.float32)
        self.sali = 15.0
        for ivar in range(NVAR):
            self.Conc[ivar]=ROW[9+ivar]

    def get_ratio(self):
        ''' Return ratio between actual mean discharge and the
        climatological one read from xls
        '''
        ratio = np.nan
        filename = meteodir + self.name + ".txt"
        if os.path.exists(filename):
            _,actual_Q = self.read_Discharge_file(filename)
            ratio = actual_Q.mean()/self.Q_mean
        return ratio

    def apply_ratio(self, ratio) :
        if not self.applied_ratio:
            self.Q_mean = self.Q_mean*ratio
            self.applied_ratio = True


    def getTimeDischarge(self,timelist):
        '''Behaviour climatologic if river is classified as 'yearly clim.'
        or if is not possible to find the file having the same name of the river + '.txt'
        '''
          
        if self.type_of_ave == 'yearly clim.' :
            return self.getClimTimeDischarge(timelist)
        else:
            filename = meteodir + self.name + ".txt"
            if os.path.exists(filename):
                print(" ****************  Found  " + filename)
                TLfound,Q = self.read_Discharge_file(filename)
                return self.Time_interp(Q, TLfound, timelist)
            else:
                print("Warning : " + filename + " file not found. Climatological data will be used instead. ")
                return self.getClimTimeDischarge(timelist)

    def read_Discharge_file(self, filename):
        ''' Reads file in the format yyyymmdd-hh:MM:ss Q
        '''
        DT=[('date','U17'),('Q',np.float32)]
        A =np.loadtxt(filename, dtype=DT)
        return A['date'],A['Q']
    
    
    def Time_interp(self,Q,timelist_in, timelist_out):
        nFrames_in = len(timelist_in)
        nFrames_out = len(timelist_out)
        Tin  = np.zeros((nFrames_in,),np.float32)
        Tout = np.zeros((nFrames_out,),np.float32)
        
        for i in range(nFrames_in):  Tin[ i] = float(DL.readTimeString(timelist_in[ i]).strftime("%s"))        
        for i in range(nFrames_out): Tout[i] = float(DL.readTimeString(timelist_out[i]).strftime("%s"))
        return np.interp(Tout,Tin,Q)
            
    def getClimTimeDischarge(self,timelist):
        '''
        Discharges are calculated by a formula
        a sinusoid  - having T=365/2 days, min=0.25, max=1.75 at julian day 120 - 
        modulating mean annual discharge provided in xls file. 
        '''
        nFrames = len(timelist)
        Q = np.zeros((nFrames,),np.float32)
        for it, timestring in enumerate(timelist):
            D=DL.readTimeString(timestring)
            julian = int(D.strftime("%j"))
            Modulation_Factor = 1.0 + 0.75*np.cos(2*(2*np.pi*(julian-120.)/365))
            Q[it] = self.Q_mean* Modulation_Factor 
        return Q
    def getTimeTemperature(self,timelist):
        ''' 
        Temperatures are calculated by a formula, a sinusoid having T=365 days, min = 5 deg, max=15 deg at julian day 212.
        '''
        nFrames = len(timelist)
        T = np.zeros((nFrames,),np.float32)
        for it, timestring in enumerate(timelist):
            D=DL.readTimeString(timestring)
            julian = int(D.strftime("%j"))
            T[it] = 10.0 + 5*np.cos((2*np.pi*(julian-212.)/365))
        return T

def get_list(f):
    L = []
    for c in f :
        if isinstance(c, tuple):
            v = c[0].value
        else:
            v=c.value  
        if v is not None:
            try:
                a=float(v)
            except:
                a=str(v)
            L.append(a)
    return L
f=sh_loc['B3:B100']

column_list=get_list(f)
nRivers=int(max(column_list))
 

RATIOS = np.zeros((nRivers), np.float32)
for iRiver in range(nRivers):
    irow=4+iRiver
    f=sh_loc[irow]
    row_list= get_list(f)
    R = River(row_list)
    RATIOS[iRiver] = R.get_ratio()


actual_vs_clim_ratio  = np.nanmean(RATIOS)
if np.isnan(actual_vs_clim_ratio): actual_vs_clim_ratio = 1.0
print("Applying ratio : ", actual_vs_clim_ratio)

RIVERS=[]

for iRiver in range(nRivers):
    irow=4+iRiver
    f=sh_loc[irow]
    row_list= get_list(f)
    R = River(row_list)
    R.apply_ratio(actual_vs_clim_ratio)
    RIVERS.append(R)
    
#for iRiver in range(nRivers): print RIVERS[iRiver].name


def get_RiverBFM_Data(lato,varname):
    '''
       Concentration of Biogeochemical variables is intended not to change in time
       Returns : 
       integer array Lon_Ind[nRivers] of Longitude Indexes
       integer array Lat_Ind[nRivers] of Latitude  Indexes
       float array  OUT[nRiver] for the required variable
       
    lato can be 'E','S','W' or 'N' 
    varname is a BFM variable such as 'N1p'
    '''
    
    nLato=0
    for R in RIVERS:
        if R.side ==  lato : nLato = nLato+1

    Lon_Ind = np.zeros((nLato),np.int32)
    Lat_Ind = np.zeros((nLato),np.int32)
    conc = np.zeros((nLato,),np.float32)
    
    counter=0
    for R in RIVERS:
        if R.side == lato:
            Lon_Ind[counter] = R.iLon -1
            Lat_Ind[counter] = R.iLat -1
                        
            for i in range(NVAR):
                if NAMEvar[i] ==varname : break 
            conc[counter] = R.Conc[i]
            counter=counter+1
    return Lon_Ind,Lat_Ind,conc


def get_RiverPHYS_Data(lato,varname,timelist,Mask):
    '''
    
    Arguments:
    * lato     * string, can be 'E','S','W' or 'N'
    * varname  * string,  is a PHYS variable : 'T','S','V'
    * timelist * is a list of date17 strings
    * Mask     * a general.mask object
    
    Returns :
       integer array Lon_Ind[nRivers] of Longitude Indexes
       integer array Lat_Ind[nRivers] of Latitude  Indexes
       float array  OUT[nRiver,nTimes] for the required variable
       
    '''
    
    nFrames = len(timelist)
    nLato=0
    for R in RIVERS:
        if R.side ==  lato : nLato = nLato+1    

    Lon_Ind = np.zeros((nLato),np.int32)
    Lat_Ind = np.zeros((nLato),np.int32)
    OUT = np.zeros((nLato,nFrames),np.float32)
    
    counter=0
    for R in RIVERS:
        if R.side == lato:
            Lon_Ind[counter] = R.iLon -1
            Lat_Ind[counter] = R.iLat -1
                        
            if varname == 'T' :
                OUT[counter,:] = R.getTimeTemperature(timelist) 
            if varname == 'S':
                OUT[counter,:] = R.sali
            if varname == 'V':
                denom = R.nHcells* Mask.CellArea(lato,R.nVcells)
                OUT[counter,:] = R.getTimeDischarge(timelist)/denom
            counter=counter+1
    return Lon_Ind,Lat_Ind,OUT



if __name__ == "__main__":
    timelist=['20220614-12:00:00']
    from general import mask
    Mask = mask('/g100_work/OGS_prodC/MIT/V1M-dev/V1/devel/wrkdir/BC_IC/mask.nc')
    A=get_RiverPHYS_Data('W','V',timelist,Mask)

