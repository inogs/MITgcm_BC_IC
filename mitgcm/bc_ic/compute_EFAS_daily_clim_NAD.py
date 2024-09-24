# It computes the daily climatology of EFAS historical discharges in NAD subdomain (2011-2023) 
# It takes as inputs: 
# 1) the csv configuration file of rivers in NAD
# 2) the NetCDF EFAS maps of daily discharge in the single years (previously computed)
# and then it: 
# 1) extracts the time series of the rivers
# 2) corrects the discharges by the factor included in the configuration file 
# 3) saves the bias-corrected time series of discharges in a NetCDF file 
# 4) computes the daily climatology and saves it in a NetCDF file
# 5) computes the overall climatological mean and saves it in a csv file

import pandas as pd
import xarray as xr 
import numpy as np
import netCDF4 as NC
import matplotlib.pyplot as plt

### it reads the STATIC csv of the rivers in sub
DF = pd.read_csv('rivers_NAD.csv',sep=";")
DF = DF.dropna(axis = 0, how = 'all')
DF = DF.dropna(axis = 1, how = 'all')
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
ILON=np.asarray(DF['jir'],np.int32).tolist()
JLAT=np.asarray(DF['jjr'],np.int32).tolist()

FILES = []
for iyear in range(2011,2024):
    inputfile='/g100_scratch/userexternal/vdibiagi/EFAS/MER/DAILY/'+ str(iyear)+'_daily.nc'
    FILES.append(inputfile)

def select_points(DS):
    x = xr.DataArray(ILON, dims=['location']) 
    y = xr.DataArray(JLAT, dims=['location'])
    return DS.isel(longitude=x, latitude=y)

DSS=xr.open_mfdataset(FILES, combine='nested',concat_dim=["time"], preprocess=select_points)

# bias correction of the discahrge by a multiplicative factor read in the csv file
factor = xr.DataArray(np.asarray(DF['runoffFactor']),dims=['location'])
DScorr = DSS * factor

### it saves discharge daily timeseries in a NetCDF
DScorr.to_netcdf('rivers_daily_2011_2023_NAD.nc')

### Computing daily climatology
month_day_str = DScorr.time.dt.strftime("%m-%d")   
DS_DAILYCLIM = DScorr.groupby(month_day_str).mean('time')  
DS_DAILYCLIM.to_netcdf('rivers_CLIM_daily_2011_2023_NAD.nc')

# overall climatological mean of the river discharges
DF['CLIM']=DScorr.dis06.values.mean(axis=0)

# File of overall mean climatological discharges
SAVED = DF[['rivername', 'CLIM']]
SAVED.to_csv('rivers_CLIM_overall_mean_NAD.csv', index=True) 
