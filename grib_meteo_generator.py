import os 
import argparse
import interpolator


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

TIMELIST = args.timelist
INPUTDIR = args.inputdir
OUTPUTDIR = args.outputdir
MASKFILE = args.outmaskfile

os.system( f'mkdir -p {OUTPUTDIR}' )
os.system( f'rm -rf {OUTPUTDIR}/*' )
#os.system( f'mkdir -p " + OUTPUTDIR + "CHECK") 


VARS = ['Lat', 'Lon', 'aqh', 'lwdown', 'swdown', 'precip', 'apress', 'uwind', 'vwind', 'atemp']
data = interpolator.interpolate(
    INPUTDIR, 
    TIMELIST,
    MASKFILE, 
    VARS[ 2 : ], 
    OUTPUTDIR
) 
