import argparse

def argument():
    parser = argparse.ArgumentParser(description = '''
    Generates meshmask from  MEDSEA_ANALYSISFORECAST_BGC_006_014 static files,
    MED_MFC_006_014_mask_bathy.nc and MED_MFC_006_014_coordinates.nc
     ''',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(   '--inputdir', '-i',
                                type = str,
                                required = True,
                                help ='The directory where MED_MFC_006_014_mask_bathy.nc and MED_MFC_006_014_coordinates.nc are.'
                                )
    parser.add_argument(   '--outfile',"-o",
                                type = str,
                                required = True,
                                help = 'Path of existing dir')
           
    
    
    return parser.parse_args()


args = argument()

from commons import netcdf4
import netCDF4
import numpy as np
from commons.utils import addsep

INPUTDIR=addsep(args.inputdir)
bathyfile=INPUTDIR+"MED_MFC_006_014_mask_bathy.nc"
coordfile=INPUTDIR+"MED_MFC_006_014_coordinates.nc"
lon     = netcdf4.readfile(bathyfile, 'longitude')
lat     = netcdf4.readfile(bathyfile, 'latitude')
nav_lev = netcdf4.readfile(bathyfile, 'depth')
tmask   = netcdf4.readfile(bathyfile, 'mask')
e1t=netcdf4.readfile(coordfile, 'e1t')
e2t=netcdf4.readfile(coordfile, 'e2t')
e3t=netcdf4.readfile(coordfile, 'e3t')


jpk, jpj, jpi = e3t.shape
time, z_a = 1,1
E3t = np.ones((time,jpk,jpj,jpi),np.double)
E2t = np.ones((time,z_a,jpj,jpi),np.double)
E1t = np.ones((time,z_a,jpj,jpi),np.double)
Glamt = np.ones((time,z_a,jpj,jpi),np.double)
Gphit = np.ones((time,z_a,jpj,jpi),np.double)
Tmask = np.ones((time,jpk,jpj,jpi),np.double)
E3t[0,:] = e3t
E2t[0,0,:] = e2t
E2t[0,0,:] = e1t


nav_lon,nav_lat = np.meshgrid(lon,lat)
Glamt[0,0,:] = nav_lon
Gphit[0,0,:] = nav_lat
Tmask[0,:] = tmask.astype(np.double)

ncOUT = netCDF4.Dataset(args.outfile,'w')
ncOUT.createDimension('x',jpi);
ncOUT.createDimension('y',jpj);
ncOUT.createDimension('z',jpk);
ncOUT.createDimension('time',time)
ncOUT.createDimension('x_a',1);
ncOUT.createDimension('y_a',1);
ncOUT.createDimension('z_a',1);
ncvar    = ncOUT.createVariable('e1t'   ,'d',('time','z_a', 'y', 'x')  ) ; ncvar[:] = E1t
ncvar    = ncOUT.createVariable('e2t'   ,'d',('time','z_a', 'y', 'x')  ) ; ncvar[:] = E2t
ncvar    = ncOUT.createVariable('e3t'   ,'d',('time','z'  , 'y', 'x')  ) ; ncvar[:] = E3t
ncvar    = ncOUT.createVariable('nav_lat','f',('y','x'))                 ; ncvar[:] = nav_lat
ncvar    = ncOUT.createVariable('nav_lev' ,'f',('z',))                   ; ncvar[:] = nav_lev
ncvar    = ncOUT.createVariable('nav_lon','f',('y','x'))                 ; ncvar[:] = nav_lon
ncvar    = ncOUT.createVariable('glamt'   ,'d',('time','z_a', 'y', 'x')) ; ncvar[:] = nav_lon
ncvar    = ncOUT.createVariable('gphit'   ,'d',('time','z_a', 'y', 'x')) ; ncvar[:] = nav_lat
ncvar    = ncOUT.createVariable('tmask' ,'d',('time','z', 'y', 'x') )    ; ncvar[:] = tmask
ncOUT.close()



#from commons.mask import Mask
#M = Mask(args.outfile)