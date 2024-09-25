import argparse
from bitsea.utilities.argparse_types import existing_dir_path, existing_file_path
import json
from bitsea.commons import netcdf4
from dateutil.relativedelta import relativedelta 
import datetime
from bitsea.commons.mask import Mask
import xarray as xr
from dataclasses import dataclass
import numpy as np



def argument():
    parser = argparse.ArgumentParser(description = '''
    Converts COPERNICUS products files for MIT chain.
    Works with MEDSEA_ANALYSISFORECAST_PHY_006_013 and MEDSEA_ANALYSISFORECAST_BGC_006_014.
    Generates ave files by cutting
    - along time dimension the product file
    - down up to the depth provided by maskfile (products could have more depths)


     ''',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(   '--inputdir', '-i',
                                type = existing_dir_path,
                                required = True,
                                help ='The directory wrkdir/MODEL/AVE_FREQ_1/ where chain has run.'
                                )
    parser.add_argument(   '--outputdir',"-o",
                                type = existing_dir_path,
                                required = True,
                                help = 'Path of existing dir')
    parser.add_argument(    '--maskfile', "-m",
                                type = existing_file_path,
                                required = True,
                                help = '''Path for the maskfile ''')
    parser.add_argument(    '--rundate', "-d",
                                type = str,
                                required = True,
                                help = '''Rundate in yyyymmdd format ''')
    parser.add_argument(    '--config', "-c",
                                type = existing_file_path,
                                required = True,
                                help = '''Rundate in yyyymmdd format ''')

    return parser.parse_args()


args = argument()

@dataclass
class modelvar:
    bfm_name: str
    cmems_name:str
    dataset:str
    productID:str
    conversion_value:float=1

with open(args.config) as f:
    A=json.load(f)

VARIABLES=[modelvar(**raw_var) for raw_var in A["variables"]]

dateformat="%Y%m%d-%H:%M:%S"
TheMask = Mask(args.maskfile)
jpk,_,_ = TheMask.shape



for V in VARIABLES:

    basename = "{}-{}.nc".format(V.dataset,args.rundate)

    inputfile = args.inputdir / basename
    M = netcdf4.readfile(inputfile, V.cmems_name)
    time = xr.open_dataset(inputfile).time

    for it, t in enumerate(time.to_numpy()):
        d=np.datetime64(t,'s').astype(datetime.datetime)
        datestr=(d + relativedelta(hours=12)).strftime(dateformat)
        outbasename="ave.{}.{}.nc".format(datestr,V.bfm_name)
        outfile= args.outputdir / outbasename
        print(outfile)
        netcdf4.write_3d_file(M[it,:jpk,:,:]*V.conversion_value, V.bfm_name, outfile, TheMask, thredds=True)
