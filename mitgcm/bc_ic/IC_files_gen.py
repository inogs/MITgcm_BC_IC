import argparse
import os

import numpy as np
import scipy.io as NC
from bitsea.commons import netcdf4
from bitsea.commons.dataextractor import DataExtractor
from bitsea.commons.mask import Mask
from bitsea.commons.utils import addsep
from bitsea.commons.utils import file2stringlist

from .general import mask
from .general import NetCDF_phys_Files
from .general import NetCDF_phys_Vars
from .general import space_intepolator_griddata


def argument():
    parser = argparse.ArgumentParser(
        description=(
            "Creates ready IC files for MITgcm both physical and "
            "biogeochemical. Since input data come from other external run,"
            "a linear interpolation is performed. If argument MODELVARLIST "
            "is given with biogeochemical variable list, IC for these BIO "
            "variables will be created. Else, physical IC will be created."
        )
    )
    parser.add_argument(
        "--inputdir", "-i", type=str, required=True, help="/some/path/"
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
        "--nativemask",
        type=str,
        required=True,
        help="NetCDF File name of the mask on which inputs are defined.",
    )
    parser.add_argument(
        "--modelvarlist",
        "-v",
        type=str,
        default=None,
        help="/some/path/filename, Do not define it to get physical IC.",
    )
    parser.add_argument(
        "--time",
        "-t",
        type=str,
        required=True,
        help="/some/path/filename. A file with an only time, the restart time",
    )

    return parser.parse_args()


def writeCheckFile(*, M, outputdir, var, Mask1, Mask2):
    Mcheck = M.copy()

    checkfile = outputdir + "CHECK/" + "IC_" + var + ".nc"
    NCout = NC.netcdf_file(checkfile, "w")
    NCout.createDimension("Lon", Mask2.Lon.size)
    NCout.createDimension("Lat", Mask2.Lat.size)
    NCout.createDimension("Depth", Mask2.jpk)
    ncvar = NCout.createVariable(var, "f", ("Depth", "Lat", "Lon"))
    setattr(ncvar, "missing_value", 1.0e20)
    ncvar[:] = Mcheck
    NCout.close()


def gen_ic_files(
    *, inputdir, outputdir, nativemask, time, outmaskfile, modelvarlist
):
    INPUTDIR = addsep(inputdir)
    OUTPUTDIR = addsep(outputdir)
    os.system("mkdir -p " + OUTPUTDIR)
    os.system("mkdir -p " + OUTPUTDIR + "CHECK")
    TIMELIST = file2stringlist(time)
    Mask_bitsea1 = Mask(nativemask)
    Mask1 = mask(nativemask)
    Mask2 = mask(outmaskfile)

    if modelvarlist:
        MODELVARS = modelvarlist

        for var in MODELVARS:
            inputfile = INPUTDIR + "ave." + TIMELIST[0] + "." + var + ".nc"
            outBinaryFile = OUTPUTDIR + "IC_" + var + ".dat"
            B = DataExtractor(Mask_bitsea1, inputfile, var).values

            M = space_intepolator_griddata(Mask2, Mask1, B)

            writeCheckFile(
                M=M, outputdir=OUTPUTDIR, var=var, Mask1=Mask1, Mask2=Mask2
            )
            F = open(outBinaryFile, "wb")
            for jk in range(Mask2.jpk):
                F.write(M[jk, :, :])
            F.close()

    else:
        MODELVARS = ["U", "V", "T", "S"]
        for var in MODELVARS:
            inputfile = (
                INPUTDIR
                + TIMELIST[0][:8]
                + "_"
                + NetCDF_phys_Files[var]
                + ".nc"
            )
            outBinaryFile = OUTPUTDIR + "IC_" + var + ".dat"

            B = netcdf4.readfile(inputfile, NetCDF_phys_Vars[var])[
                0, : Mask1.jpk, :, :
            ]
            B[~Mask1.tmask] = np.NaN

            M = space_intepolator_griddata(Mask2, Mask1, B)
            writeCheckFile()
            F = open(outBinaryFile, "wb")
            for jk in range(Mask2.jpk):
                F.write(M[jk, :, :])
            F.close()


if __name__ == "__main__":
    args = argument()
    gen_ic_files(
        inputdir=args.inputdir,
        outputdir=args.outputdir,
        nativemask=args.nativemask,
        time=args.time,
        outmaskfile=args.outmaskfile,
        modelvarlist=file2stringlist(args.modelvarlist),
    )
