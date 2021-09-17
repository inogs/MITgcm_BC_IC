import numpy as np

import netCDF4
import os
from commons.utils import data_for_linear_interp, Time_Interpolation
from commons.utils import addsep, file2stringlist
from commons.interpolators import SeaOverLand
from scipy import interpolate
import scipy.io.netcdf as NC


NetCDF_phys_Vars ={'U':'vozocrtx', 'V':'vomecrty', 'T':'votemper', 'S':'vosaline'}
NetCDF_phys_Files={'U':'U', 'V':'V', 'T':'T', 'S':'S'}

class mask():
    def __init__(self, filename=None,loadtmask=True):
        if filename is None:
            self.Lat = 0.
            self.Lon = 0.
            self.Depth = 0.
            self.jpk   = 0
            self.tmask = 0
            self.jpi   = 0
            self.jpj   = 0
        else:
            dset = netCDF4.Dataset(filename)
            if "nav_lat" in dset.variables:
                    ylevels  = np.array(dset.variables["nav_lat"])
                    self.Lat = ylevels[:,0]
            if "lat" in dset.variables:
                    self.Lat  = np.array(dset.variables["lat"])
            if "nav_lon" in dset.variables:
                    xlevels  = np.array(dset.variables["nav_lon"])
                    self.Lon = xlevels[0,:]
            if "lon" in dset.variables:
                    self.Lon  = np.array(dset.variables["lon"])

            if "depth"   in dset.variables: self.Depth = np.array(dset.variables["depth"])
            if "nav_lev" in dset.variables: self.Depth = np.array(dset.variables["nav_lev"])
            
            try:
                self.CellBottoms = np.array(dset.variables['CellBottoms'])
            except:
                self.CellBottoms = None
                
            if ("tmask" in dset.variables) and (loadtmask):
                m = dset.variables["tmask"]
                if len(m.shape) == 4:
                    self.tmask = np.array(m[0,:,:,:], dtype=np.bool)
                elif len(m.shape) == 3:
                    self.tmask = np.array(m[:,:,:], dtype=np.bool)
                elif len(m.shape) == 2:
                    self.tmask = np.array(m[:,:], dtype=np.bool)

            else:
                self.tmask = None
            dset.close()
            self.delta = self.Lon[1] - self.Lon[0]
            self.jpk = self.Depth.size
            self.jpi = self.Lon.size
            self.jpj = self.Lat.size
    def CellArea(self,side,nCells):
        '''
        Arguments:
        * side   * string, can be 'E','S','W' or 'N'
        * nCells * integer, read on xls river file 
        '''
        Radius=6371000.0  #m
        Depth = self.CellBottoms[nCells-1]
        E_width= np.deg2rad(self.delta)*Radius
        if side is "E" or side is "W":
            return E_width*Depth
        if side is "S":
            return E_width*Depth*np.sin(self.Lat[0])
        if side is "N":
            return E_width*Depth*np.sin(self.Lat[-1])            
     


def vertical_plane_interpolator(mask2,mask1,M2d,side):
    '''Interpolates a 2d vertical matrix by using horizontal profiles
    M2d size is [jpk, LonSize, or LatSize]
    '''

    if side is 'E' or side is 'W' :
        M=np.zeros((mask2.jpk,mask2.Lat.size),dtype=np.float32)
        X1 = mask1.Lat
        X2 = mask2.Lat
    if side is 'N' or  side is 'S' :        
        M=np.zeros((mask2.jpk,mask2.Lon.size),dtype=np.float32)
        X1 = mask1.Lon
        X2 = mask2.Lon
            
    if np.isnan(M2d).all():
        M[:,:]=np.NaN
        return M
    
    
    for jk in range(mask2.jpk):
        jkb, jka, t_interp= data_for_linear_interp(mask1.Depth, mask2.Depth[jk])        
        Horizontal_Profile_b = M2d[jkb,:]
        Horizontal_Profile_a = M2d[jka,:]
        waterpoints_b = ~np.isnan(Horizontal_Profile_b)
        waterpoints_a = ~np.isnan(Horizontal_Profile_a)
        
        if waterpoints_b.any():
            Horiz_Profile_new_b = np.interp(X2, X1[waterpoints_b], Horizontal_Profile_b[waterpoints_b])
        if waterpoints_a.any():
            Horiz_Profile_new_a = np.interp(X2, X1[waterpoints_a], Horizontal_Profile_b[waterpoints_a])
                    
        M[jk,:] =  Horiz_Profile_new_b * (1-t_interp ) + Horiz_Profile_new_a * t_interp
        
            # Non lo calcola e si tiene il precedente, che ha sicuramente gia' calcolato
    return M

def space_interpolator(mask2,mask1,M3d):
    '''Interpolates a 3d matrix using latitudinal slices
    '''
    
    nLon = mask2.Lon.size
    nLat = mask2.Lat.size
    M = np.zeros((mask2.jpk, nLat, nLon),np.float32)
    for j in range(nLat):
        jib, jia, t_interp=data_for_linear_interp(mask1.Lat, mask2.Lat[j]);        
        M2db = vertical_plane_interpolator(mask2,mask1, M3d[:,jib,:],'S')
        M2da = vertical_plane_interpolator(mask2,mask1, M3d[:,jia,:],'S')
        # communicate not nans each other ##########
        ii=np.isnan(M2db); jj=np.isnan(M2da) 
        M2db[ii & ~jj]=M2da[ii & ~jj]
        M2da[jj & ~ii]=M2db[jj & ~ii]
        ############################################
        M[:,j,:] = M2db * (1-t_interp) + M2da*t_interp
    return M

def space_intepolator_plane(mask2,mask1, M3d):
    '''Interpolates a 3d matrix using horizontal slices
    '''
    #X1,Y1 = np.meshgrid(mask1.Lon,mask1.Lat)
    #X2,Y2 = np.meshgrid(mask2.Lon,mask2.Lat)
    M3d_out = np.zeros((mask2.jpk, mask2.jpj, mask2.jpi), np.float32) * np.nan
    
    for k in range(mask2.jpk):
        A = SeaOverLand(M3d[k,:,:],30)
        f = interpolate.interp2d(mask1.Lon,mask1.Lat,A,kind='linear')
        M3d_out[k,:,:] = f(mask2.Lon,mask2.Lat)

    M3d_out[~mask2.tmask] = np.nan
    
    if np.isnan(M3d_out[mask2.tmask]).any() : 
        print("nans in space_interpolator_plane:",  np.isnan(M3d_out[mask2.tmask]).sum())
        for k in range(mask2.jpk):
            a = M3d_out[k,:,:]
            lev_mask = mask2.tmask[k,:,:]
            print(k, np.isnan(a[lev_mask]).sum())
        
    return M3d_out

def space_intepolator_griddata(mask2,mask1, M3d):
    '''Interpolates a 3d matrix using horizontal slices
    '''
    X1,Y1 = np.meshgrid(mask1.Lon,mask1.Lat)
    X2,Y2 = np.meshgrid(mask2.Lon,mask2.Lat)
    M3d_out = np.zeros((mask2.jpk, mask2.jpj, mask2.jpi), np.float32) * np.nan
    
    
    for k in range(mask2.jpk):
        jkb, jka, t_interp= data_for_linear_interp(mask1.Depth, mask2.Depth[k])
        tmask1 = (M3d[jkb,:,:]<1.e+19) & ~np.isnan(M3d[jkb,:,:]) # indipendent from umask, vmask, or tmask
        #tmask1 = mask1.tmask[jkb,:,:]
        if tmask1.sum() == 0 :
            print('All nans, return to upper layer ')
            jkb = jkb -1
            #tmask1 = mask1.tmask[jkb,:,:]
            tmask1 = (M3d[jkb,:,:]<1.e+19) & ~np.isnan(M3d[jkb,:,:])
        
        Map2d = M3d[jkb,:,:]
        nP = tmask1.sum()
        points = np.zeros((nP,2), np.float32)
        points[:,0] = X1[tmask1]
        points[:,1] = Y1[tmask1]
        values   = Map2d[tmask1]
        MAP2d_nearest =interpolate.griddata( points, values, (X2, Y2), 'nearest', fill_value=np.nan)
        M3d_out[k,:,:] = MAP2d_nearest

    #M3d_out[~mask2.tmask] = np.nan # in order to avoid problems
    
    if np.isnan(M3d_out[mask2.tmask]).any() : 
        print("nans in space_interpolator_griddata:",  np.isnan(M3d_out[mask2.tmask]).sum())
        for k in range(mask2.jpk):
            a = M3d_out[k,:,:]
            lev_mask = mask2.tmask[k,:,:]
            print(k, np.isnan(a[lev_mask]).sum())
        
    return M3d_out


def side_tmask(side,mask):
    if side is "N" : tmask = mask.tmask[:,-1,:]
    if side is "S" : tmask = mask.tmask[:,0,:]
    if side is "E" : tmask = mask.tmask[:,:,-1]
    if side is "W" : tmask = mask.tmask[:,:,0]    
    return tmask

def zeroPadding(side,mask):
    if side is 'E' or side is 'W':
        return np.zeros((mask.jpk, mask.Lat.size),dtype=np.float32)
    if side is "S" or side is "N":
        return np.zeros((mask.jpk, mask.Lon.size),dtype=np.float32)