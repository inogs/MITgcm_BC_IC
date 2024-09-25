#! /bin/bash
#PBS -A IscrC_CADRI               
#PBS -l walltime=4:00:00
#PBS -l select=1:ncpus=36:mpiprocs=36:mem=118GB 
#PBS -m abe 
#PBS -M vdibiagio@inogs.it 
#PBS -o jobMinterp.out
#PBS -e jobMinterp.err
#PBS -N BCMintp   
#


cd $PBS_O_WORKDIR

module purge
module load profile/advanced
module load autoload 
module load intel/pe-xe-2017--binary 
module load netcdf/4.4.1--intel--pe-xe-2017--binary 
module load python/2.7.12 scipy/0.18.1--python--2.7.12
module load intelmpi/2017--binary
source /marconi_work/OGS_dev_0/COPERNICUS/py_env_2.7.12/bin/activate
PYTHONPATH=$PYTHONPATH:/marconi_work/OGS_dev_0/COPERNICUS/bit.sea
module load nco
module list

MPI="mpirun -np 36"
#MPI=" "

. ./profile.inc

DATESTART=20060101-12:00:00  # <--- IC
DATE__END=20161231-12:00:00 # all period 

RUNDIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/BC_IC_preparation_allPeriod
mkdir -p $RUNDIR
HERE=$PWD 

      AVE_WEEKLY_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/WEEKLY/UNZIPPED
         # BIO low 1 freq variables
      AVE_MONTHLY_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/MONTHLY/UNZIPPED
          # BIO low 2 freq variables
           PHYS_DIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/PHYS/UNZIPPED
             # PHYS : daily variables

######################################################

###  ELABORATION DIRS  ###############################
        START_PHYS=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/PHYS/UNZIPPED_ORIG   
 PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/CADEAU/                # Original for phys IC cutted
     BIOCUT_IC_DIR=$RUNDIR/BIO/IC/CADEAU/                # BIO IC cutted
    PHYSCUT_BC_DIR=$RUNDIR/PHYS/CUTTED_SLICES           # BC slices phys
BIOCUT_BC_DIR_HIGH=$RUNDIR/BIO/CUTTED_SLICES/DAILY       # BC slices BIO high freq -> output of temporal interpolations (for weekly and monthly data)
BIOCUT_BC_DIR__LOW_W=$RUNDIR/BIO/CUTTED_SLICES/WEEKLY      # BC slices BIO low freq weekly
BIOCUT_BC_DIR__LOW_M=$RUNDIR/BIO/CUTTED_SLICES/MONTHLY      # BC slices BIO low freq monthly
  
  TIMEINTERP___DIR=$RUNDIR/BIO/IC/INTERPOLATED
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

           MASK_16=$RUNDIR/mask16.nc   # BIO mask, 1/16
           MASK_128=$RUNDIR/mask128.nc # Cadeau mask
           MASK__F=$RUNDIR/maskINGV.nc # INGV mask for PHYS
        MASK16_Red=$RUNDIR/mask16R.nc        # reduced mask16 on north Adri
   VAR_TO_INTERP_W=static-data/InterpVarNamesW
   VAR_TO_INTERP_M=static-data/InterpVarNamesM
       MODELVARS=static-data/ModelVarNames 

export RIVERDATA=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/BC_IC_from_ogstm/static-data/masks/CADEAU/discharges_CADEAU_N2.xlsx
export RIVERMETEODIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/fiumi_squerin/river_meteo_data  
######################################################


if [ 1 == 1 ] ; then

### Step 0.  GET MASK INFO  ##################################### 

medmit_prex_or_die "gzip -cd static-data/masks/V4/mask.nc.gz    > $MASK_16 " 
medmit_prex_or_die "gzip -cd static-data/masks/CADEAU/mask.nc.gz > $MASK_128 "
medmit_prex_or_die "gzip -cd static-data/masks/INGV/mask.nc.gz  > $MASK__F "  

medmit_prex_or_die " python get_cut_Locations.py -c $MASK__F -f $MASK_128 > $RUNDIR/set_cut_indexes_INGV_vs_M128.sh "
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_16 -f $MASK_128 > $RUNDIR/set_cut_indexes_V4_vs_M128.sh "

medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_INGV_vs_M128.sh $RUNDIR/set_cut_indexes_V4_vs_M128.sh"

# getting Mask16 reduced on NADRI 
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_V4_vs_M128.sh"
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_16 -O $MASK16_Red"
##################################################################
fi


if [ 1 == 0 ] ; then
### Step 1. GETTING DATA FROM ARCHIVES ########################## not updated and not used
# 1.1 Tar extracting
mkdir -p $WEEKLY_ZIPPED $DAILY_ZIPPED $DAILY_PHYS_ZIPPED
for var in `cat $VAR_TO_INTERP `; do # 15 min
   medmit_prex_or_die " tar -xf /gss/gss_work/DRES_OGS_BiGe/ateruzzi/RA_CARBO_TRANSITION/output/AVE/WEEKLY/${var}.tar -C $WEEKLY_ZIPPED "
done
for var in `cat $VARLIST_HIGH `; do # 20 min
   medmit_prex_or_die "tar -xf /gss/gss_work/DRES_OGS_BiGe/ateruzzi/RA_CARBO_TRANSITION/output/AVE/DAILY/2013/${var}.tar -C $DAILY_ZIPPED "
done   
for var in T U V; do # 10 min
   medmit_prex_or_die "tar -xf /gss/gss_work/DRES_OGS_BiGe/ateruzzi/FORCING_REA_1985-2014/tar/${var}_2013.tar -C $DAILY_PHYS_ZIPPED "
done
# 1.2 Parallel uncompressing
mkdir -p $AVE_WEEKLY_DIR $AVE_DAILY_DIR $PHYS_DIR
medmit_prex_or_die " mpirun -np 12 python uncompress.py -i $WEEKLY_ZIPPED     -o $AVE_WEEKLY_DIR -l *2013*gz "
medmit_prex_or_die " mpirun -np 12 python uncompress.py -i $DAILY_ZIPPED      -o $AVE_DAILY_DIR  -l *2013*gz "
medmit_prex_or_die " mpirun -np 12 python uncompress.py -i $DAILY_PHYS_ZIPPED -o $PHYS_DIR       -l *2013*gz "   
##################################################################
fi

if [ 1==0 ] ; then
### Step 2. DATA FOR LINEAR TIME INTERPOLATION  #############

# We get TIMELIST_FROM  from existing files

# WEEKLY
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

fi
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

medmit_prex_or_die " . nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M128.sh "
medmit_prex_or_die "./cutter.sh -i $START_PHYS -o $PHYSCUT_IC_DIR -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N ' "
medmit_prex_or_die "python IC_files_gen.py -m $MASK_128 --nativemask $MASK16_Red  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START "


## bio ##

medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M128.sh "

medmit_prex_or_die "python Time_interpolator.py -i $AVE_WEEKLY_DIR  --datatype ave -o $TIMEINTERP___DIR -v $VAR_TO_INTERP_W -if $TIMES_WEEKLY -of $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python Time_interpolator.py -i $AVE_MONTHLY_DIR  --datatype ave -o $TIMEINTERP___DIR -v $VAR_TO_INTERP_M -if $TIMES_MONTHLY -of $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP_W  -t $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP_M  -t $TIMELIST_START -m $MASK_16 "

medmit_prex_or_die "python IC_files_gen.py -m $MASK_128 --nativemask $MASK16_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS "
fi

##################################################################





### Step 4. BOUNDARY CONDITIONS ##################################



## phys ##
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M128.sh "

if [ 1 == 0 ] ;  then
medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR/SOUTH  -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_S ' "
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 -s E -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 -s N -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 -s W -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 --nativemask $MASK16_Red -s S -i $PHYSCUT_BC_DIR/SOUTH  -o $PHYS_BC_DIR"
fi

## bio ##
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M128.sh "
# South Boundary

if [ 1 == 0 ] ; then
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_WEEKLY_DIR --datatype ave -o ${BIOCUT_BC_DIR__LOW_W}/SOUTH -v $VAR_TO_INTERP_W -t $TIMES_WEEKLY -m $MASK_16"
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_MONTHLY_DIR --datatype ave -o ${BIOCUT_BC_DIR__LOW_M}/SOUTH -v $VAR_TO_INTERP_M -t $TIMES_MONTHLY -m $MASK_16"
medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_W}/SOUTH -o ${BIOCUT_BC_DIR_HIGH}/SOUTH -s N -if $TIMES_WEEKLY -of $TIMES_DAILY -v $VAR_TO_INTERP_W -m $MASK16_Red "
medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_M}/SOUTH -o ${BIOCUT_BC_DIR_HIGH}/SOUTH -s N -if $TIMES_MONTHLY -of $TIMES_DAILY -v $VAR_TO_INTERP_M -m $MASK16_Red "

medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s N -o $BIO_BC_DIR"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s E -o $BIO_BC_DIR"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s W -o $BIO_BC_DIR"

medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 --nativemask $MASK16_Red -s S -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/SOUTH"
fi


##################################################################

### Step 5. Prepare data to fluxus 
#cd $RUNDIR
#medmit_prex_or_die " tar -czf $RUNDIR/bc.tar.gz  BC/PHYS/*dat BC/BIO/*dat "
#medmit_prex_or_die " tar -czf $RUNDIR/IC.tar.gz  IC/PHYS/*dat IC/BIO/*dat "




