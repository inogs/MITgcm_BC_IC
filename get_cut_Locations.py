import argparse


def argument():
    parser = argparse.ArgumentParser(description = '''
    Prints out in standard output four indexes for cutting one mesh to fit another.
    Indexes are found using Nearest method.
    This output can be redirected to another executable file, in order to launch it to
    export environment varibles useful to other scripts.
    ''')
    parser.add_argument(   '--tocutmask', '-c',
                                type = str,
                                required = True,
                                help ='/some/path/mask.nc'
                                )
    
    parser.add_argument(   '--tofitmask', '-f',
                                type = str,
                                required = True,
                                help = '/some/path/outmask.nc')
    
    return parser.parse_args()

args = argument()

from general import mask,np
    
file1 = args.tocutmask
file2 = args.tofitmask
Mask1= mask(file1,loadtmask=False)
Mask2= mask(file2,loadtmask=False)


def nearest_ind(array,value):
    DIST = (array-value)**2
    ind=np.nonzero(DIST==DIST.min())# tuple
    return int(ind[0][0])


cut_lon_1= nearest_ind(Mask1.Lon, Mask2.Lon[0])
cut_lon_2= nearest_ind(Mask1.Lon, Mask2.Lon[-1])
cut_lat_1= nearest_ind(Mask1.Lat, Mask2.Lat[0])
cut_lat_2= nearest_ind(Mask1.Lat, Mask2.Lat[-1])
cut_depth= nearest_ind(Mask1.Depth, Mask2.Depth[-1])


print("export Index_W=" +str(cut_lon_1))
print("export Index_E=" +str(cut_lon_2))
print("export Index_S=" +str(cut_lat_1))
print("export Index_N=" +str(cut_lat_2))
print("export Index_T=0" )
print("export Index_B=" +str(cut_depth))

