import argparse

def argument():
    parser = argparse.ArgumentParser(description = 'Interpolates in time producing ave files. Reads timelist files')
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
    parser.add_argument(    '--datatype', 
                                type = str,
                                required=True,
                                choices = ['ave', 'AVE', 'RST'] )
    parser.add_argument(    '--varlist',"-v", 
                                type = str,
                                required=True,
                                help = '/some/path/filename' )
    parser.add_argument(   '--maskfile', '-m',
                                type = str,
                                required = True,
                                help = '/some/path/mask.nc')    
    
    
    
    return parser.parse_args()



args = argument()

from general import *
from commons import genUserDateList as DL

INPUT_DIR    = addsep(args.inputdir)
OUTPUTDIR    = addsep(args.outputdir)

inputtype = args.datatype

dateFormat="%Y%m%d-%H:%M:%S"
os.system("mkdir -p " + OUTPUTDIR)


Input_TIMELIST=[]
for line in file2stringlist(args.inputtimefile):
    Input_TIMELIST.append(DL.readTimeString(line))
OutputTIMELIST=[]
for line in file2stringlist(args.outputtimefile):
    OutputTIMELIST.append(DL.readTimeString(line))






def Load_Data(DATADIR, TimeList,before,after,var, datatype):
    Before_date17 = TimeList[before].strftime(dateFormat)
    After__date17 = TimeList[after ].strftime(dateFormat)
    
    if datatype == 'RST':         
        Before_File = "RST." + Before_date17 + "."  + var + ".nc"
        After__File = "RST." + After__date17 + "."  + var + ".nc"
        var = "TRN" + var        
    elif datatype=='ave':
        Before_File = "ave." + Before_date17 + "." + var + ".nc"
        After__File = "ave." + After__date17 + "." + var + ".nc"
    elif datatype=='AVE':
        Before_File = "ave." + Before_date17 + ".nc"
        After__File = "ave." + After__date17 + ".nc"    
    print "loading " + Before_File, After__File, 'for ', var
    
    ncB = NC.netcdf_file(DATADIR + Before_File,'r')
    ncA = NC.netcdf_file(DATADIR + After__File,'r')
    
    Before_Data = ncB.variables[var].data[0,:,:,:].copy().astype(np.float32)
    After__Data = ncA.variables[var].data[0,:,:,:].copy().astype(np.float32)
    
    ncA.close()
    ncB.close()
    return Before_Data, After__Data





Mask = mask(args.maskfile)


BEFORE, AFTER,T_interp = Time_Interpolation(OutputTIMELIST[0],Input_TIMELIST)
VARLIST=file2stringlist(args.varlist)
for var in VARLIST:
    Before_DATA, After__DATA = Load_Data(INPUT_DIR, Input_TIMELIST, BEFORE, AFTER,var,inputtype)
    tmask=Before_DATA > 1.e+19;
    
    
    
    for t in OutputTIMELIST:
        outfile = OUTPUTDIR  +  "ave." + t.strftime(dateFormat) +"." + var + ".nc"
        print outfile
        
        before,after,T_interp = Time_Interpolation(t,Input_TIMELIST)
        if before>BEFORE:
            BEFORE=before
            AFTER=after
            Before_DATA, After__DATA = Load_Data(INPUT_DIR, Input_TIMELIST, BEFORE, AFTER,var,inputtype)
        Actual = (1-T_interp)*Before_DATA + T_interp*After__DATA
        Actual[tmask] = 1.e+20
        
        NCout = NC.netcdf_file(outfile,'w')
        NCout.createDimension("lon",Mask.Lon.size)
        NCout.createDimension("lat",Mask.Lat.size)
        NCout.createDimension("depth",Mask.jpk)
        NCout.createDimension("time", 1)
        ncvar = NCout.createVariable("lon",'f',('lon',))
        ncvar[:] = Mask.Lon
        ncvar = NCout.createVariable("lat",'f',('lat',))
        ncvar[:] = Mask.Lat
        ncvar = NCout.createVariable("depth",'f',('depth',))
        ncvar[:] = Mask.Depth
            
        ncvar = NCout.createVariable(var,'f',('time','depth','lat','lon'))
        setattr(ncvar,'missing_value',1.e+20)
        ncvar[:] = Actual
        
        NCout.close()
     
    
    
