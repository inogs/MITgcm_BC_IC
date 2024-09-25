
#! /bin/bash
# FROM NADRI to GOT after NADRI run


MPI=

. ./profile.inc

DATESTART=20231203-00:00:00
DATE__END=20231207-00:00:00

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

if [ 1 == 0 ] ; then

### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/GoT/bathy.gz   > $BATHY"
medmit_prex_or_die "python static-data/masks/GoT/maskgen.py  -b $BATHY  -o $MASKFILE "


medmit_prex_or_die " python get_cut_Locations.py -c $MASK_CADEAU -f $MASKFILE > $RUNDIR/set_cut_indexes_CADEAU_vs_local.sh "
source $RUNDIR/set_cut_indexes_CADEAU_vs_local.sh

medmit_prex_or_die "ncks -F -d lon,$((Index_W+1)),$((Index_E+1)) -d lat,$((Index_S+1)),$((Index_N+1)) -d depth,1,$Index_B $MASK_CADEAU -O $MASK_CADEAU_RED"
medmit_prex_or_die " python get_cut_Locations.py -c $MASK_CADEAU_RED -f $MASK_CADEAU_RED > $RUNDIR/set_cut_indexes_local_itself.sh "

##################################################################
fi




### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START


CUT_IC_DIR=$RUNDIR/IC/CUT
mkdir -p $CUT_IC_DIR


VARLIST_HIGH=static-data/masks/GoT/HF_statevars.txt
VARLIST_LOW=/g100_work/OGS_prodC/MIT/V1M-prod/etc/static-data/POSTPROC/merging_varlist_daily


AVE_DIR=/g100_work/OGS_prodC/MIT/V1M-prod/wrkdir/POSTPROC/AVE/
ALL_VARS=/g100_work/OGS_prodC/MIT/V3/devel/wrkdir/all_vars.txt
MASK_INPUTS=/g100_work/OGS_prodC/MIT/V1M-prod/wrkdir/BC_IC/mask.nc
MASK=/g100_work/OGS_prodC/MIT/V3/devel/wrkdir/BC_IC/mask.nc


medmit_prex_or_die "python ogstm_cutter.py  -i $AVE_DIR   --datatype ave -o $CUT_IC_DIR -v $ALL_VARS  -t $TIMELIST_START -M $MASK_INPUTS -m $MASK"

MASK_INPUTS_REDUCED=/g100_work/OGS_prodC/MIT/V3/devel/wrkdir/BC_IC/mask_CADEAU_reduced.nc
IC_DIR=$RUNDIR/IC/
mkdir -p $IC_DIR
medmit_prex_or_die "python IC_files_gen.py -m $MASK --nativemask $MASK_INPUTS_REDUCED  -i $CUT_IC_DIR -o $IC_DIR -t $TIMELIST_START -v $ALL_VARS"



##################################################################


### Step 3. INITIAL CONDITIONS ###################################

TIMES_HF=$RUNDIR/BC/hourly.txt
TIMES_LF=$RUNDIR/BC/daily.txt
medmit_prex_or_die "python TimeList_generator.py -s $DATESTART -e $DATE__END --hours 1 > $TIMES_HF "
medmit_prex_or_die "python TimeList_generator.py -s $DATESTART -e $DATE__END --days  1 > $TIMES_LF "
SIDE=S
CUT_BC_DIR=$RUNDIR/BC/
mkdir -p $CUT_BC_DIR

BC_DIR=$RUNDIR/BC/
VARLIST_HIGH=/g100_work/OGS_prodC/MIT/V3M-dev/wrkdir/hourly_vars.txt
medmit_prex_or_die "python ogstm_cutter.py  -i $AVE_DIR --datatype ave --side ${SIDE} -o $CUT_BC_DIR/HF/${SIDE} -v $VARLIST_HIGH -t $TIMES_HF -M $MASK_INPUTS -m $MASK"
medmit_prex_or_die "python ogstm_cutter.py  -i $AVE_DIR --datatype ave --side ${SIDE} -o $CUT_BC_DIR/LF/${SIDE} -v $VARLIST_LOW  -t $TIMES_LF -M $MASK_INPUTS -m $MASK"

medmit_prex_or_die "python BC_files_gen.py -t $TIMES_HF -m $MASK -v $ALL_VARS  -s S -o $BC_DIR -i  $CUT_BC_DIR/HF/S --nativemask $MASK_INPUTS_REDUCED"


for I in $CUT_BC_DIR/LF/${SIDE}/* ; do
   mit_prex_or_die "mit_hourly_linker $I $CUT_BC_DIR/HF/${SIDE}"
done



