import argparse

def argument():
    parser = argparse.ArgumentParser(description = '''
    Interpolates in time producing ave files. Reads a single input file
    It saves a NetCDF file for every time and variable
    Input data are read sequentially in time, keeping in memory only two frames,
    used to perform linear interpolation between them.
    At the moment works only on 4D files [time,depth,lat,lon]
    ''')
    parser.add_argument(   '--inputfile', '-i',
                                type = str,
                                required=True,
                                help = '')

    parser.add_argument(   '--outputdir',"-o",
                                type = str,
                                required=True,
                                help = '/some/path/')
    parser.add_argument(   '--deltaseconds',"-d",
                                type = int,
                                required=True,
                                help = 'Delta t in seconds')

    return parser.parse_args()



args = argument()

import netCDF4
from datetime import datetime,timedelta
import numpy as np
import os

def get_dict(ncObject):
    out_dict = {}
    for key in ncObject.ncattrs():
        out_dict[key] = ncObject.getncattr(key)
    return out_dict   

def addsep(string):
    if string[-1] != os.sep:
        return string + os.sep
    else:
        return  string
def readfile(filename, var, timeslice):
    '''
    Generic file reader
    '''
    D = netCDF4.Dataset(filename,"r")
    VAR = np.array(D. variables[var][timeslice,:])
    D.close()
    return VAR


def data_for_linear_interp(array,value):
    '''
    Returns minimal data useful to perform linear interpolation
    two indexes and a weight.

    Arguments:
    * array * a sorted array, meaning x in a function y=f(x)
    * value * integer or float, meaning a point x(0)

    Returns :
    * before   * integer
    * after    * integer
    * t_interp * float


    value = array[before]*(1-t_interp) + array[after]*t_interp
    '''

    if value > array[-1] :
        l = len(array)
        return l-1, l-1, 0
    for i, array_elem in enumerate(array):
        if value < array_elem: break


    after = i
    before= i-1
    t_interp = float((value-array[before]))/(array[after]-array[before])

    if after==0 :
        before=0
        t_interp=0

    return before, after, t_interp

def Time_Interpolation(Instant_datetime, TimeList):
    '''
    Returns minimal data useful to perform linear interpolation in time,
    two indexes and a weight.

    Arguments:
    Instant_datetime : a datetime object
    Timelist         : a list of sorted datetime objects

    Returns :
    * before   * integer
    * after    * integer
    * t_interp * float

    '''
    instant_seconds = int(Instant_datetime.strftime("%s"))
    array___seconds = np.array([int(date.strftime("%s"))  for date in TimeList   ])

    before, after,t_interp = data_for_linear_interp(array___seconds,instant_seconds)
    return before, after,t_interp


    
filename  = args.inputfile
OUTPUTDIR = addsep(args.outdir)
delta_new = args.deltaseconds


ncIN = netCDF4.Dataset(filename,"r")
DIMS = ncIN.dimensions
longitude=ncIN.variables['longitude']
latitude =ncIN.variables['latitude']
depth    =ncIN.variables['depth']
time     =ncIN.variables['time']
lon_dict   = get_dict(longitude)
lat_dict   = get_dict(latitude)
depth_dict = get_dict(depth)
time_dict  = get_dict(time)
global_atts= get_dict(ncIN)
VARLIST=[p for p in ncIN.variables if not p in ['depth','time','longitude','latitude']]


Dref = datetime(1970,1,1,0,0,0)
nctimes = np.array(time)
INPUT_TIMELIST= [Dref + timedelta(seconds=s) for s in nctimes ]


times_new_seconds=np.arange(nctimes[0], nctimes[-1], delta_new)
nFrames_out = len(times_new_seconds)
OUTPUT_TIMELIST = [Dref + timedelta(seconds=s) for s in  times_new_seconds]
dateFormat="%Y%m%d-%H%M%S"


def dump_outfile(filename,big_file=False, time_value=0):
    '''
    Creates the header of NetCDF file
    Arguments:
    * filename * string
    * big_file * logical, true if we want to write a file with all the time frames

    Returns:
    * ncOUT  * the handle of the output file, in order to
               allow the dump of the main variables
    '''

    ncOUT = netCDF4.Dataset(filename,'w')
    for dimName,dimValue in DIMS.items():
        if dimName=='time':
            if big_file:
                ncOUT.createDimension('time',nFrames_out)
            else:
                ncOUT.createDimension('time',None)
        else:
            ncOUT.createDimension(dimName,dimValue.size)
    for att in global_atts:setattr(ncOUT,att, global_atts[att])
    
    ncvar=ncOUT.createVariable('longitude','f','longitude')
    ncvar[:]=np.array(longitude)
    for att in lon_dict:setattr(ncvar,att, lon_dict[att])
    
    ncvar=ncOUT.createVariable('latitude','f','latitude')
    ncvar[:]=np.array(latitude)
    for att in lat_dict:setattr(ncvar,att, lat_dict[att])
    
    ncvar=ncOUT.createVariable('depth','f','depth')
    ncvar[:]=np.array(depth)
    for att in depth_dict:setattr(ncvar,att, depth_dict[att])
    

    ncvar = ncOUT.createVariable('time','d',('time',))
    if big_file:
        ncvar[:] = times_new_seconds
    else:
        ncvar[:] = time_value
    for att in time_dict:setattr(ncvar,att, time_dict[att])

    
    return ncOUT





dims=('time','depth','latitude','longitude')


for var in VARLIST:
    
    BEFORE, AFTER,T_interp = Time_Interpolation(OUTPUT_TIMELIST[0],INPUT_TIMELIST)    
    Before_DATA=readfile(filename, var, BEFORE)
    After__DATA=readfile(filename, var, AFTER )

    
    for it, t in enumerate(OUTPUT_TIMELIST):
        outfile = OUTPUTDIR  +  "ave." + t.strftime(dateFormat) +"." + var + ".nc"
        
        
        before,after,T_interp = Time_Interpolation(t,INPUT_TIMELIST)


        # condition to load following input data
        if before>BEFORE:
            BEFORE=before
            AFTER=after
            Before_DATA = After__DATA
            print("switching to time ", INPUT_TIMELIST[AFTER])
            After__DATA = readfile(filename, var, AFTER )

        Actual = (1-T_interp)*Before_DATA + T_interp*After__DATA # linear interp

        # Dump the NetCDF file
        ncOUT = dump_outfile(outfile, big_file=False, time_value=times_new_seconds[it] )
        ncvar=ncOUT.createVariable(var,'f',dims,zlib=True,fill_value=np.nan)
        ncvar[0,:]=Actual
        ncOUT.close()



ncIN.close()   
