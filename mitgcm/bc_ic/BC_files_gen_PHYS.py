import argparse
from pathlib import Path

import netCDF4 as NC
import numpy as np
import read_river_csv
from bitsea.commons import netcdf4
from bitsea.commons.utils import file2stringlist
from bitsea.commons.mask import Mask

from mitgcm.bc_ic.general import writeSideCheckFile
from mitgcm.bc_ic.general import side_tmask
from mitgcm.bc_ic.general import vertical_plane_interpolator
from mitgcm.bc_ic.general import zeroPadding


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



def main(
    *,
    side,
    outmaskfile,
    interpdir,
    nativemask,
    outputdir,
    timelist,
    rivers = None
):
    Mask2 = Mask(outmaskfile)

    if interpdir is not None:
        INTERPDIR = Path(interpdir)
        Mask1 = Mask(nativemask)
        tmask1 = side_tmask(side, Mask1)

    OUTPUTDIR = Path(outputdir)
    TIMELIST = file2stringlist(timelist)
    OUTPUTDIR.mkdir(parents=True, exist_ok=True)
    CHECK = OUTPUTDIR / "CHECK"
    CHECK.mkdir(parents=True, exist_ok=True)

    for var in ["T", "S", "U", "V"]:
        if var == "U":
            if side in ["E", "W"]:
                Lon_Ind, Lat_Ind, C = read_river_csv.get_RiverPHYS_Data(
                    side, "V", TIMELIST, Mask2
                )

                if side == "E":
                    C = -C
            else:
                C[:, :] = 0
        if var == "V":
            if side in ["S", "N"]:
                Lon_Ind, Lat_Ind, C = read_river_csv.get_RiverPHYS_Data(
                    side, "V", TIMELIST, Mask2
                )

                if side == "N":
                    C = -C
            else:
                C[:, :] = 0
        if var in ["T", "S"]:
            Lon_Ind, Lat_Ind, C = read_river_csv.get_RiverPHYS_Data(
                side, var, TIMELIST, Mask2
            )

        outBinaryFile = OUTPUTDIR / ("OBC_" + side + "_" + var + ".dat")
        print(outBinaryFile)
        if rivers is not None:
            nSideRivers = Lon_Ind.size
        else:
            nSideRivers = 0

        F = open(outBinaryFile, "wb")

        for it, t in enumerate(TIMELIST):
            M = zeroPadding(side, Mask2)

            if interpdir:
                filename = INTERPDIR / ("ave." + t + "." + var + ".nc")
                B = netcdf4.readfile(filename, var)
                B[~tmask1] = np.NaN

                M = vertical_plane_interpolator(Mask2, Mask1, B, side)

            for iRiver in range(nSideRivers):
                if side in ["E", "W"]:
                    M[:, Lat_Ind[iRiver]] = C[iRiver, it]
                if side in ["S", "N"]:
                    M[:, Lon_Ind[iRiver]] = C[iRiver, it]
            # writeCheckFile(OUTPUTDIR, M, Mask2, side,t,var, interpdir)
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
