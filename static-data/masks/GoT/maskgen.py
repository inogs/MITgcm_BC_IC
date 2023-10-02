import argparse
def arguments():
    parser = argparse.ArgumentParser(description = '''
   Generates maskfile by reading bathymetry
    ''', formatter_class=argparse.RawTextHelpFormatter)
 
 
    parser.add_argument(   '--bathymetry','-b',
                                type = str,
                                required = True,
                                help = 'Path of the bathymetry file')
    parser.add_argument(   '--outputfile','-o',
                                type = str,
                                required = True,
                                help = 'Path of the maskfile')                                

    return parser.parse_args()

args = arguments()
import numpy as np
import scipy.io as NC

bathyfile = args.bathymetry
maskfile  = args.outputfile


delZ = np.concatenate((np.ones(6,)*0.5, np.ones(29,)*1.0, np.ones(4,)*2.0, np.ones(18,)*3.0  ), axis=0)


CellBottoms=np.cumsum(delZ)
Depth = CellBottoms - delZ/2

jpi = 450
jpj = 300
jpk = Depth.size

Lat = 45.40 + np.arange(jpj)*1./768
Lon = 13.22 + np.arange(jpi)*1./768

# tmask construction

fid=open(bathyfile,'rb')
domain_size=jpi*jpj
A=np.fromfile(fid,dtype=np.float32,count=domain_size).astype(np.float64)
fid.close()
Bathy = -A.reshape(jpj,jpi)

#ii=Bathy>0
#Bathy[ii] = Bathy[ii]-1.4e-07

LEVELS=np.zeros((jpj,jpi),np.int32)

for ji in range(jpi):
    for jj in range(jpj):
        if Bathy[jj,ji] == 0:
            LEVELS[jj,ji] = 0;
        else:
            for jk in range(jpk):
                if CellBottoms[jk] >= Bathy[jj,ji]:
                    break
            LEVELS[jj,ji]=jk+1

tmask = np.zeros((jpk,jpj,jpi), bool);

for ji in range(jpi):
    for jj in range(jpj):
        for jk in range(LEVELS[jj,ji]):
            tmask[jk, jj,ji] = True



ncOUT = NC.netcdf_file(maskfile,"w")
ncOUT.createDimension("lon",jpi)
ncOUT.createDimension("lat",jpj)
ncOUT.createDimension("depth",jpk)
ncOUT.createDimension("z_a",1)

ncvar    = ncOUT.createVariable("lon", 'f', ("lon",))
ncvar[:] = Lon
ncvar    = ncOUT.createVariable("lat", 'f', ("lat",))
ncvar[:] = Lat

ncvar    = ncOUT.createVariable("depth", 'f', ("depth",))
ncvar[:] = Depth

ncvar    = ncOUT.createVariable("CellBottoms", 'f', ("depth",))
ncvar[:] = CellBottoms

ncvar    = ncOUT.createVariable("tmask", 'b', ("depth","lat","lon"))
ncvar[:] = tmask

ncvar    = ncOUT.createVariable("nav_lev", 'f', ("depth",))
ncvar[:] = Depth
ncvar    = ncOUT.createVariable("e3t", 'f', ('z_a',"depth",'lat','lon'))
ncvar[0,:] = tmask

ncvar    = ncOUT.createVariable("nav_lon", 'f', ("lat", "lon",))
lon2d=  np.repeat(np.array(Lon,ndmin=2),jpj,axis=0)
lat2d = np.repeat(np.array(Lat,ndmin=2).T,jpi,axis=1)
ncvar[:] = lon2d


ncvar    = ncOUT.createVariable("nav_lat", 'f', ("lat","lon"))
ncvar[:] = lat2d

ncvar = ncOUT.createVariable("e1t",'f',('z_a','z_a','lat','lon'))
ncvar[:]=0
ncvar = ncOUT.createVariable("e2t",'f',('z_a','z_a','lat','lon'))
ncvar[:]=0

ncOUT.close()

