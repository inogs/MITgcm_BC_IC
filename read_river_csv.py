from pathlib import Path
import numpy as np
import pandas as pd

import os
import sys

import rivers


csv_file = os.getenv("RIVERDATA")
if csv_file is None:
    print("Error: Environment variables RIVERDATA - indicating the name of csv river file - must be defined.")
    sys.exit(1)
csv_file = Path(csv_file)

meteodir = os.getenv("RIVERMETEODIR")
if meteodir is None:
    print("Error: Environment variables RIVERMETEODIR - indicating where to find discharge files - must be defined.")
    sys.exit(1)
meteodir = Path(meteodir)

csv_data = pd.read_csv(csv_file)

# Here we read the name of the variables; the first 9 entries are not
# biogeochemical variables but latitude, longitude, cell indices, etc...
bgc_vars = []
for i, var_name in enumerate(csv_data.columns):
    if i <= 8:
        continue
    bgc_vars.append(rivers.BGCVar(i - 8, var_name))

nRivers = len(csv_data)


RATIOS = np.zeros(nRivers, np.float32)
for iRiver in range(nRivers):
    R = rivers.River(csv_data.iloc[iRiver], meteo_dir=meteodir)
    RATIOS[iRiver] = R.get_ratio()


actual_vs_clim_ratio = np.nanmean(RATIOS)
if np.isnan(actual_vs_clim_ratio):
    actual_vs_clim_ratio = 1.0
print("Applying ratio : ", actual_vs_clim_ratio)

RIVERS = []

for iRiver in range(nRivers):
    R = rivers.River(csv_data.iloc[iRiver], meteo_dir=meteodir)
    R.apply_ratio(actual_vs_clim_ratio)
    RIVERS.append(R)


def get_RiverPHYS_Data(lato, varname, timelist, Mask):
    return rivers.get_RiverPHYS_Data(lato, varname, timelist, Mask, RIVERS)


def get_RiverBFM_Data(lato, varname):
    return rivers.get_RiverBFM_Data(lato, varname, RIVERS, bgc_vars)


if __name__ == "__main__":
    timelist=['20220614-12:00:00']
    from general import mask
    Mask = mask('/g100_work/OGS_prodC/MIT/V1M-dev/V1/devel/wrkdir/BC_IC/mask.nc')
    A = get_RiverPHYS_Data('W', 'V', timelist, Mask)
