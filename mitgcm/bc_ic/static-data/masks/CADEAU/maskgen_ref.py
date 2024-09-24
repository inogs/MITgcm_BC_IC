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



delZ = np.array([1.075198334203378181,    1.228564680493946071,    1.386477340563033067,    1.549060921308409888,    
                 1.716442813513822330,    1.888753213787822460,    2.066125143780482176,    2.248694466392407776,    
                 2.436599898702297651,    2.629983021427506173,    2.828988284530169039,    3.033763008798814553,    
                 3.244457383028020558,    3.461224456502350222,    3.684220126478066959,    3.913603120323386975,    
                 4.149534971932553162,    4.392179992144519929,    4.641705232656931912,    4.898280443211660895,    
                 5.162078021539855399,    5.433272955713164265,    5.712042758509596752,    5.998567393322900898,    
                 6.293029191242567322,    6.595612758841980394,    6.906504876239523583,    7.225894385009723919,    
                 7.553972065481502796,    7.890930502996980067,    8.236963942674719874,    8.592268132257231628,    
                 8.957040152604349714,    9.331478235393205978,    9.715781567658723361,    10.110150082715335884,    
                10.514784237146614032,   10.929884773448975466,   11.355652468037988001])
delZ = np.concatenate((np.ones(20,),  delZ  ), axis=0)

CellBottoms=np.cumsum(delZ)
Depth = CellBottoms - delZ/2

jpi = 494
jpj = 300
jpk = Depth.size

Lat = 43.47265625 + np.arange(jpj)*1./128
Lon = 12.22265625 + np.arange(jpi)*1./128

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

