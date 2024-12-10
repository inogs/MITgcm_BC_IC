#
import os
from collections.abc import Iterable

import numpy as np
import xarray as xr
import cc3d
import json
import pandas as pd
import geopandas as gpd
from pyproj import CRS #, Transformer
from xarray.core.formatting import dim_summary_limited


#

def load_ita_bathy(
        url: str = "https://erddap.emodnet.eu/erddap/griddap/bathymetry_2022",
        x_vertices: Iterable = (5., 21.),
        y_vertices: Iterable = (34., 48.),
        out_file: str = "ITA_bathymetry.nc",
        full_meta: bool = False,
) -> xr.Dataset:
    """Loads bathymetry from the EMODnet server and subsets to a box containing
    all the regional domains.
    Args:
        url (string): url where to find EMODnet data
        x_vertices (iteratable of floats): min and max longitude
        y_vertices (iteratable of floats): min and max latitude
        outFile (string): file name to write bathymetry to, if absent
        full_meta (bool): flag to keep all the meta- and accessory data (std,
        max-min range, interpolation flags, etc)
    Returns:
        xarray Dataset with longitude, latitude and elevation
    """

    if not os.path.isfile(out_file):
        ds = xr.open_dataset(url)
    else:
        ds = xr.open_dataset(out_file)

    if full_meta:
        ds = ds.sel(longitude=slice(x_vertices[0], x_vertices[1]),
                    latitude=slice(y_vertices[0], y_vertices[1]))
    else:
        ds = ds.elevation.sel(longitude=slice(x_vertices[0], x_vertices[1]),
                              latitude=slice(y_vertices[0], y_vertices[1])).to_dataset()

    if not os.path.isfile(out_file):
        ds.to_netcdf(out_file)

    return ds

def load_domain(
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
    n_x = int((jdata["maximum_longitude"] - jdata["minimum_longitude"]) / res)
    n_y = int((jdata["maximum_latitude"] - jdata["minimum_latitude"]) / res)
    lon_domain = np.linspace(jdata["minimum_longitude"] + res * .5, jdata["maximum_longitude"] - res * .5, n_x)
    lat_domain = np.linspace(jdata["minimum_latitude"] + res * .5, jdata["maximum_latitude"] - res * .5, n_y)
    return lon_domain, lat_domain

def interpolate_bathy(
        ds_ita: xr.Dataset,
        x_domain: np.ndarray,
        y_domain: np.ndarray,
        out_file: str = '-',
) -> xr.Dataset:
    """Interpolates the EMODnet bathymetry (resolution ~100 m) to the domain
    grid (~500 m); different methods can be used, but from tests they are
    pretty much equivalent (differences of order 1e-6).
    Args:
        ds_ita (xr.DataArray): EMODnet bathymetry cut to the Italian region
        x_domain (np.ndarray): longitude array of the domain
        y_domain (np.ndarray): latitude array of the domain
        out_file (string): file name to write bathymetry to, if absent
    Returns:
        xarray Dataset with longitude, latitude and elevation
    """

    ds_dom = ds_ita.interp(longitude=x_domain, latitude=y_domain, method='linear')
    ds_dom = xr.where(ds_dom > 0., 0, ds_dom)
    # TODO: write to file
    return ds_dom

def remove_puddles(
        ds: xr.Dataset,
        threshold: int = 500,
        noMG: bool = False,
) -> xr.Dataset:
    """Removes unconnected pixels (puddles) from the domain, leaving only ones above
    a set threshold in pixel number.
    Args:
        ds (xr.DataArray): domain bathymetry
        threshold (np.ndarray): minimum number of pixels of a puddle
        noMG (boolean): flag to close innacurate Marano-Grado lagoon in EMODnet data
    Returns:
        xarray Dataset with longitude, latitude and 'cleaned' elevation
    """

    if noMG:
        ds = remove_MG_lagoon(ds)

    if isinstance(ds, xr.Dataset):
        mask_puddles = xr.where(ds == ds, 1, 0).elevation.values * np.where(ds.elevation.values == 0., 0, 1)
    elif isinstance(ds, xr.DataArray):
        mask_puddles = xr.where(ds == ds, 1, 0).values * np.where(ds == 0., 0, 1)
    elif isinstance(ds, np.ndarray):
        mask_puddles = np.where(ds == ds, 1, 0) * np.where(ds == 0., 0, 1)
    #mask_puddles =
    puddles = cc3d.connected_components(mask_puddles, connectivity=4)
    removed_puddles = cc3d.dust(puddles, connectivity=4, threshold=threshold)
    if isinstance(ds, xr.Dataset):
        ds = ds.elevation * removed_puddles  # np.where(removed_puddles == 0., np.nan, 1)
    else:
        ds = ds * removed_puddles #np.where(removed_puddles == 0., np.nan, 1)

    return ds

def remove_isles(
        ds,
):
    idxs = [slice(1086,1088), slice(1088,1090), slice(1015,1018), slice(1017,1019), slice(900,902), 846]
    idys = [2, 1, slice(1,3), 0, 1, 1]
    sub_vals = [-25., -42., np.nan, np.nan, np.nan, np.nan]
    for ix, iy, sv in zip(idxs, idys, sub_vals):
        ds[iy, ix] = sv
    return ds

def remove_MG_lagoon(
        ds: xr.Dataset,
) -> xr.Dataset:
    """Closes MG lagoon with hardcoded values to clean bathymetry
    Args:
        ds (xr.DataArray): domain bathymetry
    Returns:
        xarray Dataset with longitude, latitude and elevation
    """
    lat_mouths = [569, 564, 563]
    lon_mouths = [213, 234, 236]
    for i in range(3):
        ds.elevation[lat_mouths[i], lon_mouths[i]] = np.nan
    return ds


def read_Venice_lagoon(
        bathy_start: xr.Dataset,
        dataLagoon,
        crss=['EPSG:3004', 'EPSG:4326'],
) -> np.ndarray:
    """Reads bathymetric data from multiple unstructured sources, interpolates on a structured grid and adds it to the
    domain bathymetry
    Args:
        bathy_start (xr.Dataset): domain bathymetry
        dataLagoon (List of strings): paths to input data
        crss (List of strings): coordinate reference systems for the input data
    Returns:
        np.ndarray with longitude, latitude and elevation
    """
    df_list = []
    z_list = []
    cntr = 0

    bathy_start = bathy_start['elevation'].where(bathy_start['elevation'] == bathy_start['elevation'], 0.)
    n_y, n_x = bathy_start.shape
    xc, yc = bathy_start.coords.values()
    xc, yc = xc.values, yc.values
    Xc, Yc = np.meshgrid(xc, yc)
    Xcf, Ycf = Xc.flatten(), Yc.flatten()

    i0, i1, j0, j1 = 0, 110, 460, 550  # select window around lagoon
    slx, sly = slice(i0, i1), slice(j0, j1)
    zoomFac = 8
    Nzx, Nzy = zoomFac * (i1 - i0 - 1) + 1, zoomFac * (j1 - j0 - 1) + 1
    xz, yz = np.linspace(xc[i0], xc[i1], Nzx), np.linspace(yc[j0], yc[j1], Nzy)
    dxz, dyz = np.diff(xz)[0], np.diff(yz)[0]
    xzg, yzg = (np.linspace(xz[0] - dxz / 2, xz[-1] + dxz / 2, Nzx + 1),
                np.linspace(yz[0] - dyz / 2, yz[-1] + dyz / 2, Nzy + 1))
    Xz, Yz = np.meshgrid(xz, yz)
    Xzf, Yzf = Xz.flatten(), Yz.flatten()

    if not os.path.isfile('VE_lagoon.npz'):
        for pn in dataLagoon:
            df = pd.read_csv(pn)
            cIn = crss[0]
            cOut = crss[1]
            crs = CRS.from_string(cOut)
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Longitude'], df['Latitude'], df['Depth']),
                                   crs=cIn).to_crs(crs=crs)

            points = gdf['geometry']
            dfLL = df.copy()
            dfLL['Longitude'] = points.x
            dfLL['Latitude'] = points.y
            dfLL['Depth'] = points.z
            df_list.append(dfLL)

            del df
            del gdf

            z_intp = np.ones((Nzy, Nzx)) * np.nan
            sumZ = np.histogram2d(points.x, points.y, weights=points.z, density=False, bins=(xzg, yzg))[0].T
            numZ = np.histogram2d(points.x, points.y, density=False, bins=(xzg, yzg))[0].T
            z_intp = sumZ / numZ
            z_list.append(z_intp)
            cntr += 1

        #np.savez('VE_lagoon.npz', z_list[0], z_list[1])
    else:
        z_list = list(np.load('VE_lagoon.npz', allow_pickle=True).values())

    masks = [np.where(zl == zl, 1, 0) for zl in z_list]
    z_fin = xr.DataArray(np.nansum(z_list, axis=0) / np.sum(masks, axis=0), coords=[yz, xz],
                         dims=['latZoom', 'lonZoom'])
    lagoon = z_fin.coarsen(latZoom=zoomFac // 2, lonZoom=zoomFac // 2, boundary='pad').mean(
        skipna=True)  # 2-steps coarsen
    lagoon = lagoon.coarsen(latZoom=2, lonZoom=2, boundary='pad').mean(skipna=False)  # 2-steps coarsen
    lagoon = np.where(lagoon == lagoon, lagoon, 0.)
    bathy_new = bathy_start * 1
    bathy_new[sly, slx] = np.where(bathy_start[sly, slx] == 0., lagoon, bathy_start[sly, slx])

    return bathy_new


def read_Grado_Marano_lagoon(
        bathy_start: xr.Dataset,
        dataLagoon,
        crss=['EPSG:3004', 'EPSG:4326'],
) -> np.ndarray:
    """Reads bathymetric data from multiple unstructured sources, interpolates on a structured grid and adds it to the
    domain bathymetry
    Args:
        bathy_start (xr.Dataset): domain bathymetry
        dataLagoon (List of strings): paths to input data
        crss (List of strings): coordinate reference systems for the input data
    Returns:
        np.ndarray with longitude, latitude and elevation
    """
    df_list = []
    z_list = []
    cntr = 0

    bathy_start = bathy_start['elevation'].where(bathy_start['elevation'] == bathy_start['elevation'], 0.)
    n_y, n_x = bathy_start.shape
    xc, yc = bathy_start.coords.values()
    xc, yc = xc.values, yc.values
    Xc, Yc = np.meshgrid(xc, yc)
    Xcf, Ycf = Xc.flatten(), Yc.flatten()

    i0, i1, j0, j1 = 170, 280, 560, 585 # select window around lagoon
    slx, sly = slice(i0, i1), slice(j0, j1)
    zoomFac = 8
    Nzx, Nzy = zoomFac * (i1 - i0 - 1) + 1, zoomFac * (j1 - j0 - 1) + 1
    xz, yz = np.linspace(xc[i0], xc[i1], Nzx), np.linspace(yc[j0], yc[j1], Nzy)
    dxz, dyz = np.diff(xz)[0], np.diff(yz)[0]
    xzg, yzg = np.linspace(xz[0] - dxz / 2, xz[-1] + dxz / 2, Nzx + 1), np.linspace(yz[0] - dyz / 2, yz[-1] + dyz / 2,
                                                                                    Nzy + 1)
    Xz, Yz = np.meshgrid(xz, yz)
    Xzf, Yzf = Xz.flatten(), Yz.flatten()

    if not os.path.isfile('MG_lagoon.npz'):
        for pn in dataLagoon:
            df = pd.read_csv(pn)
            cIn = crss[0]
            cOut = crss[1]
            crs = CRS.from_string(cOut)
            if cntr == 0:
                gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Longitude'], df['Latitude'], df['Depth']),
                                       crs=cOut).to_crs(crs=crs)
            elif cntr == 1:
                gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Longitude'], df['Latitude'], df['Depth']),
                                       crs=cIn).to_crs(crs=crs)

            points = gdf['geometry']
            dfLL = df.copy()
            dfLL['Longitude'] = points.x
            dfLL['Latitude'] = points.y
            dfLL['Depth'] = points.z
            df_list.append(dfLL)

            del df
            del gdf

            z_intp = np.ones((Nzy, Nzx)) * np.nan
            sumZ = np.histogram2d(points.x, points.y, weights=points.z, density=False, bins=(xzg, yzg))[0].T
            numZ = np.histogram2d(points.x, points.y, density=False, bins=(xzg, yzg))[0].T
            z_intp = sumZ / numZ
            z_list.append(z_intp)
            cntr += 1

        #np.savez('MG_lagoon.npz', z_list[0], z_list[1])
    else:
        z_list = list(np.load('MG_lagoon.npz', allow_pickle=True).values())

    masks = [np.where(zl == zl, 1, 0) for zl in z_list]
    z_fin = xr.DataArray(np.nansum(z_list, axis=0) / np.sum(masks, axis=0), coords=[yz, xz],
                         dims=['latZoom', 'lonZoom'])
    lagoon = z_fin.coarsen(latZoom=zoomFac // 2, lonZoom=zoomFac // 2, boundary='pad').mean(
        skipna=True)  # 2-steps coarsen
    lagoon = lagoon.coarsen(latZoom=2, lonZoom=2, boundary='pad').mean(skipna=False)  # 2-steps coarsen
    lagoon = np.where(lagoon == lagoon, lagoon, 0.)
    bathy_new = bathy_start * 1
    bathy_new[sly, slx] = np.where(bathy_start[sly, slx] == 0., lagoon, bathy_start[sly, slx])

    return bathy_new

def combine_lagoons(
        bathy_VE: np.ndarray,
        bathy_MG: np.ndarray,
        bathy_start: xr.Dataset,
) -> xr.Dataset:
    """Combines
    Args:
        bathy_VE (np.ndarray): domain bathymetry with Venice lagoon
        bathy_MG (np.ndarray): domain bathymetry with Marano-Grado lagoon
        bathy_start (xr.Dataset): original domain bathymetry
    Returns:
        xarray Dataset with longitude, latitude and elevation
    """
    mask_VE = np.where(bathy_VE == 0., 0, 1)
    mask_MG = np.where(bathy_MG == 0., 0, 1)

    bathys = [bathy_VE, bathy_MG]
    masks = [mask_VE, mask_MG]

    bathy_tot = bathy_start**0 * np.nansum(bathys, axis=0) / np.nansum(masks, axis=0)

    return bathy_tot

def main():
    final_bathy_file = 'data/NADRI_bathymetry_no_lagoons_no_isles.nc' #'data/NADRI_bathymetry.nc'
    interpolated_bathy_file = 'data/NADRI_interp.nc'
    italy_bathy_file = 'data/ITA_bathymetry.nc'
    lagoons_dir = '/home/fabio/Trieste/PhD/GoT_Isonzo_discharge/Venice_lagoon/' #'/home/fabio/PhD/PhD_Cafè/VeniceLagoon/'
    venice_bathy_file = [lagoons_dir+'Batimetria_2003CORILA_shift_40-15.csv',
                         lagoons_dir+'Bati_2013_coarsed.csv']
    grado_bathy_file = [lagoons_dir+'Planes_bathymetry_4326.csv',
                        lagoons_dir+'Channels_bathymetry.csv']
    config_file = 'domain_north_adriatic_extended.json'
    if not os.path.isfile(final_bathy_file):
        if not os.path.isfile(interpolated_bathy_file):
            ds = load_ita_bathy(out_file = italy_bathy_file)
            lon_dom, lat_dom = load_domain(config_file)
            ds_dom = interpolate_bathy(ds, x_domain=lon_dom, y_domain=lat_dom)
            ds_dom.to_netcdf(interpolated_bathy_file)
        else:
            ds_dom = xr.open_dataset(interpolated_bathy_file)
        ds_clean = remove_puddles(ds_dom, noMG = True)
        #ds_clean = dig_rivers(ds_clean, rivers_file, config_file)
        #ds_lagoons = combine_lagoons(read_Venice_lagoon(ds_clean, venice_bathy_file),
        #                             read_Grado_Marano_lagoon(ds_clean, grado_bathy_file),
        #                             ds_clean)
        #ds_lagoons = remove_puddles(ds_lagoons, threshold = 100)
        ds_clean = remove_isles(ds_clean)
        ds_lagoons = remove_puddles(ds_clean, threshold=100)
        ds_lagoons.to_netcdf(final_bathy_file)
    else:
        ds_lagoons = xr.open_dataset(final_bathy_file)

    return ds_lagoons

#

if __name__ == '__main__':
    main()
