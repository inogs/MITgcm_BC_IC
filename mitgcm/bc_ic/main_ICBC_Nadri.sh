#! /bin/bash

# Remote (pico) part:
# Step 0 : get Mask info
# Step 1 : get Data from Archives
# Step 2 : Interpolate BIO low freq variables to high freq (for not stored variables)
# Step 3 : IC
# Step 4 : BC
# Step 5 : Prepare tarfiles for fluxus.ogs.trieste.it


module purge
module load intel/cs-xe-2015--binary intelmpi/5.0.1--binary mkl/11.2.0--binary
module load profile/advanced gnu/4.8.3 python/2.7.8 ;
PYPATH=/pico/home/usera07ogs/a07ogs00/OPA/V4-dev/HOST/pico/lib/python2.7/site-packages/
export PYTHONPATH=$PYPATH:$PYTHONPATH
MPI=

. ./profile.inc

DATESTART=20141001-12:00:00
DATE__END=20141201-12:00:00

RUNDIR=/pico/scratch/userexternal/gbolzon0/For_MITgcm_TEST
mkdir -p $RUNDIR

####### RIVER DATA FROM METEO   ###################################
medmit_prex "cp $HOME/DISCHARGES/Timavo_oct_nov_2013.txt $RUNDIR/Timavo.txt"  # Daily
medmit_prex "cp $HOME/DISCHARGES/Isonzo_oct_nov_2014.txt $RUNDIR/Isonzo.txt"  #Hourly data, on North SIDE

###################################################################

#######  DOWNLOADED FILES DIRS  ######################
      RESTARTS_DIR=$RUNDIR/BIO/UNZIPPED/RST             # BIO low freq varibles, listed in $VAR_TO_INTERP
           AVE_DIR=$RUNDIR/BIO/UNZIPPED/AVE             # BIO high freq variables
          PHYS_DIR=$RUNDIR/PHYS/UNZIPPED/               # PHYS 
######################################################

###  ELABORATION DIRS  ###############################
        START_PHYS=$RUNDIR/PHYS/V4                      # Original for phys IC
    PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/ADRI/                # Original for phys IC cutted
    PHYSCUT_BC_DIR=$RUNDIR/PHYS/CUTTED_SLICES/ADRI/     # BC slices phys
     BIOCUT_IC_DIR=$RUNDIR/BIO/IC/ADRI/                 # BIO IC cutted
BIOCUT_BC_DIR_HIGH=$RUNDIR/BIO/CUTTED_SLICES/ADRI/DAILY # BC slices BIO high freq
BIOCUT_BC_DIR__LOW=$RUNDIR/BIO/CUTTED_SLICES/ADRI/WEEKLY #BC slices BIO low freq
  TIMEINTERPcutDIR=$RUNDIR/BIO/CUTTED_SLICES/ADRI/INTERPOLATED/
  TIMEINTERP___DIR=$RUNDIR/BIO/IC/INTERPOLATED/
    
######################################################

##### OUTPUTS,  ready for MITgcm  ####################
        BIO_BC_DIR=$RUNDIR/BC/BIO
       PHYS_BC_DIR=$RUNDIR/BC/PHYS/
        BIO_IC_DIR=$RUNDIR/IC/BIO
        PHYSIC_DIR=$RUNDIR/IC/PHYS/
######################################################


######  FILES ########################################
TIMELIST_FROM_FILE=$RUNDIR/tl1.txt
TIMELIST_TO___FILE=$RUNDIR/tl2.txt
TIMELIST_HR___FILE=$RUNDIR/tl_hr.txt
    TIMELIST_START=$RUNDIR/t0.txt

           MASK_16=$RUNDIR/mask16.nc
           MASK_64=$RUNDIR/mask64.nc
           MASK__F=$RUNDIR/maskINGV.nc
        MASK16_Red=$RUNDIR/mask16R.nc
   VAR_TO_INTERP=static-data/InterpVarNames
       MODELVARS=static-data/ModelVarNames
     VARLIST_HIGH=$RUNDIR/varlist_high
export RIVERDATA=static-data/masks/NADRI/discharges_NADRI.xlsx
export RIVERMETEODIR=$RUNDIR
######################################################




### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/V4/mask.nc.gz    > $MASK_16 "
medmit_prex_or_die "gzip -cd static-data/masks/NADRI/mask.nc.gz > $MASK_64 "
medmit_prex_or_die "gzip -cd static-data/masks/INGV/mask.nc.gz  > $MASK__F "

medmit_prex_or_die " python get_cut_Locations.py -c $MASK__F -f $MASK_64 > $RUNDIR/set_cut_indexes_INGV_vs_M64.sh "
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_16 -f $MASK_64 > $RUNDIR/set_cut_indexes_V4_vs_M64.sh "

medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_INGV_vs_M64.sh $RUNDIR/set_cut_indexes_V4_vs_M64.sh"

# getting Mask16 reduced on North Adriatic
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_V4_vs_M64.sh"
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_16 -O $MASK16_Red"
##################################################################



### Step 1. GETTING DATA FROM ARCHIVES ##########################

medmit_prex_or_die "INFO=($( ./get_V4_Archive_Date_Info.sh -s $DATESTART -e $DATE__END ) ) "
DATESTART_A=${INFO[0]}
      WEEKS=${INFO[1]}

medmit_prex_or_die " ./getForcingsFromArchive.sh -d $DATESTART_A -w $WEEKS -O $PHYS_DIR     -h remotehost "
medmit_prex_or_die " ./getDailyBIOFromArchive.sh -d $DATESTART_A -w $WEEKS -O $AVE_DIR      -h remotehost "
medmit_prex_or_die " ./getRST__BIOFromArchive.sh -d $DATESTART_A -w $WEEKS -O $RESTARTS_DIR -h remotehost "

##################################################################






### Step 2. DATA FOR LINEAR TIME INTERPOLATION  ###########################

# We get TIMELIST_FROM  from existing files
cat /dev/null > $TIMELIST_FROM_FILE
for I in `ls $RESTARTS_DIR/*N1p* `; do
   filename=`basename $I`
   echo ${filename:4:17} >> $TIMELIST_FROM_FILE
done

# TIMELIST_TO is generated
medmit_prex_or_die " python TimeList_generator.py -s $DATESTART -e $DATE__END -d 'days = 1' > $TIMELIST_TO___FILE "

# python Varlist_generator.py > $VAR_TO_INTERP # done once and for all
##################################################################








### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START
DATESTART8=${DATESTART:0:8}

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
medmit_prex_or_die " python high_var_list.py > $VARLIST_HIGH "
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M64.sh "

medmit_prex_or_die "python Time_interpolator.py -i $RESTARTS_DIR  --datatype RST -o $TIMEINTERP___DIR -v $VAR_TO_INTERP -if $TIMELIST_FROM_FILE -of $TIMELIST_START -m $MASK_16 "

medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $AVE_DIR          --datatype AVE -o $BIOCUT_IC_DIR -v $VARLIST_HIGH   -t $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP  -t $TIMELIST_START -m $MASK_16 "

medmit_prex_or_die "python IC_files_gen.py -m $MASK_64 --nativemask $MASK16_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS "

##################################################################





### Step 4. BOUNDARY CONDITIONS ##################################
# Times of North Side 2
medmit_prex_or_die "python TimeList_generator.py -s $DATESTART -e $DATE__END -d 'hours = 1' > $TIMELIST_HR___FILE "


## phys ##
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M64.sh "
medmit_prex_or_die " ./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_S ' "

medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_64 -s S -o $PHYS_BC_DIR --nativemask $MASK16_Red  -i $PHYSCUT_BC_DIR "
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_64 -s E -o $PHYS_BC_DIR "
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_64 -s W -o $PHYS_BC_DIR "
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMELIST_HR___FILE -v $MODELVARS -m $MASK_64 -s N -o $PHYS_BC_DIR "

## bio ##
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M64.sh "

medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $RESTARTS_DIR --datatype RST -o $BIOCUT_BC_DIR__LOW -v $VAR_TO_INTERP -t $TIMELIST_FROM_FILE -m $MASK_16"
medmit_prex_or_die "$MPI python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $AVE_DIR      --datatype AVE -o $BIOCUT_BC_DIR_HIGH -v $VARLIST_HIGH  -t $TIMELIST_TO___FILE -m $MASK_16"


medmit_prex_or_die "$MPI python BC_Time_interpolator.py -i $BIOCUT_BC_DIR__LOW -o $TIMEINTERPcutDIR -if $TIMELIST_FROM_FILE -of $TIMELIST_TO___FILE -v $VAR_TO_INTERP -s S -m $MASK16_Red "
medmit_prex_or_die " cp $BIOCUT_BC_DIR_HIGH/ave*nc $TIMEINTERPcutDIR " # they are already at the needed frequency


medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_64 -s S -o $BIO_BC_DIR --nativemask $MASK16_Red  -i $TIMEINTERPcutDIR"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_64 -s E -o $BIO_BC_DIR "
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_64 -s W -o $BIO_BC_DIR "
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMELIST_HR___FILE -v $MODELVARS -m $MASK_64 -s N -o $BIO_BC_DIR "

##################################################################



### Step 5. Prepare data to fluxus ###

medmit_prex_or_die " rm -rf $RUNDIR/CHECK ; mkdir  $RUNDIR/CHECK "

medmit_prex_or_die " mv ${PHYSIC_DIR}CHECK  $RUNDIR/CHECK/IC "
medmit_prex_or_die " mv ${BIO_IC_DIR}/CHECK  $RUNDIR/CHECK/IC/BIO "

medmit_prex_or_die " mv ${PHYS_BC_DIR}CHECK  $RUNDIR/CHECK/BC "
medmit_prex_or_die " mv ${BIO_BC_DIR}/CHECK  $RUNDIR/CHECK/BC/BIO "

cd $RUNDIR
medmit_prex_or_die " tar -czf $RUNDIR/bc.tar.gz  BC "
medmit_prex_or_die " tar -czf $RUNDIR/ic.tar.gz  IC "


