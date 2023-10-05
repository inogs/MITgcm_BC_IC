
#! /bin/bash
# FROM NADRI to GOT after NADRI run


MPI=

. ./profile.inc

DATESTART=20230930-00:00:00
DATE__END=20141201-12:00:00

RUNDIR=/g100_scratch/userexternal/gbolzon0/MIT/GoT/wrkdir
mkdir -p $RUNDIR


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


BATHY=$RUNDIR/bathy
MASKFILE=$RUNDIR/mask.nc
MASK_CADEAU=/g100_work/OGS_prodC/MIT/V1M-prod/wrkdir/BC_IC/mask.nc
MASK_CADEAU_RED=$RUNDIR/mask_CADEAU_reduced.nc

VAR_TO_INTERP=static-data/InterpVarNames
MODELVARS=static-data/ModelVarNames
VARLIST_HIGH=$RUNDIR/varlist_high
export RIVERDATA=static-data/masks/GoT/discharges_GoT.xlsx
export RIVERMETEODIR=$RUNDIR
######################################################


### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/GoT/bathy.gz   > $BATHY"
medmit_prex_or_die "python static-data/masks/GoT/maskgen.py  -b $BATHY  -o $MASKFILE "


medmit_prex_or_die " python get_cut_Locations.py -c $MASK_CADEAU -f $MASKFILE > $RUNDIR/set_cut_indexes_CADEAU_vs_local.sh "
source $RUNDIR/set_cut_indexes_CADEAU_vs_local.sh

medmit_prex_or_die "ncks -F -d lon,$((Index_W+1)),$((Index_E+1)) -d lat,$((Index_S+1)),$((Index_N+1)) -d depth,1,$Index_B $MASK_CADEAU -O $MASK_CADEAU_RED"
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_CADEAU_RED -f $MASK_CADEAU_RED > $RUNDIR/set_cut_indexes_local_itself.sh "

##################################################################





### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START

AVE_DIR=/g100_work/OGS_prodC/MIT/V1M-prod/wrkdir/POSTPROC/AVE/
CUT_IC_DIR=$RUNDIR/IC/CUT
mkdir -p $CUT_IC_DIR
VARLIST_HIGH="$RUNDIR/varlist.txt"
source $RUNDIR/set_cut_indexes_CADEAU_vs_local.sh
VARLIST_HIGH=static-data/masks/GoT/HF_statevars.txt
VARLIST_LOW=/g100_work/OGS_prodC/MIT/V1M-prod/etc/static-data/POSTPROC/merging_varlist_daily
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $AVE_DIR   --datatype ave -o $CUT_IC_DIR -v $VARLIST_HIGH  -t $TIMELIST_START -m $MASK_CADEAU "
medmit_prex_or_die "python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $AVE_DIR   --datatype ave -o $CUT_IC_DIR -v $VARLIST_LOW   -t $TIMELIST_START -m $MASK_CADEAU "

CUT_IC_DIR=$RUNDIR/IC/CUT
IC_DIR=$RUNDIR/IC
medmit_prex_or_die "python IC_files_gen.py -m $MASKFILE --nativemask $MASK_CADEAU_RED -i $CUT_IC_DIR -o $IC_DIR  -t $TIMELIST_START -v $VARLIST_HIGH "
medmit_prex_or_die "python IC_files_gen.py -m $MASKFILE --nativemask $MASK_CADEAU_RED -i $CUT_IC_DIR -o $IC_DIR  -t $TIMELIST_START -v $VARLIST_LOW "

##################################################################



exit 0


getDataFrom_ADRI_Simulation.sh -i $NADRI_RUNDIR -o $OUTDIR




python MIT_cutter.py -m $MASK_64 --loncut $Index_E,$Index_W --latcut $Index_S,$Index_N -i $AVE_DIR -o $BIOCUT_DIR -v ModelVarNames -t $TIMELIST_START
#potrebbe scrivere NetCDF




python BC_files.gen.py -t $TIMELIST_TO___FILE -v ModelVarNames -m $MASK_320 -s S -o $BC_DIR --nativemask $MASK64_Red  -i $BIOCUT_DIR
