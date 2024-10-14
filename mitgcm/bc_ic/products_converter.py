import argparse
import datetime
import json
from dataclasses import dataclass

import numpy as np
import xarray as xr
from bitsea.commons import netcdf4
from bitsea.commons.mask import Mask
from bitsea.utilities.argparse_types import existing_dir_path
from bitsea.utilities.argparse_types import existing_file_path
from dateutil.relativedelta import relativedelta


@dataclass
class ModelVar:
    bfm_name: str
    cmems_name: str
    dataset: str
    productID: str
    conversion_value: float = 1


def argument():
    parser = argparse.ArgumentParser(
        description="""
    Converts COPERNICUS products files for MIT chain.
    Works with MEDSEA_ANALYSISFORECAST_PHY_006_013 and MEDSEA_ANALYSISFORECAST_BGC_006_014.
    Generates ave files by cutting
    - along time dimension the product file
    - down up to the depth provided by maskfile (products could have more depths)


     """,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--inputdir",
        "-i",
        type=existing_dir_path,
        required=True,
        help="The directory wrkdir/MODEL/AVE_FREQ_1/ where chain has run.",
    )
    parser.add_argument(
        "--outputdir",
        "-o",
        type=existing_dir_path,
        required=True,
        help="Path of existing dir",
    )
    parser.add_argument(
        "--maskfile",
        "-m",
        type=existing_file_path,
        required=True,
        help="""Path for the maskfile """,
    )
    parser.add_argument(
        "--rundate",
        "-d",
        type=str,
        required=True,
        help="""Rundate in yyyymmdd format """,
    )
    parser.add_argument(
        "--config",
        "-c",
        type=existing_file_path,
        required=True,
        help="""Rundate in yyyymmdd format """,
    )

    return parser.parse_args()


def main(*, config, maskfile, rundate, inputdir, outputdir):
    variables = [ModelVar(**raw_var) for raw_var in config["variables"]]

    dateformat = "%Y%m%d-%H:%M:%S"
    mask = Mask(maskfile)
    jpk, _, _ = mask.shape

    for var in variables:
        basename = "{}-{}.nc".format(var.dataset, rundate)

        inputfile = inputdir / basename
        var_data = netcdf4.readfile(inputfile, var.cmems_name)
        time = xr.open_dataset(inputfile).time

        for it, t in enumerate(time.to_numpy()):
            d = np.datetime64(t, "s").astype(datetime.datetime)
            datestr = (d + relativedelta(hours=12)).strftime(dateformat)
            outbasename = "ave.{}.{}.nc".format(datestr, var.bfm_name)
            outfile = outputdir / outbasename
            print(outfile)
            netcdf4.write_3d_file(
                var_data[it, :jpk, :, :] * var.conversion_value,
                var.bfm_name,
                outfile,
                mask,
                thredds=True,
            )
    return 0


if __name__ == "__main__":
    args = argument()
    with open(args.config) as f:
        config = json.load(f)
    exit(
        main(
            cnofig=config,
            maskfile=args.maskfile,
            rundate=args.rundate,
            inputdir=args.inputdir,
            outputdir=args.outputdir,
        )
    )
