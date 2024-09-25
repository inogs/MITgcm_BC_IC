#! /bin/bash


# Step 0. Get Mask info
# Step 1. Generating ftp batchfile
# Step 2. Getting files from archives
# Step 3. Space Interpolation

RUNDATE=20181019
DATESTART=$( date -d "${RUNDATE}  -  7  days " +%Y%m%d-%H:%M:%S )
DATE__END=$( date -d "${RUNDATE}  + 36 hours " +%Y%m%d-%H:%M:%S )
DOWNSTART=$( date -d "${RUNDATE}  -  8  days " +%Y%m%d-%H:%M:%S )
. ./profile.inc

RUNDIR=/marconi_scratch/userexternal/gbolzon0/OP_Cadeau/RUNDATES/${RUNDATE}
         MASK_ARSO=$RUNDIR/mask.arso.nc
          MASK_128=$RUNDIR/mask128.nc          # Cadeau mask
          BATHYGZ=bathy.gz
            BATHY=$RUNDIR/bathy.nc
DOWNLOADED_METEO=$RUNDIR/DOWNLOAD
      ORIG_METEO=$RUNDIR/ORIG/
        BC_METEO=$RUNDIR/BC/
   FTP_BATCHFILE=$RUNDIR/batchfile
DOWNTIMELISTFILE=$RUNDIR/to_download_timelist.txt
    TIMELISTFILE=$RUNDIR/meteo_timelist.txt
export PATH=$PATH:/share/scratch/backup_root/usr/bin/ # to have ftp on fluxus
export PATH=$PATH:/marconi/home/usera07ogs/a07ogs00/OPA/V3C/HOST/marconi/bin/

mkdir -p $RUNDIR
mkdir -p $DOWNLOADED_METEO
mkdir -p $ORIG_METEO


### Step 0.  GET MASK INFO  #####################################

medmit_prex_or_die "gzip -cd static-data/masks/METEO/mask.nc.gz > $MASK_ARSO "
medmit_prex_or_die "gzip -cd static-data/masks/CADEAU/${BATHYGZ} > $BATHY   "
medmit_prex_or_die "python static-data/masks/CADEAU/maskgen.py -b $BATHY -o $MASK_128  "


##################################################################


### Step 1. Generating ftp batchfile  ##########################

medmit_prex_or_die " python TimeList_generator.py -s $DOWNSTART -e $DATE__END -d \"days = 1 \" > $DOWNTIMELISTFILE "

medmit_prex_or_die " cat static-data/config/.meteo.config > $FTP_BATCHFILE "

echo lcd $DOWNLOADED_METEO >> $FTP_BATCHFILE
for I in `cat $DOWNTIMELISTFILE `; do
  YYYYMMDD=${I:0:8}
  FILENAME=asogsasc_${YYYYMMDD}00.tar.gz
  echo get $FILENAME >> $FTP_BATCHFILE
done

echo bye >> $FTP_BATCHFILE

##################################################################



### Step 2. Getting files from archives  #########################

medmit_prex_or_die " ncftp -u arso -p neva99! ftp.ogs.trieste.it < $FTP_BATCHFILE  "
# ftp -in < $FTP_BATCHFILE
for I in `ls $DOWNLOADED_METEO/*gz `; do medmit_prex_or_die "tar -xzf $I -C $ORIG_METEO "; done

##################################################################



### Step 3. Space Interpolation   ###############################

medmit_prex_or_die " python TimeList_generator.py -s $DATESTART -e $DATE__END -d 'hours = 1' > $TIMELISTFILE "
medmit_prex_or_die " python meteo_generator.py -i $ORIG_METEO -o $BC_METEO -m $MASK_128 --nativemask $MASK_ARSO -t $TIMELISTFILE "

##################################################################


medmit_prex_or_die " mv $BC_METEO/CHECK $RUNDIR "





