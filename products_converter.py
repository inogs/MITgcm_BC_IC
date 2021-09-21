import argparse

def argument():
    parser = argparse.ArgumentParser(description = '''
    Converts COPERNICUS products files for MIT chain.
    Works with MEDSEA_ANALYSISFORECAST_PHY_006_013 and MEDSEA_ANALYSISFORECAST_BGC_006_014.
    Generates ave files by cutting
    - along time dimension the product file
    - down up to the depth provided by maskfile (products could have more depths)


     ''',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(   '--inputfile', '-i',
                                type = str,
                                required = True,
                                help ='The directory wrkdir/MODEL/AVE_FREQ_1/ where chain has run.'
                                )
    parser.add_argument(   '--outputdir',"-o",
                                type = str,
                                required = True,
                                help = 'Path of existing dir')
    parser.add_argument(    '--maskfile', "-m",
                                type = str,
                                required = True,
                                help = '''Path for the maskfile ''')
    parser.add_argument(    '--varname', "-v",
                                type = str,
                                required = True,
                                help = '''Path for the maskfile ''')            
    
    
    return parser.parse_args()


args = argument()

from commons import netcdf4
from dateutil.relativedelta import relativedelta 
import datetime
from commons.mask import Mask
from commons.utils import addsep

BFM_NAMES={"no3" : "N3n",
          "po4" : "N1p",
          "nh4" : "N4n",
          "si"  : "N5s",
          "o2"  : "O2o", 
          "dissic": "O3c",
          "talk"  : "O3h"
}

PHYS_FILENAMES={"uo": "U",
            "vo": "V",
            "so": "S",
        "thetao": "T"
        }
PHYS_VARNAMES={"uo": "vozocrtx",
            "vo": "vomecrty",
            "so": "vosaline",
        "thetao": "votemper"
        }

VAR_CONV={"no3" : 1,
          "po4" : 1,
          "nh4" : 1,
          "si"  : 1,
          "o2"  : 1, 
          "dissic": 12000.,
          "talk"  : 1000.
}


prod_var=args.varname
if prod_var in PHYS_VARNAMES.keys():
    netcdf_varname = PHYS_VARNAMES[prod_var]
    file_varname = PHYS_FILENAMES[prod_var]
    conversion=1.0
    dateformat="%Y%m%d"
    fileformat="%s%s_%s.nc"
    Dref = datetime.datetime(1900,1,1,0,0,0)
else:
    netcdf_varname = BFM_NAMES[prod_var]
    file_varname   = BFM_NAMES[prod_var]
    conversion = VAR_CONV[prod_var]
    dateformat="%Y%m%d-%H:%M:%S"
    fileformat="%save.%s.%s.nc"
    Dref = datetime.datetime(1970,1,1,0,0,0)
OUTDIR=addsep(args.outputdir)

TheMask = Mask(args.maskfile)
jpk,_,_ = TheMask.shape


M = netcdf4.readfile(args.inputfile, prod_var)
time= netcdf4.readfile(args.inputfile,'time')


for it, t in enumerate(time):
    if prod_var in PHYS_VARNAMES.keys():
        d = Dref + relativedelta(minutes=t)
    else:
        d = Dref + relativedelta(seconds=t)
    outfile=fileformat %(OUTDIR,d.strftime(dateformat), file_varname)
    print(outfile)
    netcdf4.write_3d_file(M[it,:jpk,:,:]*conversion, netcdf_varname, outfile, TheMask, thredds=True)