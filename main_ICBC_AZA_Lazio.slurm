#! /bin/bash

#SBATCH -N1 -n20
#SBATCH --time=5:50:00
#SBATCH --job-name=jobFettine
#SBATCH --account OGS21_PRACE_P
#SBATCH --partition gll_usr_prod


#cd $SLURM_SUBMIT_DIR

# su galileo
module load autoload
module load intelmpi/oneapi-2021--binary
module load nco
LIBDIR=/g100_work/OGS21_PRACE_P/COPERNICUS/V8C/HOST/g100
export    HDF5_DIR=$LIBDIR
export NETCDF4_DIR=$LIBDIR
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$LIBDIR
source /g100_work/OGS21_PRACE_P/COPERNICUS/py_env_3.6.8/bin/activate
export PYTHONPATH=$PYTHONPATH:/g100_work/OGS21_PRACE_P/COPERNICUS/bit.sea


MPI="mpirun -np 20"

. ./profile.inc

DATESTART=20180101-12:00:00   
DATE__END=20181231-12:00:00 # fixme: era 20191231

RUNDIR=/gpfs/scratch/userexternal/vdibiagi/CADEAU/REA_IC_BC/BC_IC_preparation_AZA # FIXME
mkdir -p $RUNDIR
HERE=$PWD 

###  INPUT DATA  ###############################

DATA_DIR=/gpfs/scratch/userexternal/vdibiagi/CADEAU/REA_IC_BC/DATA #fixme c'era $ all'inizio

# PHYS, to be processed
#PHYS_DIR_Anna=/gpfs/scratch/userexternal/ateruzzi/MULTIVARIATE_24/TEST_04/wrkdir/MODEL/FORCINGS # 
PHYS_DIR=$DATA_DIR/PHYS_r # data copied here, then deleted 

# BIO, to be processed
#AVE_DIR_Anna=/gpfs/scratch/userexternal/ateruzzi/MULTIVARIATE_24/TEST_04/wrkdir/MODEL/ # questi i dati originali
AVE_DIR=$DATA_DIR/BIO_r # data copied here

######################################################

###  ELABORATION DIRS  ###############################

# PHYS input pre-processed: daily variables netCDF3
PHYS_DIR_netCDF3=$DATA_DIR/PHYS_netCDF3

# BIO input pre-processed: daily and weekly variables netCDF3
AVE_DAILY_netCDF3=$DATA_DIR/BIO_netCDF3/DAILY
AVE_WEEKLY_netCDF3=$DATA_DIR/BIO_netCDF3/WEEKLY # FIXMEEEEEEEEEEEEEEEEEEEE ho spostato file del 2016, 2017 e 2019 dopo 0104 dentro "other"

# intermediate directories for BIO pre-processing (then deleted)
DAILY_BIO_netCDF4=$AVE_DIR/netCDF4_DAILY
WEEKLY_BIO_netCDF4=$AVE_DIR/netCDF4_WEEKLY
# useful only for uncompressing
#AVE_DAILY=/gpfs/scratch/userexternal/vdibiagi/CADEAU/REA_IC_BC/DATA/BIO_r/UNZIPPED_DAILY
#AVE_WEEKLY=/gpfs/scratch/userexternal/vdibiagi/CADEAU/REA_IC_BC/DATA/BIO_r/UNZIPPED_WEEKLY

START_PHYS=/gpfs/scratch/userexternal/vdibiagi/CADEAU/REA_IC_BC/PHYS/UNZIPPED_IC 
PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/AZA_Lazio/                  # Original for phys IC cutted; FIXME era .../IC/CADEAU
BIOCUT_IC_DIR=$RUNDIR/BIO/IC/AZA_Lazio/                    # BIO IC cutted; FIXME come sopra
#
PHYSCUT_BC_DIR=$RUNDIR/PHYS/CUTTED_SLICES               # BC slices phys
BIOCUT_BC_DIR_HIGH=$RUNDIR/BIO/CUTTED_SLICES/DAILY      # BC slices BIO high freq -> output of temporal interpolations (for weekly and possibly monthly data)
BIOCUT_BC_DIR__LOW_W=$RUNDIR/BIO/CUTTED_SLICES/WEEKLY   # BC slices BIO low freq weekly
#BIOCUT_BC_DIR__LOW_M=$RUNDIR/BIO/CUTTED_SLICES/MONTHLY # BC slices BIO low freq monthly
  
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
#TIMES_MONTHLY=$RUNDIR/monthly.txt
TIMELIST_START=$RUNDIR/t0.txt
 
MASK__F=$RUNDIR/maskINGV_AF.nc # INGV mask for PHYS
MASK_24=$RUNDIR/mask24.nc      # BIO mask, 1/24
MASK24_Red=$RUNDIR/mask24R.nc  # reduced mask24 on the domain (here: Tyrrhenus)
MASK_128=$RUNDIR/mask128.nc    # here: Lazio mask
        
MODELVARS=static-data/ModelVarNamesV5
VAR_BIO_DAILY=static-data/ModelVarDailyV5
VAR_TO_INTERP_W=static-data/ModelVarWeeklyV5
# VAR_TO_INTERP_M=static-data/InterpVarNamesM_prova
    
export RIVERDATA=/gpfs/scratch/userexternal/vdibiagi/CADEAU/REA_IC_BC/fiumi_squerin/river_meteo_data/rivers_AZA_Lazio/discharges_AZA_Lazio_V5_tmp.xlsx 
export RIVERMETEODIR=/gpfs/scratch/userexternal/vdibiagi/CADEAU/REA_IC_BC/fiumi_squerin/river_meteo_data/rivers_AZA_Lazio/2018/for_readXLS
######################################################

 
if [ 1 == 1 ] ; then

### Step 0.  GET MASK INFO  ##################################### 

MASK__PHYS=/g100_scratch/userexternal/gbolzon0/meshmask_INGVfor_ogstm.nc
MASK_OGSTM=/g100_scratch/userexternal/gcoidess/REANALISI_INTERIM/wrkdir/MODEL/meshmask.nc

BATHY=$RUNDIR/BC_IC/bathy.bin
mit_prex_or_die "gzip -dc static-data/AZAL/bathy.gz > $BATHY"
mit_prex_or_die "$MPI_1 python static-data/masks/AZAL/maskgen.py -b $BATHY -o $MASKFILE"

medmit_prex_or_die " python get_cut_Locations.py -c $MASK__F -f $MASK_128 > $RUNDIR/set_cut_indexes_INGV_AF_vs_M128.sh "
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_24 -f $MASK_128 > $RUNDIR/set_cut_indexes_24_vs_M128.sh "

medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_INGV_AF_vs_M128.sh $RUNDIR/set_cut_indexes_24_vs_M128.sh"

# getting Mask24 reduced on Lazio 
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_24_vs_M128.sh"
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_24 -O $MASK24_Red"
##################################################################
fi


if [ 1 == 0 ] ; then

### Step 1. DATA FROM ARCHIVES ########################## 
# 
# PHYS: Parallel conversion from netCDF4 to netCDF3 
mkdir -p $PHYS_DIR_netCDF3
for var in T U V; do 
medmit_prex_or_die " mpirun -np 20 python ncConversion.py -i $PHYS_DIR -o $PHYS_DIR_netCDF3  -l ${var}2018*nc "
medmit_prex_or_die " mpirun -np 20 python ncConversion.py -i $PHYS_DIR -o $PHYS_DIR_netCDF3  -l ${var}2019*nc "   
done

# BIO: tar extraction and parallel conversion from netCDF4 to netCDF3  

#### DAILY
mkdir -p $DAILY_BIO_netCDF4 $AVE_DAILY_netCDF3
#mkdir -p $AVE_DAILY # general: if I need also to uncompress
# 1.1 Tar extracting
for var in `cat $VAR_BIO_DAILY `; do 
medmit_prex_or_die "tar -xf $AVE_DIR/AVE_FREQ_1_tar_2018/${var}.tar -C $DAILY_BIO_netCDF4 " 
medmit_prex_or_die "tar -xf $AVE_DIR/AVE_FREQ_1_tar_2019/${var}.tar -C $DAILY_BIO_netCDF4 "  
done
# (Parallel uncompressing)-> if I need it, I have to change the input dir of ncConversion (step 1.2)
#medmit_prex_or_die " mpirun -np 20 python uncompress.py -i $DAILY_BIO_netCDF4  -o $AVE_DAILY -l *2018*gz "
#medmit_prex_or_die " mpirun -np 20 python uncompress.py -i $DAILY_BIO_netCDF4  -o $AVE_DAILY -l *2019*gz "
# 1.2 Parallel netCDF3 conversion 
medmit_prex_or_die " mpirun -np 20 python ncConversion.py -i $DAILY_BIO_netCDF4 -o $AVE_DAILY_netCDF3  -l ave*.nc "

#### WEEKLY
mkdir -p $WEEKLY_BIO_netCDF4 $AVE_WEEKLY_netCDF3
#mkdir -p $AVE_WEEKLY # general: if I need also to uncompress
# 1.1 Tar extracting
for var in `cat $VAR_TO_INTERP_W `; do 
medmit_prex_or_die "tar -xf $AVE_DIR/AVE_FREQ_2_tar/${var}.tar -C $WEEKLY_BIO_netCDF4 " 
medmit_prex_or_die "tar -xf $AVE_DIR/AVE_FREQ_2_tar/2019/${var}.tar -C $WEEKLY_BIO_netCDF4 "  
done
# (Parallel uncompressing)-> if I need it, I have to change the input dir of ncConversion (step 1.2)
#medmit_prex_or_die " mpirun -np 20 python uncompress.py -i $WEEKLY_BIO_netCDF4  -o $AVE_WEEKLY -l *2018*gz "
#medmit_prex_or_die " mpirun -np 20 python uncompress.py -i $WEEKLY_BIO_netCDF4  -o $AVE_WEEKLY -l *2019*gz "
# 1.2 Parallel netCDF3 conversion 
medmit_prex_or_die " mpirun -np 20 python ncConversion.py -i $WEEKLY_BIO_netCDF4 -o $AVE_WEEKLY_netCDF3  -l ave*.nc "
fi


if [ 1==0 ] ; then
### Step 2. DATA FOR LINEAR TIME INTERPOLATION  #############

# We get TIMELIST_FROM from existing files

# WEEKLY
cat /dev/null > $TIMES_WEEKLY   
for I in `ls $AVE_WEEKLY_netCDF3/*B1p* `; do 
   filename=`basename $I`
   echo ${filename:4:17} >> $TIMES_WEEKLY
done

# general: if I have monthly data 
# MONTHLY
#cat /dev/null > $TIMES_MONTHLY
#for I in `ls $AVE_MONTHLY_DIR/*B1c* `; do
#   filename=`basename $I`
#   echo ${filename:4:17} >> $TIMES_MONTHLY
#done

fi #FIXME spostato qui per fare solo 2018, era 4 righe sotto
# TIMELIST_TO is generated
medmit_prex_or_die " python TimeList_generator.py -s $DATESTART -e $DATE__END -d 'days = 1' > $TIMES_DAILY "

#fi
##################################################################

### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START
DATESTART8=${DATESTART:0:8}  

if [ 1 == 0 ] ; then

## phys  ##

mkdir -p $START_PHYS

for I in `ls $PHYS_DIR_netCDF3/*${DATESTART8}* ` ; do 
   filename=`basename $I `
   ln -fs $I $START_PHYS/$filename
done

medmit_prex_or_die " . nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_AF_vs_M128.sh "

medmit_prex_or_die "./cutter.sh -i $START_PHYS -o $PHYSCUT_IC_DIR -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N ' "

medmit_prex_or_die "python IC_files_gen_24.py -m $MASK_128 --nativemask $MASK24_Red  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START "
fi
#########


if [ 1 == 0 ] ; then

## bio ##

medmit_prex_or_die " . $RUNDIR/set_cut_indexes_24_vs_M128.sh "

medmit_prex_or_die "python Time_interpolator.py -i $AVE_WEEKLY_netCDF3  --datatype ave -o $TIMEINTERP___DIR -v $VAR_TO_INTERP_W -if $TIMES_WEEKLY -of $TIMELIST_START -m $MASK_24 "
##medmit_prex_or_die "python Time_interpolator.py -i $AVE_MONTHLY_DIR  --datatype ave -o $TIMEINTERP___DIR -v $VAR_TO_INTERP_M -if $TIMES_MONTHLY -of $TIMELIST_START -m $MASK_24 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP_W  -t $TIMELIST_START -m $MASK_24 "
##medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP_M  -t $TIMELIST_START -m $MASK_24 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $AVE_DAILY_netCDF3 --datatype ave -o $BIOCUT_IC_DIR -v $VAR_BIO_DAILY  -t $TIMELIST_START -m $MASK_24 "

medmit_prex_or_die "python IC_files_gen_24.py -m $MASK_128 --nativemask $MASK24_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS "
fi

##################################################################



### Step 4. BOUNDARY CONDITIONS ##################################



## phys ##

if [ 1 == 0 ] ;  then
#medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_AF_vs_M128.sh "

# scommentare questi 2 sotto, sono già stati fatti fino al 2019 compreso
#medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR_netCDF3 -o $PHYSCUT_BC_DIR/SOUTH  -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_S ' " #cutter ci mette 31 minuti circa per 2 anni
#medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR_netCDF3 -o $PHYSCUT_BC_DIR/WEST  -c 'ncks -F -a -d x,$Index_W,$Index_W -d y,$Index_S,$Index_N ' " # Valeria added it

medmit_prex_or_die " python BC_files_gen_PHYS_24.py -t $TIMES_DAILY -m $MASK_128 -s E -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS_24.py -t $TIMES_DAILY -m $MASK_128 -s N -o $PHYS_BC_DIR"

#scommentare questo sotto
medmit_prex_or_die " python BC_files_gen_PHYS_24.py -t $TIMES_DAILY -m $MASK_128 --nativemask $MASK24_Red -s S -i $PHYSCUT_BC_DIR/SOUTH  -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS_24.py -t $TIMES_DAILY -m $MASK_128 --nativemask $MASK24_Red -s W -i $PHYSCUT_BC_DIR/WEST  -o $PHYS_BC_DIR" #Valeria added it, non funziona se non cambio i fiumi

fi


if [ 1 == 1 ] ; then
## bio ##
# scommentare questo sotto
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_24_vs_M128.sh "

# South Boundary #
# scommentare questo sotto - NOTA: ci mette 10 minuti per fare un anno
#medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_WEEKLY_netCDF3 --datatype ave -o ${BIOCUT_BC_DIR__LOW_W}/SOUTH -v $VAR_TO_INTERP_W -t $TIMES_WEEKLY -m $MASK_24"
######medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_MONTHLY_DIR --datatype ave -o ${BIOCUT_BC_DIR__LOW_M}/SOUTH -v $VAR_TO_INTERP_M -t $TIMES_MONTHLY -m $MASK_24"
#scommentare questo sotto - pochissimi minuti per un anno
#medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_W}/SOUTH -o ${BIOCUT_BC_DIR_HIGH}/SOUTH -s S -if $TIMES_WEEKLY -of $TIMES_DAILY -v $VAR_TO_INTERP_W -m $MASK24_Red "
######medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_M}/SOUTH -o ${BIOCUT_BC_DIR_HIGH}/SOUTH -s S -if $TIMES_MONTHLY -of $TIMES_DAILY -v $VAR_TO_INTERP_M -m $MASK24_Red "

#medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_DAILY_netCDF3 --datatype ave -o ${BIOCUT_BC_DIR_HIGH}/SOUTH -v $VAR_BIO_DAILY -t $TIMES_DAILY -m $MASK_24"
#medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 --nativemask $MASK24_Red -s S -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/SOUTH"


# West Boundary # Valeria added it
#medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_W --latcut $Index_S,$Index_N -i $AVE_WEEKLY_netCDF3 --datatype ave -o ${BIOCUT_BC_DIR__LOW_W}/WEST -v $VAR_TO_INTERP_W -t $TIMES_WEEKLY -m $MASK_24"
#medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR__LOW_W}/WEST -o ${BIOCUT_BC_DIR_HIGH}/WEST -s W -if $TIMES_WEEKLY -of $TIMES_DAILY -v $VAR_TO_INTERP_W -m $MASK24_Red "

#medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_W --latcut $Index_S,$Index_N -i $AVE_DAILY_netCDF3 --datatype ave -o ${BIOCUT_BC_DIR_HIGH}/WEST -v $VAR_BIO_DAILY -t $TIMES_DAILY -m $MASK_24"
#medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 --nativemask $MASK24_Red -s W -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/WEST" # Valeria added it
# restituisce errore per fiumi sbagliati

# Other Boundaries #
#medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s N -o $BIO_BC_DIR"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s E -o $BIO_BC_DIR"




fi


##################################################################

### Step 5. Prepare data to fluxus 
#cd $RUNDIR
#medmit_prex_or_die " tar -czf $RUNDIR/BC.tar.gz  BC/PHYS/*dat BC/BIO/*dat "
#medmit_prex_or_die " tar -czf $RUNDIR/IC.tar.gz  IC/PHYS/*dat IC/BIO/*dat "

##################################################################

