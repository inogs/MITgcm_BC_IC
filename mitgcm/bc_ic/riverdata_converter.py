import argparse
def argument():
    parser = argparse.ArgumentParser(description = '''
    Generates discharge data text file for
    Prints in stdout
    ''')
    
    parser.add_argument(   '--inputfile', '-i',
                                type = str,
                                default = None,
                                required = True,
                                help ='''/some/path/  Directory containg files to interpolate. 
                                '''
                                )

    return parser.parse_args()

args = argument()


import numpy as np
from datetime import datetime


mydtype=[('date','U20'),('Q',np.float32)]

A=np.loadtxt(args.inputfile, dtype=mydtype, delimiter=',',skiprows=2)

ndays=len(A)
for i in range(ndays):
    s=datetime.strptime(A['date'][i],'%Y-%m-%dT%H:%M:%SZ').strftime("%Y%m%d-%H:%M:%S")
    print(s,A['Q'][i])