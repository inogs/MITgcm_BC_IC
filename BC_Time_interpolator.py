import argparse


def argument():
    parser = argparse.ArgumentParser(description = '''
    Interpolates in time producing ave files. Reads timelist files
    
    At present is parallelized over variable list.
    '''
    )
    parser.add_argument(   '--inputdir', '-i',
                                type = str,
                                required=True,
                                help = '/some/path/MODEL/AVE_FREQ_1/')

    parser.add_argument(   '--outputdir',"-o",
                                type = str,
                                required=True,
                                help = '/some/path/')
    parser.add_argument(   '--inputtimefile',"-if",
                                type = str,
                                required=True,
                                help = '/some/path/filename ')
    parser.add_argument(   '--outputtimefile',"-of",
                                type = str,
                                required=True,
                                help = '/some/path/filename ')
    parser.add_argument(    '--varlist',"-v", 
                                type = str,
                                required=True,
                                help = '/some/path/filename' )
    parser.add_argument(   '--side',"-s",
                                type = str,
                                required = True,
                                choices= ["E",'W','S','N'])    
    parser.add_argument(   '--maskfile', '-m',
                                type = str,
                                required = True,
                                help = '/some/path/mask.nc')    
    
    
    
    return parser.parse_args()

from general import *
from commons import genUserDateList as DL

try :
    from mpi4py import MPI
    comm  = MPI.COMM_WORLD
    rank  = comm.Get_rank()
    nranks = comm.size 
except:
    rank   = 0
    nranks = 1
    
args = argument()
side   = args.side;
INPUT_DIR    = addsep(args.inputdir)
OUTPUTDIR    = addsep(args.outputdir)


dateFormat="%Y%m%d-%H:%M:%S"
os.system("mkdir -p " + OUTPUTDIR)


Input_TIMELIST=[]
for line in file2stringlist(args.inputtimefile):
    Input_TIMELIST.append(DL.readTimeString(line))
OutputTIMELIST=[]
for line in file2stringlist(args.outputtimefile):
    OutputTIMELIST.append(DL.readTimeString(line))






def Load_Data(DATADIR, TimeList,before,after,var):
    Before_date17 = TimeList[before].strftime(dateFormat)
    After__date17 = TimeList[after ].strftime(dateFormat)
    

    Before_File = "ave." + Before_date17 + "." + var + ".nc"
    After__File = "ave." + After__date17 + "." + var + ".nc"
    print "loading " + Before_File, After__File, 'for ', var
    
    ncB = NC.netcdf_file(DATADIR + Before_File,'r')
    ncA = NC.netcdf_file(DATADIR + After__File,'r')
    
    Before_Data = ncB.variables[var].data.copy()
    After__Data = ncA.variables[var].data.copy()
    
    ncA.close()
    ncB.close()
    return Before_Data, After__Data



Mask = mask(args.maskfile)


VARLIST=file2stringlist(args.varlist)
for var in VARLIST[rank::nranks]:
    BEFORE, AFTER,T_interp = Time_Interpolation(OutputTIMELIST[0],Input_TIMELIST)
    Before_DATA, After__DATA = Load_Data(INPUT_DIR, Input_TIMELIST, BEFORE, AFTER,var)
    tmask=Before_DATA > 1.e+19;

    
    
    
    for t in OutputTIMELIST:
        outfile = OUTPUTDIR  +  "ave." + t.strftime(dateFormat) +"." + var + ".nc"
        print outfile
        
        before,after,T_interp = Time_Interpolation(t,Input_TIMELIST)
        if before>BEFORE:
            BEFORE=before
            AFTER=after
            Before_DATA, After__DATA = Load_Data(INPUT_DIR, Input_TIMELIST, BEFORE, AFTER,var)
        Actual = (1-T_interp)*Before_DATA + T_interp*After__DATA
        Actual[tmask] = 1.e+20
        
        
        NCout =NC.netcdf_file(outfile,"w")    
        NCout.createDimension("Lon"  ,Mask.Lon.size)
        NCout.createDimension("Lat"  ,Mask.Lat.size)
        NCout.createDimension("Depth",Mask.jpk)
        if side is "E" or side is "W":    
            ncvar = NCout.createVariable(var,'f',('Depth','Lat'))
        if side is "N" or side is "S":
            ncvar = NCout.createVariable(var,'f',('Depth','Lon'))
        setattr(ncvar, 'missing_value', 1.e+20) 
        ncvar[:] = Actual
        NCout.close()
     
    
    
