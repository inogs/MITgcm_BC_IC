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

    MITgcm needs the OBC for all the time of run; then, timelist argument must be
    defined having in mind the times of the MITgcm run.

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
        "--timelist", "-t", type=str, required=True, help="/some/path/filename"
    )
    parser.add_argument(
        "--interpdir",
        "-i",
        type=str,
        default=None,
        help="""/some/path/SLICES/ADRI/NORTH/  Directory containg files to interpolate.
                                         This argument is optional""",
    )
    parser.add_argument(
        "--nativemask",
        type=str,
        help="""NetCDF File name of the mask on which slices are defined.
                                This parameter is read only if INTERPDIR is given.
                                """,
    )

    return parser.parse_args()


def writeCheckFile():
    checkfile = OUTPUTDIR + "CHECK/OBC_" + side + "." + t + "." + var + ".nc"
    Mcheck = M.copy()
    if args.interpdir:
        missing_value = 1.0e20
        # Mcheck[~tmask2]=missing_value
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
    timelist,
):
    Mask2 = mask(outmaskfile)
    tmask2 = side_tmask(side, Mask2)
    if interpdir:
        INTERPDIR = addsep(interpdir)
        Mask1 = mask(nativemask)
        tmask1 = side_tmask(side, Mask1)

    OUTPUTDIR = addsep(outputdir)
    TIMELIST = file2stringlist(timelist)
    os.system("mkdir -p " + OUTPUTDIR)
    os.system("mkdir -p " + OUTPUTDIR + "CHECK")

    for var in ["T", "S", "U", "V"]:
        if var == "U":
            if side in ["E", "W"]:
                Lon_Ind, Lat_Ind, C = read_river_csv.get_RiverPHYS_Data(
                    side, "V", TIMELIST, Mask2
                )
                # C = Q/Mask2.CellArea(side);
                if side == "E":
                    C = -C
            else:
                C[:, :] = 0
        if var == "V":
            if side in ["S", "N"]:
                Lon_Ind, Lat_Ind, C = read_river_csv.get_RiverPHYS_Data(
                    side, "V", TIMELIST, Mask2
                )
                # C = Q/Mask2.CellArea(side);
                if side == "N":
                    C = -C
            else:
                C[:, :] = 0
        if var in ["T", "S"]:
            Lon_Ind, Lat_Ind, C = read_river_csv.get_RiverPHYS_Data(
                side, var, TIMELIST, Mask2
            )

        outBinaryFile = OUTPUTDIR + "OBC_" + side + "_" + var + ".dat"
        print(outBinaryFile)
        F = open(outBinaryFile, "wb")

        nSideRivers = Lon_Ind.size
        for it, t in enumerate(TIMELIST):
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
                    M[:, Lat_Ind[iRiver]] = C[iRiver, it]
                if side in ["S", "N"]:
                    M[:, Lon_Ind[iRiver]] = C[iRiver, it]
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
            timelist=args.timelist,
        )
    )
