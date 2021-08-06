#! /bin/bash
#PBS -N ADIOS
#PBS -l walltime=5:20:00
#PBS -l select=3:ncpus=20:mpiprocs=20:mem=100GB
#PBS -q parallel
#PBS -A IscrC_ECOMED2_1
#


cd $PBS_O_WORKDIR


module purge
module load intel/cs-xe-2015--binary intelmpi/5.0.1--binary mkl/11.2.0--binary 
module load profile/advanced gnu/4.8.3 python/2.7.8 ; 
PYPATH=/pico/home/usera07ogs/a07ogs00/OPA/V4-dev/HOST/pico/lib/python2.7/site-packages/
export PYTHONPATH=$PYPATH:$PYTHONPATH 


DATESTART=20060101-12:00:00
DATE__END=20121231-12:00:00

RUNDIR=/pico/scratch/userexternal/gbolzon0/ADIOS/FOR_MIT
mkdir -p $RUNDIR
HERE=$PWD

cp $HOME/DISCHARGES/Isonzo_dd_2006_2013.txt $RUNDIR/Isonzo.txt
cp $HOME/DISCHARGES/Po_dd_2006_2013.txt     $RUNDIR/Po.txt
cp $HOME/DISCHARGES/Timavo_dd_2006_2013.txt $RUNDIR/Timavo.txt


#######  DOWNLOADED FILES DIRS  ######################
        AVE_FREQ_1=$RUNDIR/../ORIG_DATA/AVE_FREQ_1      # Files generated as links of 2006-2012 years
        AVE_FREQ_2=$RUNDIR/../ORIG_DATA/AVE_FREQ_2
          PHYS_DIR=$RUNDIR/../ORIG_DATA/PHYS
######################################################

###  ELABORATION DIRS  ###############################
        START_PHYS=$RUNDIR/PHYS/V4                      # Original for phys IC
    PHYSCUT_IC_DIR=$RUNDIR/PHYS/IC/ADRI/                # Original for phys IC cutted
  PHYSCUT_BC_DIR_E=$RUNDIR/PHYS/CUTTED_SLICES/EAST/     # BC slices phys
  PHYSCUT_BC_DIR_W=$RUNDIR/PHYS/CUTTED_SLICES/WEST/     # BC slices phys
     BIOCUT_IC_DIR=$RUNDIR/BIO/IC/ADRI/                 # BIO IC cutted
BIOCUT_BC_DIR_EAST=$RUNDIR/BIO/CUTTED_SLICES/EAST # BC slices BIO high freq
BIOCUT_BC_DIR_WEST=$RUNDIR/BIO/CUTTED_SLICES/WEST #BC slices BIO low freq
TIMEINTERPcutDIR_E=$RUNDIR/BIO/CUTTED_SLICES/INTERPOLATED/EAST
TIMEINTERPcutDIR_W=$RUNDIR/BIO/CUTTED_SLICES/INTERPOLATED/WEST
  TIMEINTERP___DIR=$RUNDIR/BIO/IC/INTERPOLATED/
    
######################################################

##### OUTPUTS,  ready for MITgcm  ####################
        BIO_BC_DIR=$RUNDIR/BC/BIO
        BIO_IC_DIR=$RUNDIR/IC/BIO
######################################################


######  FILES ########################################

TIMELIST_FROMhFILE=$RUNDIR/tl1.txt
TIMELIST_FROMlFILE=$RUNDIR/tl2.txt
TIMELIST_TO___FILE=$RUNDIR/tl3.txt
    TIMELIST_START=$RUNDIR/t0.txt

           MASK_16=$RUNDIR/mask16.nc
           MASK_32=$RUNDIR/mask32.nc
        MASK16_Red=$RUNDIR/mask16R.nc
       MODELVARS=static-data/ModelVarNames
     VARLIST_HIGH=HIGH_VARLIST
     VARLIST__LOW=LOW__VARLIST
export RIVERDATA=static-data/masks/ADIOS/discharges_ADIOS.xlsx
export RIVERMETEODIR=$RUNDIR
######################################################





### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/V4/mask.nc.gz    > $MASK_16 "
medmit_prex_or_die "gzip -cd static-data/masks/ADIOS/mask.nc.gz > $MASK_32 "

medmit_prex_or_die "python get_cut_Locations.py -c $MASK_16 -f $MASK_32  > $RUNDIR/set_cut_indexes_V4_vs_M32.sh"
medmit_prex_or_die "chmod 744 $RUNDIR/set_cut_indexes_V4_vs_M32.sh"

# getting Mask16 reduced on ADR ION 
medmit_prex_or_die ". nco_indexer.sh $RUNDIR/set_cut_indexes_V4_vs_M32.sh "
medmit_prex_or_die " ncks -F -a -d lon,$Index_W,$Index_E -d lat,$Index_S,$Index_N $MASK_16 -O $MASK16_Red "
##################################################################




### Step 2. LINEAR TIME INTERPOLATION  ###########################
#mkdir -p  $AVE_FREQ_1
cd $AVE_FREQ_1
#for I in `ls /gss/gss_work/try14_bolzon/RA_16/wrkdir/MODEL/AVE_FREQ_1/*nc`; do ln -fs $I ; done
for var in `cat ${HERE}/$VARLIST_HIGH `; do ln -fs ave.20121228-12:00:00.${var}.nc  ave.20130104-12:00:00.${var}.nc ; done

#mkdir  -p  $AVE_FREQ_2
cd $AVE_FREQ_2
#for I in `ls /gss/gss_work/try14_bolzon/RA_16/wrkdir/MODEL/AVE_FREQ_2/*nc`; do ln -fs $I ; done
for var in `cat ${HERE}/$VARLIST__LOW `; do ln -fs ave.20121216-12:00:00.${var}.nc  ave.20130104-12:00:00.${var}.nc ; done

cd $HERE

python TimeList_generator.py -s 20051230-12:00:00 -e 20130104-12:00:00 -d "days = 7" > $TIMELIST_FROMhFILE

# We get TIMELIST_FROM  from existing files
cat /dev/null > $TIMELIST_FROMlFILE
for I in `ls $AVE_FREQ_2/*Z6p*.nc | tail -86 `; do
   filename=`basename $I`
   echo ${filename:4:17} >> $TIMELIST_FROMlFILE
done


# TIMELIST_TO is generated
python TimeList_generator.py -s $DATESTART -e $DATE__END -d "days = 1" > $TIMELIST_TO___FILE

# python Varlist_generator.py > $VAR_TO_INTERP # done once and for all
##################################################################




if [ 1 == 0 ] ; then

### Step 3. INITIAL CONDITIONS ###################################

echo ${DATESTART} > $TIMELIST_START
DATESTART8=${DATESTART:0:8}

## phys  ##
mkdir -p $START_PHYS

for I in `ls $PHYS_DIR/*${DATESTART8}* ` ; do 
   filename=`basename $I `
   ln -fs $I $START_PHYS/$filename
done

. nco_indexer.sh $RUNDIR/set_cut_indexes_INGV_vs_M64.sh 
./cutter.sh -i $START_PHYS -o $PHYSCUT_IC_DIR -c "ncks -F -a -d x,$Index_W,$Index_E -d y,$Index_S,$Index_N "
python IC_files_gen.py -m $MASK_64 --nativemask $MASK16_Red  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START


## bio ##
. $RUNDIR/set_cut_indexes_V4_vs_M64.sh

python Time_interpolator.py -i $RESTARTS_DIR  --datatype RST -o $TIMEINTERP___DIR -v $VAR_TO_INTERP -if $TIMELIST_FROM_FILE -of $TIMELIST_START -m $MASK_16

python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $AVE_DIR          --datatype AVE -o $BIOCUT_IC_DIR -v $VARLIST_HIGH  -t $TIMELIST_START -m $MASK_16
python ogstm_cutter.py  --loncut $Index_W,$Index_E --latcut $Index_S,$Index_N -i $TIMEINTERP___DIR --datatype ave -o $BIOCUT_IC_DIR -v $VAR_TO_INTERP  -t $TIMELIST_START -m $MASK_16

python IC_files_gen.py -m $MASK_64 --nativemask $MASK16_Red -i $BIOCUT_IC_DIR -o $BIO_IC_DIR  -t $TIMELIST_START -v $MODELVARS

##################################################################






### Step 4. BOUNDARY CONDITIONS ##################################


## phys ##
. nco_indexer.sh $RUNDIR/set_cut_indexes_V4_vs_M32.sh
./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR_W -c "ncks -F -a -d x,$Index_W,$Index_W -d y,$Index_S,$Index_N "
./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR_E -c "ncks -F -a -d x,$Index_E,$Index_E -d y,$Index_S,$Index_N "

python BC_files_gen_PHYS.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_32 -s E -o $PHYS_BC_DIR --nativemask $MASK16_Red  -i $PHYSCUT_BC_DIR_E
python BC_files_gen_PHYS.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_32 -s W -o $PHYS_BC_DIR --nativemask $MASK16_Red  -i $PHYSCUT_BC_DIR_W
python BC_files_gen_PHYS.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_32 -s N -o $PHYS_BC_DIR

fi

## bio ##

. $RUNDIR/set_cut_indexes_V4_vs_M32.sh

mpirun python ogstm_cutter.py  --loncut $Index_W,$Index_W --latcut $Index_S,$Index_N -i $AVE_FREQ_1 --datatype ave -o $BIOCUT_BC_DIR_WEST -v $VARLIST_HIGH -t $TIMELIST_FROMhFILE -m $MASK_16
mpirun python ogstm_cutter.py  --loncut $Index_W,$Index_W --latcut $Index_S,$Index_N -i $AVE_FREQ_2 --datatype ave -o $BIOCUT_BC_DIR_WEST -v $VARLIST__LOW -t $TIMELIST_FROMlFILE -m $MASK_16

mpirun python ogstm_cutter.py  --loncut $Index_E,$Index_E --latcut $Index_S,$Index_N -i $AVE_FREQ_1 --datatype ave -o $BIOCUT_BC_DIR_EAST -v $VARLIST_HIGH -t $TIMELIST_FROMhFILE -m $MASK_16
mpirun python ogstm_cutter.py  --loncut $Index_E,$Index_E --latcut $Index_S,$Index_N -i $AVE_FREQ_2 --datatype ave -o $BIOCUT_BC_DIR_EAST -v $VARLIST__LOW -t $TIMELIST_FROMlFILE -m $MASK_16


mpirun python BC_Time_interpolator.py -i $BIOCUT_BC_DIR_WEST -o $TIMEINTERPcutDIR_W -if $TIMELIST_FROMhFILE -of $TIMELIST_TO___FILE -v $VARLIST_HIGH -s W -m $MASK16_Red
mpirun python BC_Time_interpolator.py -i $BIOCUT_BC_DIR_WEST -o $TIMEINTERPcutDIR_W -if $TIMELIST_FROMlFILE -of $TIMELIST_TO___FILE -v $VARLIST__LOW -s W -m $MASK16_Red

mpirun python BC_Time_interpolator.py -i $BIOCUT_BC_DIR_EAST -o $TIMEINTERPcutDIR_E -if $TIMELIST_FROMhFILE -of $TIMELIST_TO___FILE -v $VARLIST_HIGH -s E -m $MASK16_Red
mpirun python BC_Time_interpolator.py -i $BIOCUT_BC_DIR_EAST -o $TIMEINTERPcutDIR_E -if $TIMELIST_FROMlFILE -of $TIMELIST_TO___FILE -v $VARLIST__LOW -s E -m $MASK16_Red


mpirun python BC_files_gen.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_32 -s E -o $BIO_BC_DIR --nativemask $MASK16_Red  -i $TIMEINTERPcutDIR_E
mpirun python BC_files_gen.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_32 -s W -o $BIO_BC_DIR --nativemask $MASK16_Red  -i $TIMEINTERPcutDIR_W
mpirun python BC_files_gen.py -t $TIMELIST_TO___FILE -v $MODELVARS -m $MASK_32 -s N -o $BIO_BC_DIR


##################################################################





### Step 5. Prepare data to fluxus ###


mkdir -p $RUNDIR/CHECK/BC
mv $RUNDIR/BC/BIO/CHECK/  $RUNDIR/CHECK/BC/BIO

cd $RUNDIR
tar -czf $RUNDIR/bc.tar.gz  BC 



