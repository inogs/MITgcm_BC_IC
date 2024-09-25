import argparse



def argument():
    parser = argparse.ArgumentParser(description = '''
    Cuts a single slice or a box in (longitude, latitude) and depth (using Mask levels)
    starting from BIO, ave or RST files.

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
    parser.add_argument(   '--side',
                                type = str,
                                required=False,
                                choices=['N','S','E','W'],
                                help = 'If not indicated, it cuts a box corresponding to output mask  ')

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
    parser.add_argument(    '--datatype', '-d',
                                type = str,
                                required=True,
                                choices = ['ave', 'AVE', 'RST'] )
    parser.add_argument(    '--mask',"-m", 
                                type = str,
                                required=True,
                                help = 'output mask file' )
    parser.add_argument(    '--nativemask',"-M",
                                type = str,
                                required=True,
                                help = 'input mask file' )



    return parser.parse_args()

from general import *
import netCDF4
from commons.dataextractor import DataExtractor
from commons.mask import Mask

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


Mask_bitsea1 = Mask(args.nativemask)
Mask1 = mask(args.nativemask)
Mask2 = mask(args.mask)

if args.side is None:
    cut_type = "Box"
else:
    cut_type = 'side'

def nearest_ind(array,value):
    DIST = (array-value)**2
    ind=np.nonzero(DIST==DIST.min())# tuple
    return int(ind[0][0])


cut_lon_0= nearest_ind(Mask1.Lon, Mask2.Lon[0])
cut_lon_1= nearest_ind(Mask1.Lon, Mask2.Lon[-1])
cut_lat_0= nearest_ind(Mask1.Lat, Mask2.Lat[0])
cut_lat_1= nearest_ind(Mask1.Lat, Mask2.Lat[-1])
cut_depth= nearest_ind(Mask1.Depth, Mask2.Depth[-1])+1




Lon = Mask1.Lon[cut_lon_0:cut_lon_1+1]
Lat = Mask1.Lat[cut_lat_0:cut_lat_1+1]




def create_Header(filename):
    NCout = NC.netcdf_file(filename,'w')

    NCout.createDimension('lon'  , Lon.size )
    NCout.createDimension('lat'  , Lat.size )
    NCout.createDimension('depth', cut_depth )

    ncvar=NCout.createVariable('lon'  ,'f',('lon'  ,))
    ncvar[:]=Lon    
    ncvar=NCout.createVariable('lat'  ,'f',('lat'  ,))
    ncvar[:]=Lat
    
    ncvar=NCout.createVariable('depth','f',('depth',))
    ncvar[:]=Mask1.Depth[0:cut_depth]
        
    return NCout



for time in TIMELIST[rank::nranks]:     
    print(time,flush=True)
       
       
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
            M = DataExtractor(Mask_bitsea1, inputfile, invar).values
        except:
            raise ValueError ("file %s cannot be read" %inputfile ) 
        
        NCc = create_Header(cutfile)
        if cut_type == "Box":
            ncvar=NCc.createVariable(var,'f', ('depth', 'lat','lon'))
            ncvar[:] = M[:cut_depth,cut_lat_0:cut_lat_1+1,cut_lon_0:cut_lon_1+1]

        if args.side == 'E':
            ncvar=NCc.createVariable(var,'f', ('depth', 'lat'))
            ncvar[:] = M[:cut_depth,cut_lat_0:cut_lat_1+1,cut_lon_1]
        if args.side == 'W':
            ncvar=NCc.createVariable(var,'f', ('depth', 'lat'))
            ncvar[:] = M[:cut_depth,cut_lat_0:cut_lat_1+1,cut_lon_0]
        if args.side == 'S':
            ncvar=NCc.createVariable(var,'f', ('depth', 'lon'))
            ncvar[:] = M[:cut_depth,cut_lat_0,cut_lon_0:cut_lon_1+1]
        if args.side == 'N':
            ncvar=NCc.createVariable(var,'f', ('depth', 'lon'))
            ncvar[:] = M[:cut_depth,cut_lat_1,cut_lon_0:cut_lon_1+1]



        setattr(ncvar,'missing_value',1.e+20)


        NCc.close()
