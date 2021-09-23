import argparse



def argument():
    parser = argparse.ArgumentParser(description = '''
    Cuts a single slice or a box in (longitude, latitude) and depth (using Mask levels)
    starting from BIO, ave or RST files.
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
    parser.add_argument(    '--datatype', 
                                type = str,
                                required=True,
                                choices = ['ave', 'AVE', 'RST'] )
    parser.add_argument(    '--mask',"-m", 
                                type = str,
                                required=True,
                                help = '/some/path/filename' )         
        
    return parser.parse_args()

from general import *
import netCDF4

try :
    from mpi4py import MPI
    comm  = MPI.COMM_WORLD
    rank  = comm.Get_rank()
    nranks = comm.size 
except:
    rank   = 0
    nranks = 1

args = argument()       

INPUTDIR  = addsep(args.inputdir)
OUTPUTDIR = addsep(args.outputdir)
datatype = args.datatype
os.system("mkdir -p " + OUTPUTDIR) 


MODELVARS  = file2stringlist(args.modelvarlist)
TIMELIST   = file2stringlist(args.timelist)

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
print("cut type : " + cut_type)


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



for time in TIMELIST[rank::nranks]:     
    print(time)
       
       
    for var in MODELVARS:
        filename = "ave." + time + "." + var + ".nc"
        cutfile  = OUTPUTDIR +  filename
        
        if datatype == 'RST':         
            filename = "RST." + time + "."  + var + ".nc"
            invar = "TRN" + var        
        elif datatype=='AVE':
            filename = "ave." + time + ".nc"
            invar=var
        elif datatype=='ave':
            filename = "ave." + time + "." + var + ".nc"
            invar=var
       
        
        inputfile = INPUTDIR  +  filename
        
        try:        
            # NCin = NC.netcdf_file(inputfile,'r')
            # M = NCin.variables[invar].data.copy().astype(np.float32)
            # NCin.close()
            D=netCDF4.Dataset(inputfile,'r')
            M = np.array(D[invar])
            D.close()
        except:
            raise ValueError ("file %s cannot be read" %inputfile ) 
        
        NCc = create_Header(cutfile)
        if cut_type is "Box": 
            ncvar=NCc.createVariable(var,'f', ('depth', 'lat','lon'))
            setattr(ncvar,'missing_value',1.e+20)
            ncvar[:] = M[0,:Mask.jpk,lat0:lat1,lon0:lon1]
        if cut_type is "Longitudinal":
            ncvar=NCc.createVariable(var,'f', ('depth', 'lat'))
            setattr(ncvar,'missing_value',1.e+20)
            ncvar[:] = M[0,:Mask.jpk,lat0:lat1,lon0]
        if cut_type is "Latitudinal":
            ncvar=NCc.createVariable(var,'f', ('depth', 'lon'))
            setattr(ncvar,'missing_value',1.e+20)
            ncvar[:] = M[0,:Mask.jpk,lat0,lon0:lon1]

        NCc.close()
