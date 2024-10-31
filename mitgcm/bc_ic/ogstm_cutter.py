import argparse
import os

import numpy as np
import scipy.io as NC
from bitsea.commons.dataextractor import DataExtractor
from bitsea.commons.mask import Mask
from bitsea.commons.utils import file2stringlist

from mitgcm.bc_ic.general import addsep


def argument():
    parser = argparse.ArgumentParser(
        description=(
            "Cuts a single slice or a box in (longitude, latitude) and depth "
            "(using Mask levels) starting from BIO, ave or RST files.\n\n"
            "Output file is a cut ave file."
        )
    )
    parser.add_argument(
        "--inputdir",
        "-i",
        type=str,
        required=True,
        help=(
            "Directory where original files are stored. "
            "E.g. /some/path/MODEL/AVE_FREQ_1/"
        ),
    )
    parser.add_argument(
        "--outputdir", "-o", type=str, required=True, help="/some/path/"
    )
    parser.add_argument(
        "--side",
        type=str,
        required=False,
        choices=["N", "S", "E", "W"],
        help="If not indicated, it cuts a box corresponding to output mask  ",
    )

    parser.add_argument(
        "--modelvarlist",
        "-v",
        type=str,
        required=True,
        help="/some/path/filename",
    )
    parser.add_argument(
        "--timelist",
        "-t",
        type=str,
        required=True,
        help=(
            "Path name of the file with the time list."
            "A single time (1 row file) it can be used for IC."
            "E.g. /some/path/filename"
        ),
    )
    parser.add_argument(
        "--datatype",
        "-d",
        type=str,
        required=True,
        choices=["ave", "AVE", "RST"],
    )
    parser.add_argument(
        "--mask", "-m", type=str, required=True, help="output mask file"
    )
    parser.add_argument(
        "--nativemask", "-M", type=str, required=True, help="input mask file"
    )

    return parser.parse_args()


def nearest_ind(array, value):
    DIST = (array - value) ** 2
    ind = np.nonzero(DIST == DIST.min())  # tuple
    return int(ind[0][0])


def create_Header(*, filename, Lon, Lat, Depth):
    NCout = NC.netcdf_file(filename, "w")

    NCout.createDimension("lon", Lon.size)
    NCout.createDimension("lat", Lat.size)
    NCout.createDimension("depth", Depth.size)

    ncvar = NCout.createVariable("lon", "f", ("lon",))
    ncvar[:] = Lon
    ncvar = NCout.createVariable("lat", "f", ("lat",))
    ncvar[:] = Lat

    ncvar = NCout.createVariable("depth", "f", ("depth",))
    ncvar[:] = Depth

    return NCout


def main(
    *,
    inputdir,
    outputdir,
    datatype,
    modelvarlist,
    timelist,
    nativemask,
    _mask,
    side,
):
    INPUTDIR = addsep(inputdir)
    OUTPUTDIR = addsep(outputdir)
    datatype = datatype
    os.system("mkdir -p " + OUTPUTDIR)

    MODELVARS = modelvarlist
    TIMELIST = file2stringlist(timelist)

    #Mask_bitsea1 = Mask(nativemask)
    Mask1 = Mask(nativemask)
    Mask2 = Mask(_mask)

    if side is None:
        cut_type = "Box"
    else:
        cut_type = "side"

    cut_lon_0 = nearest_ind(Mask1.lon, Mask2.lon[0])
    cut_lon_1 = nearest_ind(Mask1.lon, Mask2.lon[-1])
    cut_lat_0 = nearest_ind(Mask1.lat, Mask2.lat[0])
    cut_lat_1 = nearest_ind(Mask1.lat, Mask2.lat[-1])
    cut_depth = nearest_ind(Mask1.zlevels, Mask2.zlevels[-1]) + 1

    Lon = Mask1.lon[cut_lon_0 : cut_lon_1 + 1]
    Lat = Mask1.lat[cut_lat_0 : cut_lat_1 + 1]

    for time in TIMELIST:
        print(time, flush=True)

        for var in MODELVARS:
            filename = "ave." + time + "." + var + ".nc"
            cutfile = OUTPUTDIR + filename

            if datatype == "RST":
                filename = "RST." + time + "." + var + ".nc"
                invar = "TRN" + var
            elif datatype == "AVE":
                filename = "ave." + time + ".nc"
                invar = var
            elif datatype == "ave":
                filename = "ave." + time + "." + var + ".nc"
                invar = var

            inputfile = INPUTDIR + filename

            try:
                M = DataExtractor(Mask1, inputfile, invar).values
            except Exception:
                raise ValueError("file %s cannot be read" % inputfile)

            NCc = create_Header(
                filename=cutfile,
                Lon=Lon,
                Lat=Lat,
                Depth=Mask1.zlevels[0:cut_depth]
            )
            if cut_type == "Box":
                ncvar = NCc.createVariable(var, "f", ("depth", "lat", "lon"))
                ncvar[:] = M[
                    :cut_depth,
                    cut_lat_0 : cut_lat_1 + 1,
                    cut_lon_0 : cut_lon_1 + 1,
                ]

            if side == "E":
                ncvar = NCc.createVariable(var, "f", ("depth", "lat"))
                ncvar[:] = M[:cut_depth, cut_lat_0 : cut_lat_1 + 1, cut_lon_1]
            if side == "W":
                ncvar = NCc.createVariable(var, "f", ("depth", "lat"))
                ncvar[:] = M[:cut_depth, cut_lat_0 : cut_lat_1 + 1, cut_lon_0]
            if side == "S":
                ncvar = NCc.createVariable(var, "f", ("depth", "lon"))
                ncvar[:] = M[:cut_depth, cut_lat_0, cut_lon_0 : cut_lon_1 + 1]
            if side == "N":
                ncvar = NCc.createVariable(var, "f", ("depth", "lon"))
                ncvar[:] = M[:cut_depth, cut_lat_1, cut_lon_0 : cut_lon_1 + 1]

            setattr(ncvar, "missing_value", 1.0e20)

            NCc.close()
    return 0


if __name__ == "__main__":
    args = argument()
    modelvarlist = file2stringlist(args.modelvarlist)
    exit(
        main(
            inputdir=args.inputdir,
            outputdir=args.outputdir,
            datatype=args.datatype,
            modelvarlist=modelvarlist,
            timelist=args.timelist,
            nativemask=args.nativemask,
            _mask=args.mask,
            side=args.side,
        )
    )
