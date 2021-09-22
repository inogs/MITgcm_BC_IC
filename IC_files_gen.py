import argparse


def argument():
    parser = argparse.ArgumentParser(description = '''Creates ready IC files for MITgcm 
                               both physical and biogeochemical. Since input data come from other external run,
                               a linear interpolation is performed. 
                               If argument MODELVARLIST is given with biogeochemical variable list, IC for these BIO variables
                               will be created. Else, physical IC will be created.
                               
                               ''')
    parser.add_argument(   '--inputdir', '-i',
                                type = str,
                                required = True,
                                help ='/some/path/'
                                )
    
    parser.add_argument(   '--outmaskfile', '-m',
                                type = str,
                                required = True,
                                help = '/some/path/outmask.nc')
    parser.add_argument(   '--outputdir',"-o",
                                type = str,
                                required = True,
                                help = '/some/path/')
    parser.add_argument(   '--nativemask',
                                type = str,
                                required = True,
                                help = '''NetCDF File name of the mask on which inputs are defined.
                                ''')
    parser.add_argument(    '--modelvarlist',"-v", 
                                type = str,
                                default = None,
                                help = '''/some/path/filename,
                                Do not define it to get physical IC.''' )
    parser.add_argument(    '--time',"-t", 
                                type = str,
                                required = True,
                                help = '''/some/path/filename.              
                                
                                A file with an only time, the restart time
                                       ''' )    
        
    return parser.parse_args()

from general import mask, space_intepolator_griddata,NetCDF_phys_Files,NetCDF_phys_Vars
from commons.utils import addsep, file2stringlist
import scipy.io.netcdf as NC
from commons import netcdf4
import os
import numpy as np

try :
    from mpi4py import MPI
    comm  = MPI.COMM_WORLD
    rank  = comm.Get_rank()
    nranks = comm.size 
except:
    rank   = 0
    nranks = 1



def writeCheckFile():
    Mcheck = M.copy()
    #Mcheck[~Mask2.tmask] = 1.0e+20

    checkfile = OUTPUTDIR +"CHECK/" + "IC_" + var + ".nc"    
    NCout =NC.netcdf_file(checkfile,"w")    
    NCout.createDimension("Lon"  ,Mask2.Lon.size)
    NCout.createDimension("Lat"  ,Mask2.Lat.size)
    NCout.createDimension("Depth",Mask2.jpk)    
    ncvar = NCout.createVariable(var,'f',('Depth','Lat','Lon'))
    setattr(ncvar, 'missing_value', 1.e+20) 
    ncvar[:] = Mcheck
    NCout.close()


args = argument()

INPUTDIR  = addsep(args.inputdir)
OUTPUTDIR = addsep(args.outputdir)
os.system("mkdir -p " + OUTPUTDIR)
os.system("mkdir -p " + OUTPUTDIR + "CHECK")
TIMELIST   = file2stringlist(args.time)
Mask1 = mask(args.nativemask)
Mask2 = mask(args.outmaskfile)


if args.modelvarlist:
    MODELVARS  = file2stringlist(args.modelvarlist)

    for var in MODELVARS[rank::nranks]:
        inputfile     = INPUTDIR + "ave." + TIMELIST[0] + "." + var + ".nc"    
        outBinaryFile = OUTPUTDIR + 'IC_' + var + ".dat"
        print("rank %d working on %s" %(rank, outBinaryFile))
        B=netcdf4.readfile(inputfile, var)[0,:]
        #B[~Mask1.tmask] = np.NaN
        
        M = space_intepolator_griddata(Mask2,Mask1,B)
        
        writeCheckFile()
        F = open(outBinaryFile,'wb')        
        for jk in range(Mask2.jpk) : F.write(M[jk,:,:])
        F.close()
    
else:
    MODELVARS = ["U","V","T","S"]
    for var in MODELVARS[rank::nranks]:        
        inputfile=INPUTDIR + TIMELIST[0][:8] + "_" + NetCDF_phys_Files[var] + ".nc"
        outBinaryFile = OUTPUTDIR + "IC_" + var + ".dat"
        print("rank %d working on %s" %(rank, outBinaryFile))

        B = netcdf4.readfile(inputfile, NetCDF_phys_Vars[var])[0,:Mask1.jpk,:,:]
        B[~Mask1.tmask] = np.NaN
        #B[B>1.e+19]  = np.NaN
    
        M = space_intepolator_griddata(Mask2,Mask1,B)
        writeCheckFile()
        F = open(outBinaryFile,'wb')
        for jk in range(Mask2.jpk) : F.write(M[jk,:,:])
        F.close()
        
        

