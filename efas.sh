TYPE=forecast
INPUTFILE=/g100_scratch/userexternal/vdibiagi/EFAS/MER/SHARED/download_2023_${TYPE}.netcdf4.zip
CONFIG=/g100_scratch/userexternal/gbolzon0/EFAS/MITgcm_BC_IC/static-data/masks/MER/rivers_NAD.csv


TMPDIR=/g100_scratch/userexternal/gbolzon0/EFAS/

OUTFILE=/g100_scratch/userexternal/gbolzon0/EFAS/rivers_sub.nc

python get_EFAS_daily_discharge.py -i $INPUTFILE -t $TYPE -c $CONFIG -d $TMPDIR -o $OUTFILE