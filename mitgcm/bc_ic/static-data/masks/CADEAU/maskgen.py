import argparse

import numpy as np
import scipy.io as NC


def arguments():
    parser = argparse.ArgumentParser(
        description="""
   Generates maskfile by reading bathymetry
    """,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--bathymetry",
        "-b",
        type=str,
        required=True,
        help="Path of the bathymetry file",
    )
    parser.add_argument(
        "--outputfile",
        "-o",
        type=str,
        required=True,
        help="Path of the maskfile",
    )

    return parser.parse_args()


args = arguments()
bathyfile = args.bathymetry
maskfile = args.outputfile

# fmt: off
delZ = np.array([
    1.500, 1.501, 3.234, 3.483, 3.750, 4.035, 4.339, 4.665, 5.012, 5.384,
    5.781, 6.206, 6.659, 7.144, 7.661, 8.215, 8.806, 9.437, 10.112, 10.833,
    11.603, 12.426, 13.305, 14.244, 15.247, 16.319, 17.463,
])
# fmt: on

CellBottoms = np.cumsum(delZ)
Depth = CellBottoms - delZ / 2

jpi = 494
jpj = 300
jpk = Depth.size

Lat = 43.47265625 + np.arange(jpj) * 1.0 / 128
Lon = 12.22265625 + np.arange(jpi) * 1.0 / 128

# tmask construction

fid = open(bathyfile, "rb")
domain_size = jpi * jpj
A = np.fromfile(fid, dtype=np.float32, count=domain_size).astype(np.float64)
fid.close()
Bathy = -A.reshape(jpj, jpi)

# ii=Bathy>0
# Bathy[ii] = Bathy[ii]-1.4e-07

LEVELS = np.zeros((jpj, jpi), np.int32)

for ji in range(jpi):
    for jj in range(jpj):
        if Bathy[jj, ji] == 0:
            LEVELS[jj, ji] = 0
        else:
            for jk in range(jpk):
                if CellBottoms[jk] >= Bathy[jj, ji]:
                    break
            LEVELS[jj, ji] = jk + 1

tmask = np.zeros((jpk, jpj, jpi), bool)

for ji in range(jpi):
    for jj in range(jpj):
        for jk in range(LEVELS[jj, ji]):
            tmask[jk, jj, ji] = True

rivermask = np.zeros((jpk, jpj, jpi), bool)
shift = 128
#  1 - Krka
rivermask[0:2, 160 - shift : 166 - shift, 464] = True
#  2 - Zrmanja
rivermask[0:2, 230 - shift, 414:420] = True
#  3 - HPP Senj + Crikvenica
rivermask[0:2, 344 - shift, 319:325] = True
#  4 - Bakarac + Rjecina
rivermask[0:2, 365 - shift : 371 - shift, 286] = True
#  5 - Rasa
rivermask[0:2, 319 - shift : 325 - shift, 236] = True
#  6 - Mirna
rivermask[0:2, 364 - shift, 176:182] = True
#  7 - Dragonja
rivermask[0:2, 385 - shift, 176:182] = True
#  8 - Rizana
rivermask[0:2, 395 - shift, 194:200] = True
#  9 - Timavo
rivermask[0:2, 423 - shift, 178:184] = True
# 10 - Isonzo
rivermask[0:2, 417 - shift, 165:171] = True
rivermask[0:2, 417 - shift : 422 - shift, 165] = True
# 11 - Tagliamento
rivermask[0:2, 405 - shift : 411 - shift, 112] = True
# 12 - Livenza
rivermask[0:2, 399 - shift : 405 - shift, 92 - 10] = True
# 13 - Piave
rivermask[0:2, 391 - shift : 397 - shift, 59 + 5] = True
# 14 - Sile
rivermask[0:2, 385 - shift : 391 - shift, 47 - 2] = True
# 15 - Brenta
rivermask[0:2, 347 - shift, 7:13] = True
# 16 - Adige
rivermask[0:2, 343 - shift, 9:15] = True
# 17 - Po
rivermask[0:2, 317 - shift : 319 - shift, 3:42] = (
    True  # 2 x-cells deleted from mouth for each y-row
)
rivermask[2, 317 - shift : 319 - shift, 3:43] = (
    True  # 1 x-cell deleted from mouth for each y-row
)
rivermask[0:3, 297 - shift : 319 - shift, 24] = (
    True  # 1 y-cell deleted from mouth
)
# 18 - Reno + Lamone
rivermask[0:2, 270 - shift, 2:8] = True
# 19 - Foglia
rivermask[0:2, 185 - shift, 81:87] = True

ncOUT = NC.netcdf_file(maskfile, "w")
ncOUT.createDimension("lon", jpi)
ncOUT.createDimension("lat", jpj)
ncOUT.createDimension("depth", jpk)
ncOUT.createDimension("z_a", 1)

ncvar = ncOUT.createVariable("lon", "f", ("lon",))
ncvar[:] = Lon
ncvar = ncOUT.createVariable("lat", "f", ("lat",))
ncvar[:] = Lat

ncvar = ncOUT.createVariable("depth", "f", ("depth",))
ncvar[:] = Depth

ncvar = ncOUT.createVariable("CellBottoms", "f", ("depth",))
ncvar[:] = CellBottoms

ncvar = ncOUT.createVariable("tmask", "b", ("depth", "lat", "lon"))
ncvar[:] = tmask

ncvar = ncOUT.createVariable("nav_lev", "f", ("depth",))
ncvar[:] = Depth
ncvar = ncOUT.createVariable("e3t", "f", ("z_a", "depth", "lat", "lon"))
ncvar[0, :] = tmask

ncvar = ncOUT.createVariable(
    "nav_lon",
    "f",
    (
        "lat",
        "lon",
    ),
)
lon2d = np.repeat(np.array(Lon, ndmin=2), jpj, axis=0)
lat2d = np.repeat(np.array(Lat, ndmin=2).T, jpi, axis=1)
ncvar[:] = lon2d

ncvar = ncOUT.createVariable("nav_lat", "f", ("lat", "lon"))
ncvar[:] = lat2d

ncvar = ncOUT.createVariable("e1t", "f", ("z_a", "z_a", "lat", "lon"))
ncvar[:] = 0
ncvar = ncOUT.createVariable("e2t", "f", ("z_a", "z_a", "lat", "lon"))
ncvar[:] = 0

ncvar = ncOUT.createVariable("rivermask", "b", ("depth", "lat", "lon"))
ncvar[:] = rivermask

ncOUT.close()
