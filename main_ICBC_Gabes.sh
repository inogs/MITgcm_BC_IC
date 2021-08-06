#! /bin/bash

#SBATCH -n2
#SBATCH --time=00:30:00
#SBATCH --job-name=jobFettine
#SBATCH --error fett.err
#SBATCH --output fett.out
#SBATCH --account IscrC_CADRI_0
#SBATCH --partition knl_usr_prod

# loading of marconi modules
module purge
module load profile/advanced
module load autoload
module load intel/pe-xe-2017--binary
module load netcdf/4.4.1--intel--pe-xe-2017--binary
module load python/2.7.12 scipy/0.18.1--python--2.7.12
module load intelmpi/2017--binary
module load nco

#PYPATH=/marconi_work/OGS_dev_0/COPERNICUS/bit.sea
#export PYTHONPATH=$PYTHONPATH:$PYPATH
source /marconi_work/OGS_dev_0/COPERNICUS/py_env_2.7.12/bin/activate
PYTHONPATH=$PYTHONPATH:/marconi_work/OGS_dev_0/COPERNICUS/bit.sea
module list

MPI="mpirun -np 2"

. ./profile.inc

DATESTART=20060101-12:00:00 # <--- IC
DATE__END=20060131-12:00:00

RUNDIR=/marconi_scratch/userexternal/bbejaoui/REA_IC_BC/BC_IC_preparation
mkdir -p $RUNDIR

#######  DOWNLOADED FILES DIRS  ######################
# BIO low freq varibles, listed in $VAR_TO_INTERP
  AVE_WEEKLY_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/WEEKLY/UNZIPPED/2006
# AVE_WEEKLY_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/WEEKLY/UNZIPPED/ALL
# BIO high freq variables
  AVE_MONTHLY_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/MONTHLY/UNZIPPED/2006
# AVE_MONTHLY_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/MONTHLY/UNZIPPED/ALL
# PHYS
  PHYS_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/PHYS/UNZIPPED/2006 
# PHYS_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/PHYS/UNZIPPED
######################################################

###  ELABORATION DIRS  ###############################
  START_PHYS=$RUNDIR/PHYS/PHYS_IC/
  PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/GABES/                                        # Original for phys IC cutted
  BIOCUT_IC_DIR=$RUNDIR/BIO/IC/GABES/                                          # BIO IC cutted
  PHYSCUT_BC_DIR=$RUNDIR/PHYS/CUTTED_SLICES/                                   # BC slices phys
  BIOCUT_BC_DIR_HIGH=$RUNDIR/BIO/CUTTED_SLICES/DAILY                           # BC slices BIO high freq
  BIOCUT_BC_DIR__LOW_W=$RUNDIR/BIO/CUTTED_SLICES/WEEKLY                        # BC slices BIO low freq weekly 
  BIOCUT_BC_DIR__LOW_M=$RUNDIR/BIO/CUTTED_SLICES/MONTHLY                       # BC slices BIO low freq montqhly

  TIMEINTERP___DIR=$RUNDIR/BIO/IC/INTERPOLATED/
    
######################################################

##### OUTPUTS,  ready for MITgcm  ####################
  BIO_BC_DIR=$RUNDIR/BC/BIO
  PHYS_BC_DIR=$RUNDIR/BC/PHYS/
  BIO_IC_DIR=$RUNDIR/IC/BIO
  PHYSIC_DIR=$RUNDIR/IC/PHYS/
######################################################

######  FILES ########################################
  TIMES_WEEKLY=$RUNDIR/weekly.txt
  TIMES_DAILY=$RUNDIR/daily.txt
  TIMES_MONTHLY=$RUNDIR/monthly.txt

  TIMELIST_START=$RUNDIR/t0.txt

  BATHYGZ=bathyG3D.gz
    BATHY=$RUNDIR/bathy.nc
  MASK_16=$RUNDIR/mask16.nc
  MASK_64=$RUNDIR/mask64.nc
  MASK__F=$RUNDIR/maskINGV.nc                                                    #bbbb mask16R can be plotted by ncview bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
  MASK16_Red=$RUNDIR/mask16R.nc
#  VAR_TO_INTERP=static-data/InterpVarNames
  MODELVARS=static-data/ModelVarNames
#  VARLIST_HIGH=$RUNDIR/varlist_high
  VAR_TO_INTERP_W=static-data/InterpVarNamesW
  VAR_TO_INTERP_M=static-data/InterpVarNamesM
  

export RIVERDATA=static-data/masks/GABES/discharges_GABES.xlsx                    #question about river excel file bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
export RIVERMETEODIR=$RUNDIR
######################################################


if [ 1 == 1 ] ; then

### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/V4/mask.nc.gz    > $MASK_16 "
medmit_prex_or_die "gzip -cd static-data/masks/GABES/${BATHYGZ} > $BATHY   "
medmit_prex_or_die "python static-data/masks/GABES/maskgen.py -b $BATHY -o $MASK_64  "
medmit_prex_or_die "gzip -cd static-data/masks/INGV/mask.nc.gz  > $MASK__F "

medmit_prex_or_die " python get_cut_Locations.py -c $MASK__F -f $MASK_64 > $RUNDIR/set_cut_indexes_INGV_vs_M64.sh "
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_16 -f $MASK_64 > $RUNDIR/set_cut_indexes_V4_vs_M64.sh "

medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_INGV_vs_M64.sh $RUNDIR/set_cut_indexes_V4_vs_M64.sh"

# getting Mask16 reduced on Gabes
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_V4_vs_M64.sh"
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_16 -O $MASK16_Red"
##################################################################
fi


### Step 2. DATA FOR LINEAR TIME INTERPOLATION  ##################

# We get TIMELIST_FROM  from existing files
cat /dev/null > $TIMES_WEEKLY
for I in `ls $AVE_WEEKLY_DIR/*N3n* `; do
   filename=`basename $I`
   echo ${filename:4:17} >> $TIMES_WEEKLY
done

# MONTHLY
cat /dev/null > $TIMES_MONTHLY
for I in `ls $AVE_MONTHLY_DIR/*B1c* `; do
   filename=`basename $I`
   echo ${filename:4:17} >> $TIMES_MONTHLY
done


# TIMELIST_TO is generated
medmit_prex_or_die " python TimeList_generator.py -s $DATESTART -e $DATE__END -d 'days = 1' > $TIMES_DAILY "

##################################################################


### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START
DATESTART8=${DATESTART:0:8}

if [ 1 == 0 ] ; then
## phys  ##
mkdir -p $START_PHYS

for I in `ls $PHYS_DIR/*${DATESTART8}* ` ; do 
   filename=`basename $I `
   ln -fs $I $START_PHYS/$filename
done

medmit_prex_or_die " . nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M64.sh "
medmit_prex_or_die "./cutter.sh -i $START_PHYS -o $PHYSCUT_IC_DIR -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N ' "
medmit_prex_or_die "python IC_files_gen.py -m $MASK_64 --nativemask $MASK16_Red  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START "


## bio ##

medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M64.sh "

medmit_prex_or_die "python Time_interpolator.py -i $AVE_WEEKLY_DIR  --datatype ave -o $TIMEINTERP___DIR -v $VAR_TO_INTERP_W -if $TIMES_WEEKLY -of $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python Time_interpolator.py -i $AVE_MONTHLY_DIR  --datatype ave -o $TIMEINTERP___DIR -v $VAR_TO_INTERP_M -if $TIMES_MONTHLY -of $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP_W  -t $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP_M  -t $TIMELIST_START -m $MASK_16 "

medmit_prex_or_die "python IC_files_gen.py -m $MASK_64 --nativemask $MASK16_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS "
fi

##################################################################


### Step 4. BOUNDARY CONDITIONS ##################################

## phys ##
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M64.sh "   #bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
if [ 1 == 0 ] ;  then

medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR/NORTH -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_N,$Index_N ' "
medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR/EAST  -c 'ncks -F -a -d x,$Index_E,$Index_E -d y,$Index_S,$Index_N ' "

medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_64 --nativemask $MASK16_Red -s N -i $PHYSCUT_BC_DIR/NORTH -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_64 --nativemask $MASK16_Red -s E -i $PHYSCUT_BC_DIR/EAST  -o $PHYS_BC_DIR"

medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_64 -s W -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_64 -s S -o $PHYS_BC_DIR"

fi

## bio ##
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M64.sh "      #bbbbbbbbbbbbbbb pourqoui pour bio set_cut_indexes_V4_vs_M64.sh !!!!! pas comme phys ???? plus haut   set_cut_indexes_INGV_vs_M64.sh !!!!
# North Boundary

if [ 1 == 1 ] ; then
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_N,$Index_N -i $AVE_WEEKLY_DIR --datatype ave -o ${BIOCUT_BC_DIR__LOW_W}/NORTH -v $VAR_TO_INTERP_W -t $TIMES_WEEKLY -m $MASK_16"
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_N,$Index_N -i $AVE_MONTHLY_DIR --datatype ave -o ${BIOCUT_BC_DIR__LOW_M}/NORTH -v $VAR_TO_INTERP_M -t $TIMES_MONTHLY -m $MASK_16"

# East Boundary
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_E,$Index_E --latcut $Index_S,$Index_N -i $AVE_WEEKLY_DIR --datatype ave -o ${BIOCUT_BC_DIR__LOW_W}/EAST -v $VAR_TO_INTERP_W -t $TIMES_WEEKLY -m $MASK_16"
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_E,$Index_E --latcut $Index_S,$Index_N -i $AVE_MONTHLY_DIR --datatype ave -o ${BIOCUT_BC_DIR__LOW_M}/EAST -v $VAR_TO_INTERP_M -t $TIMES_MONTHLY -m $MASK_16"

medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_W}/NORTH -o ${BIOCUT_BC_DIR_HIGH}/NORTH -s N -if $TIMES_WEEKLY  -of $TIMES_DAILY -v $VAR_TO_INTERP_W -m $MASK16_Red "
medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_W}/EAST  -o ${BIOCUT_BC_DIR_HIGH}/EAST  -s E -if $TIMES_WEEKLY  -of $TIMES_DAILY -v $VAR_TO_INTERP_W -m $MASK16_Red "
medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_M}/NORTH -o ${BIOCUT_BC_DIR_HIGH}/NORTH -s N -if $TIMES_MONTHLY -of $TIMES_DAILY -v $VAR_TO_INTERP_M -m $MASK16_Red "
medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_M}/EAST  -o ${BIOCUT_BC_DIR_HIGH}/EAST  -s E -if $TIMES_MONTHLY -of $TIMES_DAILY -v $VAR_TO_INTERP_M -m $MASK16_Red "

medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_64 --nativemask $MASK16_Red -s N -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/NORTH"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_64 --nativemask $MASK16_Red -s E -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/EAST"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_64 -s W -o $BIO_BC_DIR "
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_64 -s S -o $BIO_BC_DIR "
fi

##################################################################

### Step 5. Prepare data to fluxus ###

if [ 1 == 1 ] ; then
cd $RUNDIR
medmit_prex_or_die " tar -czf $RUNDIR/bc.tar.gz  BC/PHYS/*dat BC/BIO/*dat "
medmit_prex_or_die " tar -czf $RUNDIR/IC.tar.gz  IC/PHYS/*dat IC/BIO/*dat "
fi

