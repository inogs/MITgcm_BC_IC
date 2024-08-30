import numpy as np
import xarray as xr
from zipfile import ZipFile
import os
import pandas as pd
import xarray  
import netCDF4 as NC
import matplotlib.pyplot as plt

strDatasetType = 'forecast' # "historical" or "forecast"
# add check on one of these two

rundir = "/g100_scratch/userexternal/vdibiagi/EFAS/MER/SHARED/"

if not os.path.exists(rundir + strDatasetType):
    os.makedirs(rundir + strDatasetType)

### it does the unzip of the downloaded EFAS file
with ZipFile(rundir + "download_2023_" + strDatasetType + ".netcdf4.zip", 'r') as zip_ref:
    zip_ref.extractall(rundir + strDatasetType)
    
### it reads the dataset and computes the daily mean
nc_data = rundir + strDatasetType + "/mars_data_0.nc"
DS = xr.open_dataset(nc_data)
dailyDS = DS.resample(time="1D").mean()   
daily_filename = strDatasetType + "_daily_discharges.nc"
dailyDS.to_netcdf(rundir + daily_filename)

### it reads the STATIC csv of the rivers in sub
DF = pd.read_csv('rivers_NAD.csv',sep=";")
DF = DF.dropna(axis = 0, how = 'all')
nriv = len(DF)

### it retrieves the rivernames (checking and deleting possible spaces at the end)
LIST_NAMES_TABLE = DF['rivername'].tolist()   
lenstringnames=len(max(LIST_NAMES_TABLE, key=len))
LIST_NAMES_NETCDF=list(LIST_NAMES_TABLE)
for iriv in range(nriv):
   nameriv=LIST_NAMES_TABLE[iriv]
   strFormatRiv="{:\0<" +str(lenstringnames) +"}"
   nameriv=strFormatRiv.format(nameriv+'\0')
   LIST_NAMES_NETCDF[iriv]=nameriv

### it extracts data at EFAS river i (longitude), j (latitude)
ILON=DF['jir'].tolist()
JLAT=DF['jjr'].tolist()

def select_points(DSS):
    x = xarray.DataArray(ILON, dims=['location'])
    y = xarray.DataArray(JLAT, dims=['location'])
    return DSS.isel(longitude=x, latitude=y)

# general case, i.e., daily_filename can be replaced by a list of files and it works
DSS = xarray.open_mfdataset(daily_filename, combine='nested',concat_dim=["time"], preprocess=select_points)

# bias correction of the runoff by a multiplicative factor read in the csv file
factor = xr.DataArray(np.asarray(DF['runoffFactor']),dims=['location'])  
DScorr = DSS * factor

### it saves discharge daily timeseries in a NetCDF
DScorr.to_netcdf('rivers_sub_'+ strDatasetType + '.nc')
