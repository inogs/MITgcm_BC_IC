#! /bin/bash


####     getRST__BIOFromArchive.sh             #####
#   takes RST files from Chain V4 Archive          #
#   by unzipping                                   #
#                                                  #
#   Author: GB. 2015.01.08                         #
####################################################


usage() {
echo "Unzips weekly restart Files from chain"
echo "SYNOPSYS"
echo "getRST__BIOFromArchive.sh [ -d DATESTART] [-w nWeeks ] [-O outputdir ] [-h host] "
echo "host can be localhost or remotehost : if remotehost, data are taken from galileo archive"
echo "in a hardcoded way"
echo ""
}

if [ $# -lt 8 ] ; then
  usage
  exit 1
fi

for I in 1 2 3 4 ; do
   case $1 in
      "-d" ) DATESTART=$2;;
      "-w" ) NWEEKS=$2;;
      "-O" ) UNZIPPED_DIR=$2;;
      "-h" ) HOST=$2;;
        *  ) echo "Unrecognized option $1." ; usage;  exit 1;;
   esac
   shift 2
done

WEEKDAY=`date -d $DATESTART +%A `
if [[ $WEEKDAY != Tuesday ]] ; then
   echo "I accepy only Tuesdays: $DATESTART is a $WEEKDAY "
   exit 1
fi

mkdir -p $UNZIPPED_DIR


V4_DIR=/pico/home/usera07ogs/a07ogs00/OPA/V4-dev/archive

if [ $HOST == 'remotehost' ] ; then   
   REMOTELOGIN=gbolzon0@login.galileo.cineca.it
   KEY=/pico/home/userexternal/gbolzon0/.ssh/toGB_galileo-key
   REMOTEDIR=/gpfs/meteo/PLX/OGS/OPA/V4/prod/archive/
   echo "Getting Low Freq RST files from $REMOTELOGIN "


   LOCAL_ARCHIVE_DIR=$UNZIPPED_DIR/local_archive/
   echo "Setting up local archive in $LOCAL_ARCHIVE_DIR"
   mkdir -p $LOCAL_ARCHIVE_DIR

   for (( week=0; week<$NWEEKS; week++ )); do
       RUN_DATE=`date -d "$DATESTART + $(( week * 7 )) days" +%Y%m%d `;
       echo "********* RUN DATE : $RUN_DATE"
       #continue
       LOCALDIR=$LOCAL_ARCHIVE_DIR/$RUN_DATE/MODEL
       mkdir -p $LOCALDIR

       REMOTEFILE=$REMOTELOGIN:$REMOTEDIR/$RUN_DATE/MODEL/RST*.gz        
       scp -i $KEY $REMOTEFILE $LOCALDIR

       RUN_DATE=`date -d "$RUN_DATE + 3 days" +%Y%m%d `
       LOCALDIR=$LOCAL_ARCHIVE_DIR/$RUN_DATE/MODEL
       mkdir -p $LOCALDIR

       REMOTEFILE=$REMOTELOGIN:$REMOTEDIR/$RUN_DATE/MODEL/RST*.gz        
       scp -i $KEY $REMOTEFILE $LOCALDIR

   done


   V4_DIR=$LOCAL_ARCHIVE_DIR
fi

echo "Start Decompressing Bio Low Freq Data"

for (( week=0; week<$NWEEKS; week++ )); do
    RUN_DATE=`date -d "$DATESTART + $(( week * 7 )) days" +%Y%m%d `;
    echo "********* RUN DATE : $RUN_DATE"
    #continue
    ARCHIVE_DIR=${V4_DIR}/${RUN_DATE}/MODEL
    
    FILELIST=$(ls $ARCHIVE_DIR/RST*.gz)
    for I in $FILELIST; do
        filename=`basename $I`   #RST.20141104-12:00:00.nc.gz
        echo $filename
	gzip -dc $I > ${UNZIPPED_DIR}/${filename%.gz}
    done

    RUN_DATE=`date -d "$RUN_DATE + 3 days" +%Y%m%d `;
    ARCHIVE_DIR=${V4_DIR}/${RUN_DATE}/MODEL
    
    FILELIST=$(ls $ARCHIVE_DIR/RST*.gz)
    for I in $FILELIST; do
        filename=`basename $I`   #RST.20141104-12:00:00.nc.gz
        echo $filename
	gzip -dc $I > ${UNZIPPED_DIR}/${filename%.gz}
    done

    
done


