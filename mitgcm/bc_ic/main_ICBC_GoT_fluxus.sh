#! /bin/bash


# Step 0. Get Mask info
. ./profile.inc

DATESTART=20141001-12:00:00
DATE__END=20141201-12:00:00


RUNDIR=/share/scratch/gbolzon/GoT
mkdir -p $RUNDIR

medmit_prex "cp $HOME/DISCHARGES/Timavo_oct_nov_2013.txt $RUNDIR/Timavo.txt"  # Daily
medmit_prex "cp $HOME/DISCHARGES/Isonzo_oct_nov_2014.txt $RUNDIR/Isonzo.txt"  #Hourly data

       NADRI_DIR=/share/scratch/squerin/MIT_run/TOSCA_II/run_61dd

###  ELABORATION DIRS  ###############################
         CUT_DIR_S=$RUNDIR/CUT/South
         CUT_DIR_W=$RUNDIR/CUT/West
######################################################


##### OUTPUTS,  ready for MITgcm  ####################
            BC_DIR=$RUNDIR/BC/
            IC_DIR=$RUNDIR/IC/BIO
######################################################



######  FILES ########################################
TIMELIST_TO___FILE=$RUNDIR/tl2.txt
TIMELIST_HR___FILE=$RUNDIR/tl_hr.txt
    TIMELIST_START=$RUNDIR/t0.txt

           MASK_64=$RUNDIR/mask64.nc
          MASK_320=$RUNDIR/mask320.nc
        MASK64_Red=$RUNDIR/mask64R.nc
     ALLVARS=$RUNDIR/varlist
    MODELVARS=static-data/ModelVarNames
export RIVERDATA=static-data/masks/GoT/discharges_GoT.xlsx
export RIVERMETEODIR=$RUNDIR
######################################################







### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/NADRI/mask.nc.gz > $MASK_64 "
medmit_prex_or_die "gzip -cd static-data/masks/GoT/mask.nc.gz   > $MASK_320 "


medmit_prex_or_die " python get_cut_Locations.py -c $MASK_64 -f $MASK_320 > $RUNDIR/set_cut_indexes_NADRI_vs_M320.sh "
medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_NADRI_vs_M320.sh "

# getting Mask64 reduced Gulf of Trieste
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_NADRI_vs_M320.sh"
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_64 -O $MASK64_Red"
##################################################################





### Step 4. BOUNDARY CONDITIONS ##################################
# Times of North Side 2
medmit_prex_or_die " python TimeList_generator.py -s $DATESTART -e $DATE__END -d 'hours = 1' > $TIMELIST_HR___FILE "
medmit_prex_or_die " python TimeList_generator.py -s $DATESTART -e $DATE__END -d 'days = 1'  > $TIMELIST_TO___FILE "

medmit_prex_or_die " cp $MODELVARS $ALLVARS ; echo U>>$ALLVARS ; echo V>>$ALLVARS ; echo T>>$ALLVARS; echo S>>$ALLVARS"


## bio ##
medmit_prex_or_die " . $RUNDIR/set_cut_indexes_NADRI_vs_M320.sh "

medmit_prex_or_die "$MPI python MIT_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_S -i $NADRI_DIR -o $CUT_DIR_S -v $ALLVARS -t $TIMELIST_TO___FILE -m $MASK_64"
medmit_prex_or_die "$MPI python MIT_cutter.py  --loncut $Index_W,$Index_W --latcut $Index_S,$Index_N -i $NADRI_DIR -o $CUT_DIR_W -v $ALLVARS -t $TIMELIST_TO___FILE -m $MASK_64"


medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMELIST_TO___FILE -v $ALLVARS -m $MASK_320 -s S -o $BC_DIR --nativemask $MASK64_Red  -i $CUT_DIR_S"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMELIST_TO___FILE -v $ALLVARS -m $MASK_320 -s W -o $BC_DIR --nativemask $MASK64_Red  -i $CUT_DIR_W"
medmit_prex_or_die "$MPI python BC_files_gen.py -t $TIMELIST_HR___FILE -v $ALLVARS -m $MASK_320 -s E -o $BC_DIR "





##################################################################


