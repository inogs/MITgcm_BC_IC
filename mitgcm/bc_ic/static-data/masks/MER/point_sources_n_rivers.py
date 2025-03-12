import numpy as np
import xarray as xr
import pandas as pd
import json

#

def initialise_sal(
		hFac,
):
	"""
	Given the hFac mask from the static files generation,
	returns a zero-fill 3D array to be filled with
	salinity relaxation values for the bottom concentration
	point sources.
	"""

	return xr.zeros_like(hFac)

def initialise_conc_fluxes(
		hFac,
):
	"""
	Given the hFac mask from the static files generation,
	returns a zero-fill 2D array to be filled with
	concentration values for the bottom concentration
	point sources or surface river sources.
	"""

	return xr.zeros_like(hFac[0,:,:])

#

def get_spatial_masks(
		ds,
):
	"""
	Given the dataset from the static files generation,
	returns a zero-fill 2D array to be filled with
	concentration values for the bottom concentration
	point sources or surface river sources.
	"""

	depth = ds.Depth
	hFac = ds.hFacC
	xc = ds.XC
	yc = ds.YC
	zc = ds.Z

	return {'xc': xc, 'yc': yc, 'zc': zc, 'depth': depth, 'hFac': hFac}

def open_point_sources(
		json_file,
):
	"""
	Given the json of a specific domain's point sources,
	reads the data within.
	"""

	with open(json_file, 'r') as jfile:
		jdata = json.load(jfile)
	return jdata['discharge_points']

def open_river_sources(
		json_file,
):
	"""
	Given the json of a specific domain's river sources,
	reads the data within.
	"""

	with open(json_file, 'r') as jfile:
		jdata = json.load(jfile)
	return jdata['river_points']

#

def fill_sal_conc(
		relax_sal,
		conc,
		x,
		y,
		z,
		depth,
		json_data,
		water_freshener = 0.5
):
	"""
	Given the info for the point sources and the spatial static data,
	fills the relaxation salinity array, creates the salinity mask and
	fills the concentration array.
	"""

	for jd in json_data:
		lon = jd['Long']
		lat = jd['Lat']
		i = np.argmin(np.abs(x.values - lon))
		j = np.argmin(np.abs(y.values - lat))
		k = np.argmin(np.abs(z.values + depth[j,i].values))
		rel_S = jd['CMS_avgS'] - water_freshener
		c = jd['Carico_Ingresso_AE'] * jd['Dilution_factor']
		relax_sal[k,j,i] = rel_S
		conc[j,i] = c
	return relax_sal, xr.where(relax_sal == 0., 0., 1.), conc

#

def write_binary_files(
		relax_sal,
		S_mask,
		conc,
		aggregated = True,
		out_dir = 'data/',
		relax_path = 'relax_salinity.bin',
		conc_path = 'tracer_concetrations.bin',
		mask_path = 'S_source_mask_MER_V3.dat',
		aggreg_path = 'sewage_discharges.nc',
):
	"""
	Given the the relaxation salinity, salinity mask and concentration
	arrays, writes them to MITgcm-appropriate binary files.
	"""
	
	relax_sal.values.astype('f4').tofile(out_dir+relax_path)
	conc.values.astype('f4').tofile(out_dir+conc_path)
	S_mask.values.astype('f4').tofile(out_dir+mask_path)
	if aggregated:
		xr.merge([relax_sal.rename('relax_salinity'), conc.rename('tracer_conc')]).to_netcdf(out_dir+aggreg_path)

#
###

def main():
	static_path = 'data/MIT_static_no_lagoons_no_isles.nc'
	relax_salt = initialise_sal(xr.open_dataset(static_path).hFacC)
	tracer_conc = initialise_conc_fluxes(xr.open_dataset(static_path).hFacC)
	coords = get_spatial_masks(xr.open_dataset(static_path))
	
	domain = 'NAD'
	sewage_path = f'data/PointSource_wSalt_{domain}.json'
	sewers = open_point_sources(sewage_path)
	### rivers_path = '...'
	### rivers = open_river_sources(rivers_path)
	### ... 
	
	relax_salt, mask_salt, tracer_conc = fill_sal_conc(relax_salt, tracer_conc, coords['xc'], coords['yc'], coords['zc'], coords['depth'], sewers)
	write_binary_files(relax_salt, mask_salt, tracer_conc)

#

if __name__ == '__main__':
    main()
    print('DONE!')

###
