import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    For each original binary file, which concatenates 365 frames,in:
    - Kext_CADEAU_365.dat
    - N1p_surface_fluxes_V3.dat
    - N3n_surface_fluxes_V3.dat
    - N_bottom_fluxes_V5_x2.dat
    - O_bottom_fluxes_V3_bis.dat
    - P_bottom_fluxes_V5_x3.dat

    generates an equivalent one, based on provided timelist.
    Last frame is replicated
    ''',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(   '--inputdir', '-i',
                                type = str,
                                required = True,
                                help = ''' Dir with original N_bottom_fluxes_V5_x2.dat '''
                                )
    parser.add_argument(   '--outdir', '-o',
                                type = str,
                                required = True
                                )
    parser.add_argument(   '--maskfile', '-m',
                                type = str,
                                required = True,
                                help = ''' Path of the meshmask file'''
                                )
    parser.add_argument(   '--timelist', '-t',
                                type = str,
                                required = True,
                                help = ''' timelist file'''
                                )

    return parser.parse_args()

args = argument()

import numpy as np
from commons.mask import Mask
from commons.utils import addsep
from commons.utils import file2stringlist
from datetime import datetime

def readFrame_from_file(filename,Frame,shape):
    jpk,jpj,jpi=shape
    domain_size=jpi*jpj*jpk
    fid=open(filename,'rb')
    fid.seek(domain_size*Frame*4)
    A=np.fromfile(fid,dtype=np.float32,count=domain_size)
    fid.close()
    return A.reshape(jpk,jpj,jpi)

INPUTDIR=addsep(args.inputdir)
OUTDIR = addsep(args.outdir)
Timelist = file2stringlist(args.timelist)
TheMask = Mask(args.maskfile)
jpk,jpj,jpi = TheMask.shape


filelist=["Kext_CADEAU_365.dat",
          "N1p_surface_fluxes_V3.dat",
          "N3n_surface_fluxes_V3.dat",
          "N_bottom_fluxes_V5_x2.dat",
          "O_bottom_fluxes_V3_bis.dat",
          "P_bottom_fluxes_V5_x3.dat"]

for filename in filelist:
    inputfile=INPUTDIR + filename
    outfile=OUTDIR + filename
    print(outfile,flush=True)
    F = open(outfile,'wb')
    for timestr in Timelist:
        d=datetime.strptime(timestr,"%Y%m%d-%H:%M:%S")
        julianday = int(d.strftime("%j"))
        A = readFrame_from_file(inputfile, julianday-1, (1, jpj, jpi))
        F.write(A)
    F.write(A)
    F.close()








