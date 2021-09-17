import argparse



def argument():
    parser = argparse.ArgumentParser(description = '''
        Creates ready OBC files for MITgcm only for BIO variables.
    A boundary condition can derive from a previous run, often based on other mask, 
    in that case BC_files_gen.py needs the directory containing NetCDF files of slices, 
    and the corresponding nativemask, and performs a linear interpolation.
    If the boundary condition does not require a previous run 
    (e.g. if it is on land) the interpdir argument must not be given.
    In any case, on each boundary the river conditions will be imposed. 
    River data are provided by an xls file, whose name must be
    defined in an environment variable called RIVERDATA.
    
    MITgcm needs the OBC for all the time of run; then, timelist argument must be 
    defined having in mind the times of the MITgcm run.
    
    ''')

    parser.add_argument(   '--outmaskfile', '-m',
                                type = str,
                                required = True,
                                help = '/some/path/outmask.nc')
    parser.add_argument(   '--outputdir',"-o",
                                type = str,
                                required = True,
                                help = '/some/path/')
    parser.add_argument(   '--side',"-s",
                                type = str,
                                required = True,
                                choices = ["E","W","S","N"]) 
    parser.add_argument(    '--timelist',"-t", 
                                type = str,
                                required = True,
                                help = '/some/path/filename' ) 
    parser.add_argument(   '--interpdir', '-i',
                                type = str,
                                default = None,
                                help ='''/some/path/SLICES/ADRI/NORTH/  Directory containg files to interpolate. 
                                         This argument is optional'''
                                )
    parser.add_argument(   '--nativemask',
                                type = str,
                                help = '''NetCDF File name of the mask on which slices are defined.
                                This parameter is read only if INTERPDIR is given.                                
                                ''')    
        
    return parser.parse_args()

args = argument()
from general import *
import read_XLS
from commons import netcdf4



side   = args.side;
Mask2  = mask(args.outmaskfile)
tmask2 = side_tmask(side,Mask2)
if args.interpdir :
    INTERPDIR = addsep(args.interpdir)
    Mask1 = mask(args.nativemask)
    tmask1 = side_tmask(side,Mask1)


OUTPUTDIR = addsep(args.outputdir)
TIMELIST   = file2stringlist(args.timelist)       
os.system("mkdir -p " + OUTPUTDIR)
os.system("mkdir -p " + OUTPUTDIR + "CHECK")  



def writeCheckFile():
    checkfile = OUTPUTDIR +  "CHECK/OBC_"  + side + "." + t + "." + var + ".nc"
    Mcheck = M.copy()
    if args.interpdir:
        missing_value=1.e+20
        #Mcheck[~tmask2]=missing_value
    else:
        missing_value=0
        
    NCout =NC.netcdf_file(checkfile,"w")    
    NCout.createDimension("Lon"  ,Mask2.Lon.size)
    NCout.createDimension("Lat"  ,Mask2.Lat.size)
    NCout.createDimension("Depth",Mask2.jpk)
    if side is "E" or side is "W":    
        ncvar = NCout.createVariable(var,'f',('Depth','Lat'))
    if side is "N" or side is "S":
        ncvar = NCout.createVariable(var,'f',('Depth','Lon'))
    setattr(ncvar, 'missing_value', missing_value) 
    ncvar[:] = Mcheck
    NCout.close()



    
for var in ["T","S","U","V"]: 
    if var is "U":
        if side in ["E","W"]: 
            Lon_Ind,Lat_Ind,C = read_XLS.get_RiverPHYS_Data(side, 'V', TIMELIST,Mask2)
            #C = Q/Mask2.CellArea(side);
            if side is "E" : C = -C
        else:
            C[:,:]=0
    if var is "V":
        if side in ["S","N"]:
            Lon_Ind,Lat_Ind,C = read_XLS.get_RiverPHYS_Data(side, 'V', TIMELIST,Mask2)
            #C = Q/Mask2.CellArea(side);
            if side is "N" : C = -C
        else:
            C[:,:]=0
    if var in ["T","S"]:
        Lon_Ind,Lat_Ind,C = read_XLS.get_RiverPHYS_Data(side, var, TIMELIST,Mask2)
       
    outBinaryFile = OUTPUTDIR +'OBC_'+ side + "_" + var + ".dat"
    print(outBinaryFile)
    F = open(outBinaryFile,'wb')
            
    nSideRivers = Lon_Ind.size
    for it, t in enumerate(TIMELIST):
        M = zeroPadding(side,Mask2)
        
        if args.interpdir:
            filename = INTERPDIR +  t[:8] + "_" + NetCDF_phys_Files[var] + ".nc"
            if side in ["N","S"]:
                B = netcdf4.readfile(filename, NetCDF_phys_Vars[var])[0,:Mask1.jpk,0,:]
                B[~tmask1]=1.e+20
            if side in ["E","W"]:
                B = netcdf4.readfile(filename, NetCDF_phys_Vars[var])[0,:Mask1.jpk,:,0]
                B[~tmask1]=1.e+20
            B[B>1.e+19] = np.NaN
            M = vertical_plane_interpolator(Mask2,Mask1,B,side)
                            
        for iRiver in range(nSideRivers):
            if side is 'E' or side is 'W':            
                M[:,Lat_Ind[iRiver]] = C[iRiver,it]
            if side is "S" or side is "N":
                M[:,Lon_Ind[iRiver]] = C[iRiver,it]
        #writeCheckFile()            
        F.write(M)
    F.write(M)
    F.write(M)
    F.write(M)
    F.close()    
   
 
