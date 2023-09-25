import os
import cfgrib
import netCDF4
import numpy as np
from datetime import datetime, timedelta
from scipy.interpolate import griddata

# utility functions

def decumulate(x):
    diff = np.diff(x, axis=0)
    return np.insert(diff, 0, diff[0], axis=0)

def deaverage(x):
    n = x.shape[0]
    dim = x.ndim
    new_shape = [1] * dim
    new_shape[0] = n
    diff = np.diff(x * np.arange(1, n + 1).reshape(new_shape), prepend=0, axis=0)
    return np.insert(diff, 0, diff[0], axis=0)

def zero_clamp(x):
    return np.maximum(0, x)

def prepare_data(var, *, transformations=[], conversion=1.0):
    var_numpy = var.to_numpy()
    for transformation in transformations:
        var_numpy = transformation(var_numpy)
    return (var_numpy * conversion).astype(np.float32)

def tomorrow(today: str) -> str:
    format = '%Y%m%d00'
    current = datetime.strptime(today, format)
    current += timedelta(days=1)
    return datetime.strftime(current, format)



# utility classes

class VariablesGroup:
    def __init__(self, filters: dict[str, str], names: list[str, str]):
        self.filters = {'filter_by_keys': filters}
        self.names = names


class GRIBFile:
    def __init__(self, filepath: str, variables_groups: list[VariablesGroup]):
        self._filepath = filepath
        self._groups = variables_groups
        self._data = dict()

        for group in self._groups:
            with cfgrib.open_dataset(self._filepath, engine='cfgrib', errors='ignore', backend_kwargs=group.filters) as file:
                self._data.update({out_data: getattr(file, in_data) for in_data, out_data in group.names.items()})
                self._lat = file.latitude
                self._lon = file.longitude

    def __getitem__(self, key: str):
        return self._data[key]

    def get_mesh(self):
        return self._lat, self._lon



# main class

class DataExtractor:
    def __init__(self, lsm_fp: str, inst_fp: str, acc_fp: str, avg_fp: str, out_mesh_fp: str):
        # define VariablesGroup
        lsm_v = VariablesGroup({'stepType': 'instant'}, {'lsm': 'lsm'})
        inst_ground_v = VariablesGroup({'stepType': 'instant', 'typeOfLevel': 'meanSea'}, {'msl': 'msl'})
        inst_surface_v = VariablesGroup({'stepType': 'instant', 'typeOfLevel': 'surface'}, {'t': 't'})
        inst_above2_v = VariablesGroup({'stepType': 'instant', 'typeOfLevel': 'heightAboveGround', 'level': 2}, {'t2m': 't2m', 'd2m': 'd2m'})
        inst_above10_v = VariablesGroup({'stepType': 'instant', 'typeOfLevel': 'heightAboveGround', 'level': 10}, {'v10': 'v10', 'u10': 'u10'})
        acc_v = VariablesGroup({'stepType': 'accum'}, {'tp': 'tp'})
        avg_v = VariablesGroup({'stepType': 'avg'}, {'ASWDIR_S': 'ASWDIR_S', 'ASWDIFD_S': 'ASWDIFD_S', 'ATHD_S': 'ATHD_S'})

        # define GRIBFiles
        lsm_file = GRIBFile(lsm_fp, [lsm_v])
        inst_file = GRIBFile(inst_fp, [inst_ground_v, inst_surface_v, inst_above2_v, inst_above10_v])
        acc_file = GRIBFile(acc_fp, [acc_v])
        avg_file = GRIBFile(avg_fp, [avg_v])

        # merge dictionaries
        self._data = {**lsm_file._data, **inst_file._data, **acc_file._data, **avg_file._data}

        # extract lat e lon mesh
        lat, lon = lsm_file.get_mesh()
        in_mesh = lat.to_numpy(), lon.to_numpy()

        # extract land-sea mask
        lsm = lsm_file['lsm'].to_numpy()
        self._sea_mask = lsm < 0.5
        self._land_mask = lsm >= 0.5
        self._flatten_sea_mesh = np.array(in_mesh)[:, self._sea_mask].T
        self._flatten_land_mesh = np.array(in_mesh)[:, self._land_mask].T

        # load output mesh
        with netCDF4.Dataset(out_mesh_fp) as out_meshfile:
            lat_mesh, lon_mesh = np.array(out_meshfile.variables['lat']), np.array(out_meshfile.variables['lon'])
            self._out_mesh = tuple(np.meshgrid(lat_mesh, lon_mesh))


    def _create_interpolation(self, var):
        flatten_sea_values = var[:, self._sea_mask].T
        flatten_land_values = var[:, self._land_mask].T
        interpolation_sea = griddata(self._flatten_sea_mesh, flatten_sea_values, self._out_mesh, method='linear')
        interpolation_land = griddata(self._flatten_land_mesh, flatten_land_values, self._out_mesh, method='nearest')
        out_land_mask = np.isnan(interpolation_sea)
        interpolation_sea[out_land_mask] = interpolation_land[out_land_mask]
        return np.transpose(interpolation_sea, axes=(2,0,1))

    
    def write_binaries(self, varNames: list[str], outdir: str, today_date: str):
        output = list()

        append = lambda data: output.append(self._create_interpolation(data).copy())
        tomorrow_date = tomorrow(today_date)

        # compute humidity starting from dew point and pressure
        td = self._data['d2m'] - 273.15
        e = 6.112 * np.exp((17.76 * td) / (td + 243.5))
        q = (0.622 * e) / (0.01 * self._data['msl'] - 0.378 * e)

        append(prepare_data(q))
        append(prepare_data(self._data['ATHD_S'], transformations=[deaverage]))
        append(prepare_data(self._data['ASWDIR_S'] + self._data['ASWDIFD_S'], transformations=[deaverage, zero_clamp]))
        append(prepare_data(self._data['tp'], transformations=[decumulate, zero_clamp], conversion=1.0/3.6e6))
        append(prepare_data(self._data['msl'], conversion=1e-2))
        append(prepare_data(self._data['u10']))
        append(prepare_data(self._data['v10']))
        append(prepare_data(self._data['t']))   

        for (data, varName) in zip(output, varNames):
            today_filename = f'{outdir}/BC_{today_date}_{varName}'
            tomorrow_filename = f'{outdir}/BC_{tomorrow_date}_{varName}'

            with open(today_filename, 'wb') as f:
                f.write(data[1:25])

            with open(tomorrow_filename, 'wb') as f:
                f.write(data[25:49])