#! /bin/bash

#SBATCH -N1 -n1
#SBATCH --time=0:06:00
#SBATCH --job-name=jobFettine
#SBATCH --account OGS21_PRACE_P
#SBATCH --partition g100_usr_prod
#SBATCH --qos=g100_qos_dbg

#cd $SLURM_SUBMIT_DIR

# su g100
module load autoload
module load intelmpi/oneapi-2021--binary
module load nco
LIBDIR=/g100_work/OGS21_PRACE_P/COPERNICUS/V8C/HOST/g100
export    HDF5_DIR=$LIBDIR
export NETCDF4_DIR=$LIBDIR
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$LIBDIR
source /g100_work/OGS21_PRACE_P/COPERNICUS/py_env_3.6.8/bin/activate
export PYTHONPATH=$PYTHONPATH:/g100_work/OGS21_PRACE_P/COPERNICUS/bit.sea


MPI="mpirun -np 1"

. ./profile.inc

DATESTART=20180101-12:00:00   
DATE__END=20180119-12:00:00 

RUNDIR=/g100_scratch/userexternal/vdibiagi/AZA/BC_IC_preparation_AZA_3 
mkdir -p $RUNDIR
HERE=$PWD 

###  INPUT DATA  ###############################

DATA_DIR=/g100_scratch/userexternal/vdibiagi/AZA/DATA

# PHYS
PHYS_DIR=$DATA_DIR/PHYS_r 
# BIO
AVE_DIR=$DATA_DIR/BIO_r 

######################################################

###  ELABORATION DIRS  ###############################

# 
DAILY_BIO_netCDF4=$AVE_DIR/netCDF4_DAILY
WEEKLY_BIO_netCDF4=$AVE_DIR/netCDF4_WEEKLY

START_PHYS=/g100_scratch/userexternal/vdibiagi/AZA/DATA/START_PHYS/
PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/AZA_Lazio/               # Original for phys IC cutted
BIOCUT_IC_DIR=$RUNDIR/BIO/IC/AZA_Lazio/                 # BIO IC cutted
#
PHYSCUT_BC_DIR=$RUNDIR/PHYS/CUTTED_SLICES               # BC slices phys
BIOCUT_BC_DIR_HIGH=$RUNDIR/BIO/CUTTED_SLICES/DAILY      # BC slices BIO high freq -> output of temporal interpolations (for weekly data)
BIOCUT_BC_DIR__LOW_W=$RUNDIR/BIO/CUTTED_SLICES/WEEKLY   # BC slices BIO low freq weekly
  
TIMEINTERP___DIR=$RUNDIR/BIO/IC/INTERPOLATED

######################################################

##### OUTPUTS,  ready for MITgcm  #################### 

BIO_BC_DIR=$RUNDIR/BC/BIO/
PHYS_BC_DIR=$RUNDIR/BC/PHYS/
BIO_IC_DIR=$RUNDIR/IC/BIO/
PHYSIC_DIR=$RUNDIR/IC/PHYS/ 

######################################################


######  FILES ########################################
TIMES_WEEKLY=$RUNDIR/weekly.txt 
TIMES_DAILY=$RUNDIR/daily.txt 
TIMELIST_START=$RUNDIR/t0.txt
 
####MASK__F=$RUNDIR/maskINGV_AF.nc # INGV mask for PHYS
MASK_PHYS=$RUNDIR/maskINGV.nc    # INGV mask for PHYS
MASK_OGSTM=$RUNDIR/mask24.nc      # BIO mask, 1/24
MASK24_Red=$RUNDIR/mask24R.nc  # reduced mask24 on the domain (here: Tyrrhenus)
MASK_128=$RUNDIR/mask128.nc    # here: Lazio mask
        
#MODELVARS=static-data/ModelVarNamesV5
#VAR_BIO_DAILY=static-data/ModelVarDailyV5
#VAR_TO_INTERP_W=static-data/ModelVarWeeklyV5
MODELVARS=/g100_scratch/userexternal/vdibiagi/AZA/ModelVarNamesV5
VAR_BIO_DAILY=/g100_scratch/userexternal/vdibiagi/AZA/ModelVarDailyV5
VAR_TO_INTERP_W=/g100_scratch/userexternal/vdibiagi/AZA/ModelVarWeeklyV5

export RIVERDATA=/g100_scratch/userexternal/vdibiagi/AZA/fiumi_squerin/river_meteo_data/discharges_AZA_Lazio_V5_tmp.xlsx 
export RIVERMETEODIR=/g100_scratch/userexternal/vdibiagi/AZA/fiumi_squerin/river_meteo_data/2018/for_readXLS
######################################################

 
if [ 1 == 1 ] ; then

### Step 0.  GET MASK INFO  ##################################### 

medmit_prex_or_die "gzip -cd static-data/masks/BGC_24/mask.nc.gz > $MASK_OGSTM " 
medmit_prex_or_die "gzip -cd static-data/masks/AZA_Lazio/mask.nc.gz > $MASK_128 "
medmit_prex_or_die "gzip -cd static-data/masks/PHYS_24/mask.nc.gz > $MASK_PHYS "

medmit_prex_or_die " python get_cut_Locations.py -c $MASK_PHYS -f $MASK_128 > $RUNDIR/set_cut_indexes_PHYS_vs_M128.sh "
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_OGSTM -f $MASK_128 > $RUNDIR/set_cut_indexes_OGSTM_vs_M128.sh "

medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_PHYS_vs_M128.sh $RUNDIR/set_cut_indexes_OGSTM_vs_M128.sh"
# getting Mask24 reduced on Lazio 
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_OGSTM_vs_M128.sh"
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_OGSTM -O $MASK24_Red"
##################################################################
fi


#if [ 1 == 0 ] ; then
### Step 1. DATA FROM ARCHIVES ########################## 
#fi


if [ 1==0 ] ; then
### Step 2. DATA FOR LINEAR TIME INTERPOLATION  #############

# We get TIMELIST_FROM from existing files

# WEEKLY
cat /dev/null > $TIMES_WEEKLY   
for I in `ls $WEEKLY_BIO_netCDF4/*B1p* `; do 
   filename=`basename $I`
   echo ${filename:4:17} >> $TIMES_WEEKLY
done

fi 

# TIMELIST_TO is generated
medmit_prex_or_die " python TimeList_generator.py --datestart $DATESTART --dateend $DATE__END --days '1' > $TIMES_DAILY "

##################################################################

### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START
DATESTART8=${DATESTART:0:8}  

if [ 1 == 0 ] ; then

## phys  ##

mkdir -p $START_PHYS

for I in `ls $START_PHYS/*${DATESTART8}* ` ; do 
   filename=`basename $I `
   ln -fs $I $START_PHYS/$filename
done

medmit_prex_or_die " . nco_indexer.sh $RUNDIR/set_cut_indexes_PHYS_vs_M128.sh "

# nota per PHYS
medmit_prex_or_die "./cutter.sh -i $START_PHYS -o $PHYSCUT_IC_DIR -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N ' "

medmit_prex_or_die "python IC_files_gen.py -m $MASK_128 --nativemask $MASK24_Red  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START "

fi
#########


if [ 1 == 0 ] ; then

## bio ##
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_OGSTM_vs_M128.sh "

medmit_prex_or_die "python Time_interpolator.py -i $WEEKLY_BIO_netCDF4  --datatype ave -o $TIMEINTERP___DIR -v $VAR_TO_INTERP_W -if $TIMES_WEEKLY -of $TIMELIST_START -m $MASK_OGSTM "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP_W  -t $TIMELIST_START -m $MASK_OGSTM "

medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $DAILY_BIO_netCDF4 --datatype ave -o $BIOCUT_IC_DIR -v $VAR_BIO_DAILY  -t $TIMELIST_START -m $MASK_OGSTM "

medmit_prex_or_die "python IC_files_gen.py -m $MASK_128 --nativemask $MASK24_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS "
fi

##################################################################



### Step 4. BOUNDARY CONDITIONS ##################################

## phys ##
if [ 1 == 1 ] ;  then
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_PHYS_vs_M128.sh "

# South Boundary 
medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR/SOUTH  -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_S ' " 
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 --nativemask $MASK24_Red -s S -i $PHYSCUT_BC_DIR/SOUTH  -o $PHYS_BC_DIR"

# West Boundary 
medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR/WEST  -c 'ncks -F -a -d x,$Index_W,$Index_W -d y,$Index_S,$Index_N ' " 
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 --nativemask $MASK24_Red -s W -i $PHYSCUT_BC_DIR/WEST  -o $PHYS_BC_DIR" 

# Other Boundaries 
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 -s E -o $PHYS_BC_DIR"

fi


if [ 1 == 0 ] ; then
## bio ##
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_OGSTM_vs_M128.sh "

# South Boundary 
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $WEEKLY_BIO_netCDF4 --datatype ave -o ${BIOCUT_BC_DIR__LOW_W}/SOUTH -v $VAR_TO_INTERP_W -t $TIMES_WEEKLY -m $MASK_OGSTM"
medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_W}/SOUTH -o ${BIOCUT_BC_DIR_HIGH}/SOUTH -s S -if $TIMES_WEEKLY -of $TIMES_DAILY -v $VAR_TO_INTERP_W -m $MASK24_Red "

medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $DAILY_BIO_netCDF4 --datatype ave -o ${BIOCUT_BC_DIR_HIGH}/SOUTH -v $VAR_BIO_DAILY -t $TIMES_DAILY -m $MASK_OGSTM"

medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 --nativemask $MASK24_Red -s S -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/SOUTH"

# West Boundary 
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_W --latcut $Index_S,$Index_N -i $WEEKLY_BIO_netCDF4 --datatype ave -o ${BIOCUT_BC_DIR__LOW_W}/WEST -v $VAR_TO_INTERP_W -t $TIMES_WEEKLY -m $MASK_OGSTM"
medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_W}/WEST -o ${BIOCUT_BC_DIR_HIGH}/WEST -s W -if $TIMES_WEEKLY -of $TIMES_DAILY -v $VAR_TO_INTERP_W -m $MASK24_Red "

medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_W --latcut $Index_S,$Index_N -i $DAILY_BIO_netCDF4 --datatype ave -o ${BIOCUT_BC_DIR_HIGH}/WEST -v $VAR_BIO_DAILY -t $TIMES_DAILY -m $MASK_OGSTM"

medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 --nativemask $MASK24_Red -s W -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/WEST" # Valeria added it

# Other Boundaries 
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s E -o $BIO_BC_DIR"

fi


##################################################################

### Step 5. Prepare data to fluxus 
#cd $RUNDIR
#medmit_prex_or_die " tar -czf $RUNDIR/BC.tar.gz  BC/PHYS/*dat BC/BIO/*dat "
#medmit_prex_or_die " tar -czf $RUNDIR/IC.tar.gz  IC/PHYS/*dat IC/BIO/*dat "

##################################################################

