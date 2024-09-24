# It computes the daily historical EFAS maps from 6-hours maps, for each year in 2011-2023, in the whole domain
# For each year in a loop it:
# 1) takes as input the zipped NetCDF file of the EFAS historical maps of 6-hours discharges 
# 2) moves the file in the directory associated with the year 
# 3) extracts the dataset
# 4) computes the daily maps 
# 5) saves them in a NetCDF 

import numpy as np
import xarray as xr
from zipfile import ZipFile
import os

rundir = "/g100_scratch/userexternal/vdibiagi/EFAS/MER/"

for YEAR in range(2011,2024):

    print(str(YEAR))

    # it moves the EFAS file downloaded as downloaded${YEAR}.netcdf4.zip in the directory of the associated YEAR    
    os.rename(rundir + 'download'+str(YEAR)+'.netcdf4.zip', rundir+str(YEAR)+'/download'+str(YEAR)+'.netcdf4.zip')

    # it does the unzip of the downloaded file
    with ZipFile(rundir+str(YEAR)+'/download'+str(YEAR)+".netcdf4.zip", 'r') as zip_ref:
        zip_ref.extractall(rundir+str(YEAR))
    
    # it reads the dataset
    nc_data = rundir +str(YEAR)+"/mars_data_0.nc"
    DS = xr.open_dataset(nc_data)
    print(DS.time[0].data)
    print(int(len(DS.time)/4))

    # it computes the daily mean and saves it in a NetCDF
    dailyDS = DS.resample(time="1D").mean()   
    dailyDS.to_netcdf(rundir+"/DAILY/"+str(YEAR)+"_daily.nc")
