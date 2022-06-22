#! /bin/bash

#SBATCH -N1 -n 36
#SBATCH --time=00:30:00
#SBATCH --job-name=jobFettine
#SBATCH --account=OGS18_PRACE_P
#SBATCH --partition=knl_usr_dbg
#


#cd $SLURM_SUBMIT_DIR

#module purge
#module load profile/base
#module load intel/pe-xe-2018--binary intelmpi/2018--binary
#module load autoload
#module load hdf5/1.8.18--intel--pe-xe-2018--binary netcdf/4.6.1--intel--pe-xe-2018--binary
#module load numpy/1.15.2--python--2.7.12 mpi4py/3.0.0--intelmpi--2018--binary
#source /gpfs/work/OGS20_PRACE_P/COPERNICUS/py_env_2.7.12/bin/activate
#export PYTHONPATH=$PYTHONPATH:/gpfs/work/OGS20_PRACE_P/COPERNICUS/bit.sea
#module load nco


MPI="mpirun -np 36 "



RUNDATE=20220617
  DATESTART=$( date -d "${RUNDATE}  -  7  days " +%Y%m%d )   # <--- IC
  DATE__END=$( date -d "${RUNDATE}  +  3  days " +%Y%m%d-%H:%M:%S )   # all period
OPA_RUNDATE_A=$( date -d "last tuesday" +%Y%m%d )
     DATE_W=$( date -d "${OPA_RUNDATE_A} - 5 days +  12  hours " +%Y%m%d-%H:%M:%S )

export DATESTART
. ./profile.inc


RUNDIR=/gpfs/scratch/userexternal/gbolzon0/MIT/OP_Cadeau/RUNDATES/${RUNDATE}
BITSEA=/gpfs/work/OGS20_PRACE_P/COPERNICUS/bit.sea
#mkdir -p $RUNDIR
HERE=$PWD

####### ARCHIVE DIRS #################################

OPA_ARCDIR_ROOT=/gpfs/work/OGS_prod_0/OPA/V6C/prod/archive
      ARCHIVE_AVE_W=$OPA_ARCDIR_ROOT/analysis/$OPA_RUNDATE_A/POSTPROC/AVE_FREQ_2

###################################################### 

#######  DOWNLOADED FILES DIRS  ######################
AVE_DAILY_ZIPPED_DIR=$RUNDIR/BIO/ZIPPED/AVE/DAILY       # BIO high freq variables
       AVE_DAILY_DIR=$RUNDIR/BIO/UNZIPPED/AVE/DAILY
      AVE_WEEKLY_DIR=$RUNDIR/BIO/UNZIPPED/AVE/WEEKLY
           PHYS_DIR=$RUNDIR/PHYS/UNZIPPED                # PHYS

######################################################

    
######################################################

###  ELABORATION DIRS  ###############################
       START_PHYS=$RUNDIR/PHYS/IC/
   PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/CADEAU                 # Original for phys IC cutted
     BIOCUT_IC_DIR=$RUNDIR/BIO/IC/CADEAU               # BIO IC cutted
    PHYSCUT_BC_DIR=$RUNDIR/PHYS/CUTTED_SLICES           # BC slices phys
BIOCUT_BC_DIR_HIGH=$RUNDIR/BIO/CUTTED_SLICES/DAILY       # BC slices BIO high freq -> output of temporal interpolations (for weekly and monthly data)
BIOCUT_BC_DIR_DAILY=$RUNDIR/BIO/CUTTED_SLICES/DAILY     # BC slices BIO high freq daily
BIOCUT_BC_DIR_WEEKLY=$RUNDIR/BIO/CUTTED_SLICES/WEEKLY    # BC slices BIO low freq weekly
  
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
    TIMELIST_START=$RUNDIR/t0.txt
           BATHYGZ=bathy.gz
           BATHY=$RUNDIR/bathy.nc
           MASK_16=/marconi/home/usera07ogs/a07ogs00/OPA/V4C/wrkdir/2/MODEL/meshmask.nc   # BIO mask, 1/16
           MASK_128=$RUNDIR/mask128.nc          # Cadeau mask
           MASK__F=/marconi_scratch/userexternal/gbolzon0/OP_Cadeau/meshmask_sizeINGV.nc # INGV mask for PHYS
        MASK16_Red=$RUNDIR/mask16R.nc           # reduced mask16 on north Adri
     LOW_FREQ_VARS=static-data/InterpVarNames
    HIGH_FREQ_VARS=$RUNDIR/high_freq.txt
       MODELVARS=static-data/ModelVarNames 

export RIVERDATA=static-data/masks/CADEAU/discharges_CADEAU_N2.xlsx
export RIVERMETEODIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/fiumi_squerin/river_meteo_data
export RIVERMETEODIR=$RUNDIR #fake
######################################################

INPUTDIR=/g100_work/OGS_prodC/MIT/V1M-prod/wrkdir/MODEL/input/binaries/
INPUTDIR=/g100_work/OGS_prodC/MIT/V1M-dev/V1/devel/wrkdir/MODEL/input/binaries/
MASKFILE=/g100_work/OGS_prodC/MIT/V1M-prod/wrkdir/BC_IC/mask.nc
OUTDIR=input_binaries
mkdir -p ${OUTDIR}

medmit_prex "python get_daily_flux_file.py -i $INPUTDIR -o $OUTDIR -m $MASKFILE -t /g100_work/OGS_prodC/MIT/V1M-prod/wrkdir/daily.txt"


exit 0

DATE_RIVERSTART=$( date -d "${RUNDATE}  -  10  days " +%Y-%m-%d )
DATE_RIVER__END=$( date -d "${RUNDATE}  " +%Y-%m-%d )
URL="https://larissa.ogs.it/erddap/tabledap/Pontelagoscuro_TS.csv?time%2Criver_discharge&time%3E=${DATE_RIVERSTART}T00%3A00%3A00Z&time%3C=${DATE_RIVER__END}T00%3A00%3A00Z"

medmit_prex "curl \"$URL\" > tmp.txt "
medmit_prex "python riverdata_converter.py -i tmp.txt > Po.txt"





exit 0


if [ 1 == 1 ] ; then
### Step 1. GETTING DATA FROM ARCHIVES ##########################



mkdir -p $AVE_DAILY_ZIPPED_DIR $AVE_DAILY_DIR $AVE_WEEKLY_DIR $PHYS_DIR 




cd $AVE_DAILY_ZIPPED_DIR

for D in `mit_days `; do
  ARCHIVE_DIR=`python $BITSEA/validation/online/V6C_archive_info.py -d $D --dir`
  medmit_prex_or_die "medmit_linker $OPA_ARCDIR_ROOT/$ARCHIVE_DIR/POSTPROC/AVE_FREQ_1/ARCHIVE/ave.${D}-12:00:00.*.nc.gz "  
done
cd $HERE



# 1.2 Parallel uncompressing
for var in N O[23][ohc] P[1-4][lc] Z R6c B1c; do  
   medmit_prex_or_die " $MPI python uncompress.py -i $AVE_DAILY_ZIPPED_DIR    -o $AVE_DAILY_DIR  -l ave*${var}*.nc.gz "
done

medmit_prex_or_die " python high_var_list.py > $HIGH_FREQ_VARS "


medmit_prex_or_die " $MPI python uncompress.py -i $ARCHIVE_AVE_W  -o $AVE_WEEKLY_DIR -l *gz "


for var in `cat $LOW_FREQ_VARS `; do
   medmit_prex_or_die "weekly_linker $AVE_WEEKLY_DIR/ave.${DATE_W}.${var}.nc $AVE_DAILY_DIR "
done


####### link phys  ###########################
for D in `mit_days `; do
  ARCHIVE_PHYS_PREFIX=`python $BITSEA/validation/online/V6C_archive_info.py -d $D --phys `
  for var in U V T ; do
    phys_file=$OPA_ARCDIR_ROOT/${ARCHIVE_PHYS_PREFIX}${var}.nc
    filename=${D}_${var}.nc  # 20200510_U.nc
    medmit_prex_or_die "ln -fs $phys_file $PHYS_DIR/$filename"
  done
done
##################################################################
fi





if [ 1 == 1 ] ; then

### Step 0.  GET MASK INFO  ##################################### 

medmit_prex_or_die "gzip -cd static-data/masks/CADEAU/${BATHYGZ} > $BATHY   "
medmit_prex_or_die "python static-data/masks/CADEAU/maskgen.py -b $BATHY -o $MASK_128  "

medmit_prex_or_die " python get_cut_Locations.py -c $MASK__F -f $MASK_128 > $RUNDIR/set_cut_indexes_INGV_vs_M128.sh "
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_16 -f $MASK_128 > $RUNDIR/set_cut_indexes_V4_vs_M128.sh "

medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_INGV_vs_M128.sh $RUNDIR/set_cut_indexes_V4_vs_M128.sh"

# getting Mask16 reduced on CADEAU 
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_V4_vs_M128.sh"
medmit_prex_or_die " ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N $MASK_16 -O $MASK16_Red"
##################################################################
fi





if [ 1 == 1 ] ; then


### Step 2. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START
DATESTART8=${DATESTART:0:8}

mkdir -p $START_PHYS

if [ 1 == 1 ] ; then
## phys  ##

for I in `ls $PHYS_DIR/*${DATESTART8}* ` ; do 
   filename=`basename $I `
   medmit_prex_or_die " ln -fs $I $START_PHYS/$filename "
done

medmit_prex_or_die " . nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M128.sh "
medmit_prex_or_die "./cutter.sh -i $START_PHYS -o $PHYSCUT_IC_DIR -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N ' "
medmit_prex_or_die "mpirun -np 4 python IC_files_gen.py -m $MASK_128 --nativemask $MASK16_Red  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START "


## bio ##

medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M128.sh "
### here ogstm_cutter.py is not parallel because it works in parallel in timelist
medmit_prex_or_die "mpirun -np 1  python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $AVE_DAILY_DIR  --datatype ave -o $BIOCUT_IC_DIR -v $HIGH_FREQ_VARS -t $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "mpirun -np 10 python IC_files_gen.py -m $MASK_128 --nativemask $MASK16_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS "
fi

##################################################################





### Step 4. BOUNDARY CONDITIONS ##################################



## phys ##
if [ 1 == 1 ] ;  then
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M128.sh "
medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR/SOUTH  -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_S ' "

medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 -s E -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 -s N -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 -s W -o $PHYS_BC_DIR"
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASK_128 --nativemask $MASK16_Red -s S -i $PHYSCUT_BC_DIR/SOUTH  -o $PHYS_BC_DIR"
fi

## bio ##

medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M128.sh "
# South Boundary

if [ 1 == 1 ] ; then
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_DAILY_DIR --datatype ave -o ${BIOCUT_BC_DIR_DAILY}/SOUTH -v $HIGH_FREQ_VARS -t $TIMES_DAILY -m $MASK_16"
#medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_WEEKLY_DIR --datatype ave -o ${BIOCUT_BC_DIR_WEEKLY}/SOUTH -v $LOW_FREQ_VARS -t $TIMES_WEEKLY -m $MASK_16"
#medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i ${BIOCUT_BC_DIR_WEEKLY}/SOUTH -o ${BIOCUT_BC_DIR_DAILY}/SOUTH -s S -if $TIMES_WEEKLY -of $TIMES_DAILY -v $LOW_FREQ_VARS -m $MASK16_Red "


medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s N -o $BIO_BC_DIR"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s E -o $BIO_BC_DIR"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 -s W -o $BIO_BC_DIR"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMES_DAILY -v $MODELVARS -m $MASK_128 --nativemask $MASK16_Red -s S -o $BIO_BC_DIR  -i ${BIOCUT_BC_DIR_HIGH}/SOUTH"
fi 



##################################################################

### Step 5. Prepare data to fluxus 
cd $RUNDIR
medmit_prex_or_die " tar -czf bc.tar.gz  BC/PHYS/*dat BC/BIO/*dat "
medmit_prex_or_die " tar -czf IC.tar.gz  IC/PHYS/*dat IC/BIO/*dat "




