import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    Produces files for 
    ''', formatter_class=argparse.RawTextHelpFormatter)
 
 
    parser.add_argument(   '--inputfile','-i',
                                type = str,
                                required = True,
                                help = 'Path of squerin riv file')
    parser.add_argument(   '--outputfile','-o',
                                type = str,
                                required = True,
                                help = 'Path of file for read_XLS')
    parser.add_argument(   '--timelist','-t',
                                type = str,
                                required = True,
                                help = 'Path of timelist file')


 
 
    return parser.parse_args()
 
args = argument()

import numpy as np

river_orig=args.inputfile
times     =args.timelist

TIMES = np.loadtxt(times, dtype=[('time',"S17")])
DATA  = np.loadtxt(river_orig, dtype=[('riv',np.float32)])

n=len(DATA)

OUT=np.zeros((n,),dtype=[('time',"S17"), ('riv',np.float32)])
OUT['time']=TIMES
OUT['riv']=DATA

np.savetxt(args.outputfile, OUT, "%s %.3f")

