#
import numpy as np
import pandas as pd
import scipy.signal as sgnl
import xarray as xr
import json

import bathyMER_t1 as batload
import grid

pi = np.pi
sin = np.sin
cos = np.cos
d2r = np.deg2rad
R0 = 6371.e3 #Earth radius in m

#

def load_config(
        config_file: str,
) -> tuple:
    """Loads info defining the domain of interest from .json file.
    Args:
        config_file (string): file name where to find domain config
    Returns:
        arrays of longitude and latitude for the domain
    """

    with open(config_file, 'r') as jfile:
        jdata = json.load(jfile)
    res = jdata["resolution"]
    xg0, yg0 = jdata["minimum_longitude"], jdata["minimum_latitude"]
    n_x = int((jdata["maximum_longitude"] - jdata["minimum_longitude"]) / res)
    n_y = int((jdata["maximum_latitude"] - jdata["minimum_latitude"]) / res)
    lon_domain = np.linspace(jdata["minimum_longitude"] + res * .5, jdata["maximum_longitude"] - res * .5, n_x)
    lat_domain = np.linspace(jdata["minimum_latitude"] + res * .5, jdata["maximum_latitude"] - res * .5, n_y)
    max_depth = jdata["maximum_depth"]
    hFacMin = jdata["minimum_h-factor"]

    return xg0, yg0, res, n_x, n_y, lon_domain, lat_domain, max_depth, hFacMin

def load_bathy():
    ds = batload.main()
    z = ds.elevation
    z = z.where(z < 0., np.nan)
    z = batload.remove_puddles(z)#.values)
    z = z.where(z == z, 0.)
    return z.values

def spatial_arrays(
        n_x,
        n_y,
        xg0,
        yg0,
        dxF,
        dyF,
        first_layer_height = 1.,
        extra_depth = 20.,
):
    max_depth = -np.nanmin(load_bathy())
    del_z = grid.generate_level_heights(first_layer_height, max_depth, extra_depth)
    n_z = len(del_z)

    xg = xg0 + np.linspace(0, n_x, n_x + 1) * dxF
    yg = yg0 + np.linspace(0, n_y, n_y + 1) * dyF
    xc = 0.5 * (xg[1:] + xg[:-1])
    yc = 0.5 * (yg[1:] + yg[:-1])

    XG, YG = np.meshgrid(xg, yg)
    XC, YC = np.meshgrid(xc, yc)

    Dxf, Dyf = np.meshgrid(np.array([dxF] * n_x), np.array([dyF] * n_y))
    XCm = d2r(Dxf) * R0 * cos(d2r(YC))
    YCm = d2r(Dyf) * R0

    zg = np.zeros(n_z + 1)
    zg[1:] = np.cumsum(del_z)
    zc = 0.5 * (zg[1:] + zg[:-1])
    zt = zg[:-1]  # top faces
    zb = zg[1:]  # bottom faces

    space_dict = {'xg': xg, 'yg': yg, 'xc': xc, 'yc': yc,
                 'zg': zg, 'zc': zc, 'zt': zt, 'zb': zb,
                 'XC': XC, 'YC': YC, 'XG': XG, 'YG': YG,
                 'Dxf': Dxf, 'Dyf': Dyf, 'XCm': XCm,
                 'YCm': YCm, 'delZ': del_z}
    return space_dict, n_z

### compute hFacC = lopping factors for partial cells
def hFac_Depth_calc(zt,
        del_z,
        bathy,
        hFacMin,
        n_x,
        n_y,
        n_z,
):
    Zt = -np.ones((n_z, n_y, n_x)) * np.array([[zt]]).T
    Dz = np.ones_like(Zt) * np.array([[del_z]]).T
    onesZ = np.ones_like(Zt)
    zerosZ = np.zeros_like(Zt)

    hFac_loc = (Zt - bathy)/Dz
    hFac_loc = np.min([onesZ, np.max([zerosZ, hFac_loc], axis = 0)], axis = 0)
    hFacC = np.where((hFac_loc < hFacMin*0.5) | (bathy >= 0.), 0., np.max([hFacMin*onesZ, hFac_loc], axis = 0))

    #bathyNew = -np.sum(hFacC * Dz, axis = 0)
    hFac_loc = Zt / Dz
    hFac_loc = hFacC - np.max([hFac_loc, zerosZ], axis = 0)
    hFac_loc = np.max([hFac_loc, zerosZ], axis = 0)
    hFacC = np.where(hFac_loc < hFacMin * 0.5, 0., np.max([hFac_loc, hFacMin * onesZ], axis = 0)) #* np.where(bathy != 0., 1., 0.)
    #hFacC = np.where(hFac_loc < hFacMin * 1, 0., np.max([hFac_loc, hFacMin * onesZ], axis=0))

    Depth = np.sum(hFacC * Dz, axis = 0)

    hFacW = np.zeros_like(hFacC)
    hFacW[:,:,0] = hFacC[:,:,0]
    hFacW[:,:,1:] = np.min([hFacC[:,:,:-1], hFacC[:,:,1:]], axis = 0)

    hFacS = np.zeros_like(hFacC)
    hFacS[:,0,:] = hFacC[:,0,:]
    hFacS[:,1:,:] = np.min([hFacC[:,:-1,:], hFacC[:,1:,:]], axis = 0)
    return hFacC, hFacW, hFacS, Depth
#

# check for stagnation points and create new bathymetry without them
def stagnation_counter(hFacC,
):
    stagnation_pnts_N = 0
    window = np.array([[0,1,0], [1,0,1], [0,1,0]])
    for k in range(hFacC.shape[0]):
        hFac_conv = sgnl.convolve2d(hFacC[k,:,:], window)[1:-1, 1:-1] / 4
        stagnation_pnts_N += np.sum((hFac_conv == 0.) & (hFacC[k,:,:] != 0.))
    return stagnation_pnts_N

def stagnation_remover(hFacC,
       bathy,
):
    bathyNew = np.zeros_like(bathy)
    windN = np.array([[0,1,0], [0,0,0], [0,0,0]])
    windE = np.array([[0,0,0], [0,0,1], [0,0,0]])
    windS = np.array([[0,0,0], [0,0,0], [0,1,0]])
    windW = np.array([[0,0,0], [1,0,0], [0,0,0]])
    window = np.array([[0,1,0], [1,0,1], [0,1,0]])
    for k in range(hFacC.shape[0]):
        hFac_conv = sgnl.convolve2d(hFacC[k,:,:], window)[1:-1, 1:-1] / 4 ###
        bathyConvN = sgnl.convolve2d(bathy, windN)[1:-1, 1:-1]
        bathyConvE = sgnl.convolve2d(bathy, windE)[1:-1, 1:-1]
        bathyConvS = sgnl.convolve2d(bathy, windS)[1:-1, 1:-1]
        bathyConvW = sgnl.convolve2d(bathy, windW)[1:-1, 1:-1]
        bathysConv = [bathyConvN, bathyConvE, bathyConvS, bathyConvW]
        bathyNew = np.where((hFac_conv == 0.) & (hFacC[k,:,:] != 0.) & (bathyNew == 0.), np.min(bathysConv, axis = 0), bathyNew)
    bathyNew = np.where(bathyNew == 0., bathy, bathyNew)
    return bathyNew

### create meshmash.nc à la gbolzon
def meshmasker(XCm,
       YCm,
       XC,
       YC,
       n_z,
       del_z,
       zc,
       hFacC,
       hFacMin,
       nameFile,
       outDir,
       new_e3t = True,
):
    dty = np.float64
    e1t = np.array([[XCm]], dtype = dty)
    e2t = np.array([[YCm]], dtype = dty)
    e3t = np.array([[[del_z]]], dtype = dty).reshape(1,n_z,1,1)
    glamt = np.array([[XC]], dtype = dty)
    gphit = np.array([[YC]], dtype = dty)
    # create tmask from hFacC
    tmask = np.array([np.where(hFacC < hFacMin/2, 0, 1)], dtype = dty)
    #tmask = np.array([np.where(np.where(hFacC == hFacC, hFacC, 0) < hFacMin, 0, 1)], dtype = dty)
    if new_e3t:
        #e3t = (hFacC * e3t).astype(dty)
        e3t = (np.where(tmask == 0., 0., e3t)).astype(dty)
        dsVars = {'e1t': (['time', 'z_a', 'y', 'x'], e1t), 'e2t': (['time', 'z_a', 'y', 'x'], e2t),
                  'e3t': (['time', 'z', 'y', 'x'], e3t), 'glamt': (['time', 'z_a', 'y', 'x'], glamt),
                  'gphit': (['time', 'z_a', 'y', 'x'], gphit), 'nav_lat': (['y', 'x'], np.array(YC, dtype = dty)),
                  'nav_lev': (['z'], np.array(zc, dtype = dty)), 'nav_lon': (['y', 'x'], np.array(XC, dtype = dty)),
                  'tmask': (['time', 'z', 'y', 'x'], tmask)} #'tmask_noRiver'
    else:
        dsVars = {'e1t': (['time', 'z_a', 'y', 'x'], e1t), 'e2t': (['time', 'z_a', 'y', 'x'], e2t),
                  'e3t': (['time', 'z', 'y_a', 'x_a'], e3t), 'glamt': (['time', 'z_a', 'y', 'x'], glamt),
                  'gphit': (['time', 'z_a', 'y', 'x'], gphit), 'nav_lat': (['y', 'x'], np.array(YC, dtype = dty)),
                  'nav_lev': (['z'], np.array(zc, dtype = dty)), 'nav_lon': (['y', 'x'], np.array(XC, dtype = dty)),
                  'tmask': (['time', 'z', 'y', 'x'], tmask)}
    dsDims = []
    mshmsk = xr.Dataset(dsVars)
    mshmsk.to_netcdf(f'{outDir}/{nameFile}')
#

### create MITgcm-like variables saved in NETCDF
def MITspaceNC(xc,
       yc,
       xg,
       yg,
       zc,
       zg,
       zt,
       zb,
       XCm,
       YCm,
       Depth,
       del_z,
       n_z,
       hFacC,
       hFacW,
       hFacS,
       hFacMin,
       namefile,
       outdir,
       g = 9.81,
):
    dty = np.float32
    xC = np.array(xc, dtype = dty)
    yC = np.array(yc, dtype = dty)
    xG = np.array(xg[:-1], dtype = dty)
    yG = np.array(yg[:-1], dtype = dty)
    zc = np.array(zc, dtype = dty)
    zg = np.array(zg, dtype = dty)
    zt = np.array(zt, dtype = dty)
    zb = np.array(zb, dtype = dty)
    dxc = np.array(XCm, dtype = dty) #equal for _G, _V
    dyc = np.array(YCm, dtype = dty) #equal for _G, _U
    Depth = np.array(Depth, dtype = dty)
    dzg = np.array(del_z, dtype = dty)
    dzc = np.ones(n_z+1, dtype = dty)
    dzc[0] = dzg[0] * 0.5
    dzc[1:-1] = np.abs(zc[1:] - zc[:-1])
    dzc[-1] = dzg[-1] * 0.5
    hFacC = np.array(hFacC, dtype = dty)
    hFacW = np.array(hFacW, dtype = dty)
    hFacS = np.array(hFacS, dtype = dty)
    maskC = np.array(np.where(hFacC < hFacMin*0.5, 0., 1.), dtype = dty)
    maskInC = maskC[0,:,:]
    maskW = np.array(np.where(hFacW < hFacMin*0.5, 0., 1.), dtype = dty)
    maskInW = maskW[0,:,:]
    maskS = np.array(np.where(hFacS < hFacMin*0.5, 0., 1.), dtype = dty)
    maskInS = maskS[0,:,:]
    #horizontal area of cells in m²
    #equal for all kinds of cells (rA, rAz, rAw, rAs)
    rA = XCm*YCm
    #hydrostatic pressure as reference (PHref_)
    PHrefC = np.array(np.abs(zc) * g, dtype = dty)
    PHrefF = np.array(np.abs(zg) * g, dtype = dty)

    dsVars = {'XC': (['XC'], xC), 'YC': (['YC'], yC), 'XG': (['XG'], xG), 'YG': (['YG'], yG), 'Z': (['Z'], zc),
              'Zp1': (['Zp1'], zg), 'Zu': (['Zu'], zt), 'Zl': (['Zl'], zb), 'rA': (['YC', 'XC'], rA),
              'dxG': (['YG', 'XG'], dxc), 'dyG': (['YG', 'XG'], dyc), 'Depth': (['YC', 'XC'], Depth),
              'rAz': (['YG', 'XG'], rA), 'dxC': (['YC', 'XG'], dxc), 'dyC': (['YG', 'XC'], dyc),
              'rAw': (['YC', 'XG'], rA), 'rAs': (['YG', 'XC'], rA), 'drC': (['Zp1'], dzc), 'drF': (['Z'], dzg),
              'PHrefC': (['Z'], PHrefC), 'PHrefF': (['Zp1'], PHrefF), 'hFacC': (['Z', 'YC', 'XC'], hFacC),
              'hFacW': (['Z', 'YC', 'XG'], hFacW), 'hFacS': (['Z', 'YG', 'XC'], hFacS),
              'maskC': (['Z', 'YC', 'XC'], maskC), 'maskW': (['Z', 'YC', 'XG'], maskW),
              'maskS': (['Z', 'YG', 'XC'], maskS), 'maskInS': (['YG', 'XC'], maskInS), 'dyF': (['YC', 'XC'], dyc),
              'maskInC': (['YC', 'XC'], maskInC), 'dxV': (['YG', 'XG'], dxc), 'dyU': (['YG', 'XG'], dyc),
              'maskInW': (['YC', 'XG'], maskInW), 'dxF': (['YC', 'XC'], dxc)}

    MITlike = xr.Dataset(dsVars)
    MITlike.to_netcdf(f'{outdir}/{namefile}')


def dig_rivers(
        bathy,
        rivers_file,
        config_file,
        lons,
        lats,
):
    """

    :type bathy: xr.DataArray
    """
    df = pd.read_csv(rivers_file)
    for river in df.rivername:
        side = df.loc[df['rivername'] == river].side.values[0]
        x_mouth = df.loc[df['rivername'] == river]['lon mouth'].values[0]
        idx_x = np.argmin(np.abs(lons - x_mouth))
        y_mouth =df.loc[df['rivername'] == river]['lat mouth'].values[0]
        idx_y = np.argmin(np.abs(lats - y_mouth))
        with open(config_file, 'r') as jfile:
            jdata = json.load(jfile)
        res = jdata["resolution"]

        if river == 'Po':
            digging_depth = -6.
            digging_length = 40
        else:
            digging_depth = -3.
            digging_length = 10

        #print('\t',river, side)

        if side == 'N':
            if river == 'Isonzo':
                bathy[idx_y, idx_x - digging_length+1:idx_x + 1] = digging_depth
                bathy[idx_y:idx_y+digging_length//2, idx_x-digging_length+1] = digging_depth
            elif river == 'Tagliamento':
                bathy[idx_y:idx_y + digging_length//2+1, idx_x] = digging_depth
                #bathy[idx_y+digging_length//2, idx_x-digging_length//2+1:idx_x+1] = digging_depth
            else:
                while bathy[idx_y, idx_x] == 0.: #!= bathy[idx_y, idx_x]:
                    idx_y -= 1
                if river == 'Sile':
                    bathy[idx_y:idx_y + digging_length//2, idx_x] = digging_depth
                else:
                    bathy[idx_y:idx_y + digging_length, idx_x] = digging_depth
        elif side == 'S':
            while bathy[idx_y, idx_x] == 0.: #!= bathy[idx_y, idx_x]:
                idx_y += 1
            bathy[idx_y - digging_length + 1:idx_y + 1, idx_x] = digging_depth
        elif side == 'E':
            if river == 'Timavo':
                bathy[idx_y, idx_x:idx_x + digging_length] = digging_depth
                bathy[idx_y-3:idx_y, idx_x] = digging_depth
            else:
                while bathy[idx_y, idx_x] == 0.: #!= bathy[idx_y, idx_x]:
                    idx_x -= 1
                bathy[idx_y, idx_x:idx_x + digging_length] = digging_depth
        elif side == 'W':
            while bathy[idx_y, idx_x] == 0.: #!= bathy[idx_y, idx_x]:
                idx_x += 1
            if river == 'Po':
                bathy[idx_y:idx_y+2, idx_x - digging_length + 1:idx_x + 1] = digging_depth
            else:
                bathy[idx_y, idx_x - digging_length + 1:idx_x + 1] = digging_depth

    return batload.remove_puddles(bathy)

def open_straits(
        bathy,
):
    loc_y = [[475,476], [574,575], [540,541], [477,478], [476,477]]
    loc_x = [[36,37], [272,273], [314,315], [476,478], [477,479]]
    fill_values = [-7.10, 0., 0., -14.59, -15.68]
    for k in range(len(loc_x)):
        ly = loc_y[k]
        lx = loc_x[k]
        fv = fill_values[k]
        bathy[ly[0]:ly[1], lx[0]:lx[1]] = fv
    # close Goro & co
    bathy[390, 44] = 0. #np.nan
    bathy[392, 32:42] = 0. #np.nan
    bathy[397, 57] = 0. #np.nan
    bathy = batload.remove_puddles(bathy, threshold=1000)
    bathy[(bathy == bathy) & (bathy > -3.) & (bathy < 0.)] = -3.
    return bathy

#

def main():
    config_file = 'domain_north_adriatic_extended.json'
    rivers_file = 'data/rivers_NAD_MedEAF.csv'

    xg0, yg0, res, n_x, n_y, lon_domain, lat_domain, max_depth, hFacMin = load_config(config_file)
    space_dict, n_z = spatial_arrays(n_x, n_y, xg0, yg0, res, res)

    bathy = load_bathy()  ######### 2Bchanged
    bathy = dig_rivers(bathy, rivers_file, config_file,  ######### 2Bchanged
                       space_dict['xc'], space_dict['yc'])  ######### 2Bchanged
    bathy = open_straits(bathy)  # , space_dict['xc'], space_dict['yc'])  ######### 2Bchanged
    bathy = batload.remove_puddles(bathy)  ######### 2Bchanged
    #bathy = np.fromfile('data/NADRI_bathymetry_NS_no_lagoons_no_isles_by_hand.bin', dtype = 'f4').reshape(600,1120)  ######### 2Bchanged
    import matplotlib.pyplot as plt
    plt.imshow(bathy, origin='lower', vmin = -3.);
    plt.colorbar();
    plt.gcf().set_size_inches((40, 30));
    plt.show()

    #hFacC, hFacW, hFacS, Depth = hFac_Depth_calc(space_dict['zt'], space_dict['delZ'], bathy.values, hFacMin, n_x, n_y, n_z)
    hFacC, hFacW, hFacS, Depth = hFac_Depth_calc(space_dict['zt'], space_dict['delZ'], bathy, hFacMin, n_x, n_y, n_z)
    print(stagnation_counter(hFacC))  ######### 2Bchanged
    #'''  ######### 2Bchanged
    bathy_new = stagnation_remover(hFacC, bathy)
    print(stagnation_counter(hFacC))
    # new bathymetry assuring no stagnation points
    #'''

    out_dir = 'data/'
    out_file_bathy = 'NADRI_bathymetry_NS_no_lagoons_no_isles.bin'
    #'''

    del hFacC, hFacW, hFacS, Depth
    hFacC, hFacW, hFacS, Depth = hFac_Depth_calc(space_dict['zt'], space_dict['delZ'], bathy_new, hFacMin, n_x,n_y,n_z)
    bathy_new = stagnation_remover(hFacC, bathy_new)
    #'''
    #bathy_new.astype('f4').tofile(out_dir + out_file_bathy) ### !!here!!
    bathy.astype('f4').tofile(out_dir + out_file_bathy)  ######### 2Bchanged
    #'''
    del hFacC, hFacW, hFacS, Depth
    hFacC, hFacW, hFacS, Depth = hFac_Depth_calc(space_dict['zt'], space_dict['delZ'], bathy_new, hFacMin, n_x,n_y,n_z)
    print(stagnation_counter(hFacC))

    plt.imshow(hFacC[0,:,:], origin = 'lower'); plt.colorbar(); plt.gcf().set_size_inches((20,14)); plt.show()
    hFacC.astype('f4').tofile('data/hFacC.bin')
    #'''

    out_file_mesh = 'meshmask_no_lagoons_no_isles.nc'
    meshmasker(space_dict['XCm'], space_dict['YCm'], space_dict['XC'], space_dict['YC'], n_z, space_dict['delZ'],
               space_dict['zc'], hFacC, hFacMin,
               out_file_mesh, out_dir, new_e3t=True)  # meshmask.nc lookalike
    out_file_static = 'MIT_static_no_lagoons_no_isles.nc'
    MITspaceNC(space_dict['xc'], space_dict['yc'], space_dict['xg'], space_dict['yg'], space_dict['zc'],
               space_dict['zg'], space_dict['zt'], space_dict['zb'], space_dict['XCm'], space_dict['YCm'],
               Depth, space_dict['delZ'], n_z, hFacC, hFacW, hFacS, hFacMin, out_file_static, out_dir)  # MITgcm-like

if __name__ == '__main__':
    main()
