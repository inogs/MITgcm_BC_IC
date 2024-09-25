import argparse



def argument():
    parser = argparse.ArgumentParser(description = '''
    Cuts a single slice or a box in (longitude, latitude)
    starting from MIT .data files
    Arguments loncut and latcut define if the cut is a longitudinal or latitudinal slice
    or is a box. The entire depth is taken in account.
    Output file is a cutted ave file.
    At present is parallelized over timelist.
    
    ''')
    parser.add_argument(   '--inputdir', '-i',
                                type = str,
                                required=True,
                                help = '''Directory where original files are stored. 
                                E.g. /some/path/MODEL/AVE_FREQ_1/                                
                                ''')
    parser.add_argument(   '--outputdir',"-o",
                                type = str,
                                required=True,
                                help = '/some/path/')
    parser.add_argument(   '--loncut',
                                type = str,
                                required=True,
                                help = '22,25')
    parser.add_argument(   '--latcut',
                                type = str,
                                required=True,
                                help = '100,102')
    parser.add_argument(    '--modelvarlist',"-v", 
                                type = str,
                                required=True,
                                help = '/some/path/filename' )    
    parser.add_argument(    '--timelist',"-t", 
                                type = str,
                                required=True,
                                help = '''Path name of the file with the time list.
                                A single time (1 row file) it can be used for IC.
                                E.g. /some/path/filename''' ) 
    parser.add_argument(    '--mask',"-m", 
                                type = str,
                                required=True,
                                help = '/some/path/filename' )         
        
    return parser.parse_args()



args = argument()       

from general import *
import datetime
import numpy as np

INPUTDIR  = addsep(args.inputdir)
OUTPUTDIR = addsep(args.outputdir)
os.system("mkdir -p " + OUTPUTDIR) 


MODELVARS  = file2stringlist(args.modelvarlist)
TIMELIST   = file2stringlist(args.timelist)

TIMESTART = TIMELIST.pop(0)
DATESTART = datetime.datetime.strptime(TIMESTART,"%Y%m%d-%H:%M:%S")

strlst = args.latcut.rsplit(",")
lat0 = int(strlst[0])
lat1 = int(strlst[1])+1
strlst = args.loncut.rsplit(",")
lon0 = int(strlst[0])
lon1 = int(strlst[1])+1

Mask = mask(args.mask)
Lon = Mask.Lon[lon0:lon1]
Lat = Mask.Lat[lat0:lat1]

cut_type = "Box"
if Lon.size==1: cut_type =  "Longitudinal"
if Lat.size==1: cut_type =  "Latitudinal"
print "cut type : " + cut_type


def create_Header(filename):
    NCout = NC.netcdf_file(filename,'w')
       
    NCout.createDimension('lon'  , Lon.size )
    NCout.createDimension('lat'  , Lat.size )
    NCout.createDimension('depth', Mask.jpk )

    ncvar=NCout.createVariable('lon'  ,'f',('lon'  ,))
    ncvar[:]=Lon    
    ncvar=NCout.createVariable('lat'  ,'f',('lat'  ,))
    ncvar[:]=Lat
    
    ncvar=NCout.createVariable('depth','f',('depth',))
    ncvar[:]=Mask.Depth        
        
    return NCout



for time in TIMELIST:     
    print time
    t = datetime.datetime.strptime(time,"%Y%m%d-%H:%M:%S")
    elapsed = t - DATESTART
    elapsed_timestep = "%010d" % (elapsed.total_seconds()/100)
    
    
    for var in MODELVARS:
        inputfile = INPUTDIR  +  var + '.'+ elapsed_timestep + ".data"
        cutfile   = OUTPUTDIR +  "ave." + time + "." + var + ".nc"      
        
        
        A = np.fromfile(inputfile,np.float32)
        M = A.reshape(Mask.jpk, Mask.jpj, Mask.jpi)
        
        
        NCc = create_Header(cutfile)
        if cut_type is "Box": 
            ncvar=NCc.createVariable(var,'f', ('depth', 'lat','lon'))
            setattr(ncvar,'missing_value',1.e+20)
            ncvar[:] = M[:,lat0:lat1,lon0:lon1]
        if cut_type is "Longitudinal":
            ncvar=NCc.createVariable(var,'f', ('depth', 'lat'))
            setattr(ncvar,'missing_value',1.e+20)
            ncvar[:] = M[:,lat0:lat1,lon0]
        if cut_type is "Latitudinal":
            ncvar=NCc.createVariable(var,'f', ('depth', 'lon'))
            setattr(ncvar,'missing_value',1.e+20)
            ncvar[:] = M[:,lat0,lon0:lon1]

        NCc.close()
        
        if time == TIMELIST[0]:
            cutfile0 = OUTPUTDIR +  "ave." + TIMESTART + "." + var + ".nc"
            os.system("cp " + cutfile + " " + cutfile0)  
