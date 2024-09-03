import argparse
from utilities.argparse_types import existing_dir_path, existing_file_path, generic_path

def argument():
    parser = argparse.ArgumentParser(description = '''
    Generates EFAS daily file
    ''', formatter_class=argparse.RawTextHelpFormatter)


    parser.add_argument(   '--inputfile','-i',
                                type = existing_file_path,
                                required = True,
                                help = '''downloaded gzip file from EFAS service''')
    parser.add_argument(   '--tmpdir','-d',
                                type = existing_dir_path,
                                required = True,
                                help = 'Output dir ')
    parser.add_argument(   '--config', '-c',
                                type=existing_file_path,
                                required=True,
                                help = "Rivers csv file"),
    parser.add_argument(   '--outfile','-o',
                                type = generic_path,
                                required = True,
                                help = '''output file name''')

    return parser.parse_args()

args = argument()

import numpy as np
import xarray as xr
from zipfile import ZipFile
import pandas as pd


### unzip of the downloaded EFAS file
with ZipFile(args.inputfile, 'r') as zip_ref:
    zip_ref.extractall(args.tmpdir)
    
### it reads the dataset and computes the daily mean
nc_tmp_file = args.tmpdir / "mars_data_0.nc"
DS = xr.open_dataset(nc_tmp_file)
dailyDS = DS.resample(time="1D").mean()

daily_filename = args.tmpdir / "daily_discharges.nc"
dailyDS.to_netcdf(daily_filename)

### Reading the river csv file
DF = pd.read_csv(args.config,sep=";")
DF = DF.dropna(axis = 0, how = 'all')
nriv = len(DF)

### it extracts data at EFAS river i (longitude), j (latitude)
ILON=[int(k) for k in DF['jir'] ]
JLAT=[int(k) for k in DF['jjr'] ]

x = xr.DataArray(ILON, dims=['location'])
y = xr.DataArray(JLAT, dims=['location'])

def select_points(xr_obj : xr.DataArray):
    return xr_obj.isel(longitude=x, latitude=y)

# general case, i.e., daily_filename can be replaced by a list of files and it works
DSS = xr.open_mfdataset(daily_filename, combine='nested',concat_dim=["time"], preprocess=select_points)

# bias correction of the runoff by a multiplicative factor read in the csv file
factor = xr.DataArray(np.asarray(DF['runoffFactor']),dims=['location'])
DScorr = DSS * factor

### saves discharge daily timeseries in a NetCDF
DScorr.to_netcdf(args.outfile)

def rivernames_for_netcdf():
    '''Retrieves the rivernames
    (checking and deleting possible spaces at the end'''
    LIST_NAMES_TABLE = DF['rivername'].tolist()
    lenstringnames=len(max(LIST_NAMES_TABLE, key=len))
    LIST_NAMES_NETCDF=list(LIST_NAMES_TABLE)
    for iriv in range(nriv):
        nameriv=LIST_NAMES_TABLE[iriv]
        strFormatRiv="{:\0<" +str(lenstringnames) +"}"
        nameriv=strFormatRiv.format(nameriv+'\0')
        LIST_NAMES_NETCDF[iriv]=nameriv
