
#! /bin/bash
# FROM NADRI to GOT after NADRI run




module purge
module load intel/cs-xe-2015--binary intelmpi/5.0.1--binary mkl/11.2.0--binary
module load autoload matplotlib/1.4.3--python--2.7.9 scipy/0.15.1--python--2.7.9
MPI=

. ./profile.inc

DATESTART=20141001-12:00:00
DATE__END=20141201-12:00:00

RUNDIR=/pico/scratch/userexternal/gbolzon0/GoT/wrkdir
NADRIDIR=/pico/scratch/userexternal/gbolzon0/For_MITgcm_TEST

#######  DOWNLOADED FILES DIRS  ######################
      RESTARTS_DIR=$RUNDIR/BIO/UNZIPPED/RST             # BIO low freq varibles, listed in $VAR_TO_INTERP
           AVE_DIR=$NADRIDIR/BIO/UNZIPPED/AVE           # BIO high freq variables
          PHYS_DIR=$RUNDIR/PHYS/UNZIPPED/               # PHYS
######################################################

###  ELABORATION DIRS  ###############################
        START_PHYS=$NADRIDIR/PHYS/V4                   # Original for phys IC
    PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/GOT/                # Original for phys IC cutted
     BIOCUT_IC_DIR=$RUNDIR/BIO/IC/GOT/                 # BIO IC cutted
  TIMEINTERP___DIR=$NADRIDIR/BIO/IC/INTERPOLATED/

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
MASK_320=$RUNDIR/mask320.nc
MASK__F=$RUNDIR/maskINGV.nc
MASK16_Red=$RUNDIR/mask16R.nc
VAR_TO_INTERP=static-data/InterpVarNames
MODELVARS=static-data/ModelVarNames
VARLIST_HIGH=$RUNDIR/varlist_high
export RIVERDATA=static-data/masks/GoT/discharges_GoT.xlsx
export RIVERMETEODIR=$RUNDIR
######################################################


### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/V4/mask.nc.gz    > $MASK_16 "
medmit_prex_or_die "gzip -cd static-data/masks/GoT/mask.nc.gz   > $MASK_320 "
medmit_prex_or_die "gzip -cd static-data/masks/INGV/mask.nc.gz  > $MASK__F "

medmit_prex_or_die " python get_cut_Locations.py -c $MASK__F -f $MASK_320 > $RUNDIR/set_cut_indexes_INGV_vs_M320.sh "
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_16 -f $MASK_320 > $RUNDIR/set_cut_indexes_V4_vs_M320.sh "

medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_INGV_vs_M320.sh $RUNDIR/set_cut_indexes_V4_vs_M320.sh"

# getting Mask16 reduced Gulf of Trieste
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_V4_vs_M320.sh"
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_16 -O $MASK16_Red"
##################################################################





### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START
DATESTART8=${DATESTART:0:8}



medmit_prex_or_die " . nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M320.sh "
medmit_prex_or_die "./cutter.sh -i $START_PHYS -o $PHYSCUT_IC_DIR -c 'ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N ' "
medmit_prex_or_die "python IC_files_gen.py -m $MASK_320 --nativemask $MASK16_Red  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START "



## bio ##
medmit_prex_or_die " python high_var_list.py > $VARLIST_HIGH "
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_V4_vs_M320.sh "

medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $AVE_DIR          --datatype AVE -o $BIOCUT_IC_DIR -v $VARLIST_HIGH   -t $TIMELIST_START -m $MASK_16 "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP  -t $TIMELIST_START -m $MASK_16 "

medmit_prex_or_die "python IC_files_gen.py -m $MASK_320 --nativemask $MASK16_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS "

##################################################################



exit 0


getDataFrom_ADRI_Simulation.sh -i $NADRI_RUNDIR -o $OUTDIR




python MIT_cutter.py -m $MASK_64 --loncut $Index_E,$Index_W --latcut $Index_S,$Index_N -i $AVE_DIR -o $BIOCUT_DIR -v ModelVarNames -t $TIMELIST_START
#potrebbe scrivere NetCDF




python BC_files.gen.py -t $TIMELIST_TO___FILE -v ModelVarNames -m $MASK_320 -s S -o $BC_DIR --nativemask $MASK64_Red  -i $BIOCUT_DIR
