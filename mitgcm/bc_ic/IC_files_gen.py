import argparse
from bitsea.utilities.argparse_types import existing_dir_path,generic_path



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
        "--inputdir", "-i", type=existing_dir_path, required=True, help="/some/path/"
    )

    parser.add_argument(
        "--outmaskfile",
        "-m",
        type=str,
        required=True,
        help="/some/path/outmask.nc",
    )
    parser.add_argument(
        "--outputdir", "-o", type=generic_path, required=True, help="/some/path/"
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

import os
import numpy as np
from bitsea.commons import netcdf4
from bitsea.commons.dataextractor import DataExtractor
from bitsea.commons.mask import Mask

from bitsea.commons.utils import file2stringlist
from mitgcm.bc_ic.general import space_intepolator_griddata



def gen_ic_files(
    *, inputdir, outputdir, nativemask, time, outmaskfile, modelvarlist
):
    INPUTDIR = inputdir
    OUTPUTDIR = outputdir
    OUTPUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTPUTDIR / "CHECK").mkdir(parents=True, exist_ok=True)
    TIMELIST = file2stringlist(time)
    #Mask_bitsea1 = Mask(nativemask)
    Mask1 = Mask(nativemask)
    Mask2 = Mask(outmaskfile)

    if modelvarlist:
        MODELVARS = modelvarlist

        for var in MODELVARS:
            inputfile = INPUTDIR / ("ave." + TIMELIST[0] + "." + var + ".nc")
            outBinaryFile = OUTPUTDIR / ("IC_" + var + ".dat")
            B = DataExtractor(Mask1, inputfile, var).values

            M = space_intepolator_griddata(Mask2, Mask1, B)
            checkfile = OUTPUTDIR / "CHECK" / ("IC_" + var + ".nc")
            netcdf4.write_3d_file(M, var, checkfile, Mask2, compression=True)
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
