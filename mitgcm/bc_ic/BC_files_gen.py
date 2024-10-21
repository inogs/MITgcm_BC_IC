import argparse
import os

import numpy as np
import read_river_csv
import scipy.io as NC

from .general import addsep
from .general import file2stringlist
from .general import mask
from .general import side_tmask
from .general import vertical_plane_interpolator
from .general import zeroPadding


def argument():
    parser = argparse.ArgumentParser(
        description="""
    Creates ready OBC files for MITgcm only for BIO variables.
    A boundary condition can derive from a previous run, often based on other mask,
    in that case BC_files_gen.py needs the directory containing NetCDF files of slices,
    and the corresponding nativemask, and performs a linear interpolation.
    If the boundary condition does not require a previous run
    (e.g. if it is on land) the interpdir argument must not be given.
    In any case, on each boundary the river conditions will be imposed.
    River data are provided by an xls file, whose name must be
    defined in an environment variable called RIVERDATA.

    MITgcm needs the OBC for all the time of run; then, timelist argument reflects
    the times of the MITgcm run.

    At present is parallelized over variable list.
    """
    )

    parser.add_argument(
        "--outmaskfile",
        "-m",
        type=str,
        required=True,
        help="/some/path/outmask.nc",
    )
    parser.add_argument(
        "--outputdir", "-o", type=str, required=True, help="/some/path/"
    )
    parser.add_argument(
        "--side", "-s", type=str, required=True, choices=["E", "W", "S", "N"]
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
        help=""" Path of the file containing times of BC. These times are used for reading file name of slices.""",
    )
    parser.add_argument(
        "--interpdir",
        "-i",
        type=str,
        default=None,
        help="""/some/path/SLICES/ADRI/NORTH/  Directory containg files to interpolate.
                                         This argument is optional.""",
    )

    parser.add_argument(
        "--nativemask",
        type=str,
        default=None,
        help="""NetCDF File name of the mask on which slices are defined.
                                This parameter is read only if INTERPDIR is given.
                                """,
    )
    return parser.parse_args()


def writeCheckFile(*, var, t, side, OUTPUTDIR, M, interpdir, tmask2, Mask2):
    checkfile = OUTPUTDIR + "CHECK/OBC_" + side + "." + t + "." + var + ".nc"
    Mcheck = M.copy()
    if interpdir:
        missing_value = 1.0e20
        Mcheck[~tmask2] = missing_value
    else:
        missing_value = 0

    NCout = NC.netcdf_file(checkfile, "w")
    NCout.createDimension("Lon", Mask2.Lon.size)
    NCout.createDimension("Lat", Mask2.Lat.size)
    NCout.createDimension("Depth", Mask2.jpk)
    if side in ["E", "W"]:
        ncvar = NCout.createVariable(var, "f", ("Depth", "Lat"))
    if side in ["N", "S"]:
        ncvar = NCout.createVariable(var, "f", ("Depth", "Lon"))
    setattr(ncvar, "missing_value", missing_value)
    ncvar[:] = Mcheck
    NCout.close()


def main(
    *,
    side,
    outmaskfile,
    interpdir,
    nativemask,
    outputdir,
    modelvarlist,
    timelist,
):
    Mask2 = mask(outmaskfile)
    tmask2 = side_tmask(side, Mask2)
    if interpdir:
        INTERPDIR = addsep(interpdir)
        Mask1 = mask(nativemask)
        tmask1 = side_tmask(side, Mask1)

    OUTPUTDIR = addsep(outputdir)
    MODELVARS = file2stringlist(modelvarlist)
    TIMELIST = file2stringlist(timelist)
    os.system("mkdir -p " + OUTPUTDIR)
    os.system("mkdir -p " + OUTPUTDIR + "CHECK")

    for var in MODELVARS:
        outBinaryFile = OUTPUTDIR + "OBC_" + side + "_" + var + ".dat"
        print(outBinaryFile, flush=True)
        F = open(outBinaryFile, "wb")
        if var in ["T", "S", "U", "V"]:
            Lon_Ind, Lat_Ind, C = read_river_csv.get_RiverPHYS_Data(
                side, var, TIMELIST, Mask2
            )
        else:
            Lon_Ind, Lat_Ind, Conc = read_river_csv.get_RiverBFM_Data(side, var)
        nSideRivers = Lon_Ind.size
        for t in TIMELIST:
            M = zeroPadding(side, Mask2)

            if interpdir:
                filename = INTERPDIR + "ave." + t + "." + var + ".nc"
                NCin = NC.netcdf_file(filename, "r")
                B = NCin.variables[var].data.copy()
                NCin.close()

                B[~tmask1] = np.NaN
                M = vertical_plane_interpolator(Mask2, Mask1, B, side)

            for iRiver in range(nSideRivers):
                if side in ["E", "W"]:
                    M[:, Lat_Ind[iRiver]] = Conc[iRiver]
                if side in ["S", "N"]:
                    M[:, Lon_Ind[iRiver]] = Conc[iRiver]
            # writeCheckFile()

            F.write(M)
        F.write(M)
        F.write(M)
        F.write(M)
        F.close()
    return 0


if __name__ == "__main__":
    args = argument()
    exit(
        main(
            side=args.side,
            outmaskfile=args.outmaskfile,
            interpdir=args.interpdir,
            nativemask=args.nativemask,
            outputdir=args.outputdir,
            modelvarlist=args.modelvarlist,
            timelist=args.timelist,
        )
    )
