# Executed once and for all
# Prints var names
from general import *
import scipy.io.netcdf as NC
avefile='/gpfs/scratch/userexternal/gcossari/BIO/UNZIPPED/AVE/ave.20141013-12:00:00.nc'

NCin = NC.netcdf_file(avefile,'r')

varDict=NCin.variables.copy()
for var in ['pCO','ppn', 'lon', 'lat', 'depth']:
    if varDict.has_key(var): varDict.pop(var)
NCin.close()


MODEL_VARS = file2stringlist("ModelVarNames")
TO_INTERPVARS = MODEL_VARS[:]

for var in varDict.keys():    
    TO_INTERPVARS.remove(var)

for var in TO_INTERPVARS:
    print var

