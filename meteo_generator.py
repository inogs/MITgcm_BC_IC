import argparse



def argument():
    parser = argparse.ArgumentParser(description = '''
    Generates 8 files, one for each meteo forcing condition. Hourly data.
    File list is: 
    BC_atemp,
    BC_aqh,
    BC_uwind, 
    BC_vwind, 
    BC_apress, 
    BC_swflux, 
    BC_lwflux, 
    BC_precip.
    
    ''')
    
    parser.add_argument(   '--outmaskfile', '-m',
                                type = str,
                                required = True,
                                help = '/some/path/outmask.nc')
    parser.add_argument(   '--outputdir',"-o",
                                type = str,
                                required = True,
                                help = '/some/path/')

    parser.add_argument(    '--timelist',"-t", 
                                type = str,
                                required = True,
                                help = ''' Path of the file containing times meteo data.''' )
    parser.add_argument(   '--inputdir', '-i',
                                type = str,
                                default = None,
                                required = True,
                                help ='''/some/path/  Directory containg files to interpolate. 
                                '''
                                )
      
    parser.add_argument(   '--nativemask',
                                type = str,
                                default = None,
                                required = True,
                                help = '''NetCDF File name of the mask on meteo data are defined.
                                ''')    
    return parser.parse_args()

args = argument()

from general import *
from commons import genUserDateList as DL
from scipy.interpolate import griddata




def getFilename(INPUTDIR, date17):
    '''Returns: 
    filename if filename exist, None if not.
    Searches for names with hours <=24.
    If file not found it searches for hours > 24, in forecast
    '''
    D= DL.readTimeString(date17)
    hours = D.hour
    for days in range(0,4):
        d = D - DL.relativedelta(days = days)
        hours = D.hour + 24*days
        filename =  "%sasogs_%s00+00%02d.asc"  %( INPUTDIR, d.strftime("%Y%m%d"), hours)
        if os.path.exists(filename): return filename
    print("ERROR: file not found: " + filename)
    return None

    
    
    


def writeCheckFile():
    checkfile = OUTPUTDIR +  "CHECK/" + var + "." + time + ".nc"
    Mcheck = Minterp.copy()
    missing_value=1.e+20
    Mcheck[~tmask2]=missing_value
            
    NCout =NC.netcdf_file(checkfile,"w")    
    NCout.createDimension("Lon"  ,Mask2.Lon.size)
    NCout.createDimension("Lat"  ,Mask2.Lat.size)
    
    ncvar = NCout.createVariable(var,'f',('Lat','Lon'))
    setattr(ncvar, 'missing_value', missing_value) 
    ncvar[:] = Mcheck
    NCout.close()

Mask1 = mask(args.nativemask)
Mask2 = mask(args.outmaskfile)


LON1,LAT1 = np.meshgrid(Mask1.Lon, Mask1.Lat)
nWP = Mask1.tmask.sum()
Points1 = np.zeros((nWP,2), np.float32)
Points1[:,0] = LON1[Mask1.tmask]
Points1[:,1] = LAT1[Mask1.tmask]

LON2,LAT2 = np.meshgrid(Mask2.Lon,Mask2.Lat)
LON2=LON2.astype(np.float32)
LAT2=LAT2.astype(np.float32)
tmask2 = Mask2.tmask[0,:,:]

TIMELIST=file2stringlist(args.timelist)
INPUTDIR=addsep(args.inputdir)
OUTPUTDIR=addsep(args.outputdir)

os.system("mkdir -p " + OUTPUTDIR)
os.system("mkdir -p " + OUTPUTDIR + "CHECK") 

VARS=['Lat','Lon','atemp','aqh','uwind', 'vwind', 'apress', 'swflux', 'lwflux', 'precip' ]
DType=[]
for var in VARS: DType.append((var,np.float32))

nFrames = len(TIMELIST)

jpi = Mask1.Lon.size
jpj = Mask1.Lat.size
M = np.zeros((nFrames,jpj,jpi),dtype=DType)

for it,time in enumerate(TIMELIST):
    filename = getFilename(INPUTDIR, time)
    print(time, filename)
    ARSO=np.loadtxt(filename,dtype=DType)
    ARSO.resize((jpj,jpi))
    M[it,:,:] = ARSO

# conversion   ----------------------
M['swflux'] =  M['swflux']/3600.
M['lwflux'] = -M['lwflux']/3600.
M['precip'] =  M['precip']/(3600*1000)
#------------------------------------

for var in ['swflux','lwflux','precip']:         # Provided as cumulated
    print('Differentiating '+var)
    DIFFERENTIAL = np.diff(M[var],n=1,axis=0)
    ii = DIFFERENTIAL < 0 ; DIFFERENTIAL[ii] = 0  # precaution 
    M[var][1:,:,:] = DIFFERENTIAL
    M[var][0 ,:,:] = DIFFERENTIAL[0,:,:] 

M['swflux'] =  -M['swflux']  # because in ocean model swflux is negative

for var in VARS[2:]:
    outBinaryFile=OUTPUTDIR + "BC_" + var
    print("writing " + outBinaryFile)
    F = open(outBinaryFile,'wb')
    for it, time  in enumerate(TIMELIST):
        FrameMatrix = M[var][it,:,:].copy()
        
        
        #import pylab as pl        
        #pl.figure(1); pl.imshow(FrameMatrix); pl.colorbar(); pl.gca().invert_yaxis() ; pl.show(block=False)
        #pl.figure(2); pl.imshow(Mask1.tmask); pl.colorbar(); pl.gca().invert_yaxis() ; pl.show(block=False)
        #FM = FrameMatrix.copy()
        #FM[~Mask1.tmask] = np.NaN
        #pl.figure(3); pl.imshow(FM); pl.colorbar(); pl.gca().invert_yaxis() ; pl.show(block=False)
        #import sys; sys.exit()
        Nearest = griddata(Points1, FrameMatrix[Mask1.tmask], (LON2,LAT2),method='nearest')
        Linear  = griddata(Points1, FrameMatrix[Mask1.tmask], (LON2,LAT2),method='linear').astype(np.float32)
        Linear_Failed = np.isnan(Linear)
        Linear[Linear_Failed]=Nearest[Linear_Failed]
        Minterp = Linear
        writeCheckFile()
          
        F.write(Minterp)
    F.write(Minterp)
    F.write(Minterp)
    F.write(Minterp)
    F.close()



