#! /bin/bash


####     getForcingsFromArchive.sh #           #####
#   takes Forcings from Chain V4 Archive           #
#   by unzipping and renaming                      #
#                                                  #
#   Archive files have this kind of name:          # 
#   mfs_sys4d_20141125_20141124_a_T.nc.gz          #
#   Author: GB. 2015.01.08                         #
####################################################


usage() {
echo "Unzips and renames INGV physical forcings"
echo "SYNOPSYS"
echo "getForcingsFromArchive.sh [ -d DATESTART] [-w nWeeks ] [-O outputdir ] [-h host]"
echo "host can be localhost or remotehost : if remotehost, data are taken from galileo archive"
echo "in a hardcoded way"
echo ""
}

if [ $# -lt 8 ] ; then
  usage
  exit 1
fi

for I in 1 2 3 4; do
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
   echo "Getting Physical Forcings from $REMOTELOGIN "


   LOCAL_ARCHIVE_DIR=$UNZIPPED_DIR/local_archive/
   echo "Setting up local archive in $LOCAL_ARCHIVE_DIR"
   mkdir -p $LOCAL_ARCHIVE_DIR

   for (( week=0; week<$NWEEKS; week++ )); do
       RUN_DATE=`date -d "$DATESTART + $(( week * 7 )) days" +%Y%m%d `;
       echo "********* RUN DATE : $RUN_DATE"
       #continue
       mkdir -p $LOCAL_ARCHIVE_DIR/$RUN_DATE
       scp -r -i $KEY $REMOTELOGIN:$REMOTEDIR/$RUN_DATE/OPAOPER_A $LOCAL_ARCHIVE_DIR/$RUN_DATE
   done


   V4_DIR=$LOCAL_ARCHIVE_DIR
fi

echo "Start Decompressing Physical Forcings"

for (( week=0; week<$NWEEKS; week++ )); do
    RUN_DATE=`date -d "$DATESTART + $(( week * 7 )) days" +%Y%m%d `;
    echo "********* RUN DATE : $RUN_DATE"
    #continue
    ARCHIVE_DIR=${V4_DIR}/${RUN_DATE}/OPAOPER_A
    
	FILELIST=$(ls $ARCHIVE_DIR/*a_T.nc.gz)
	for I in $FILELIST; do
	  filename=`basename $I`   #mfs_sys4d_20141125_20141124_a_T.nc.gz
	  prefix=${filename:0:19}
	     day=${filename:19:8}
	  echo $day
	
	  gzip -dc ${ARCHIVE_DIR}/${prefix}${day}_a_T.nc.gz > ${UNZIPPED_DIR}/${day}_T.nc
	  gzip -dc ${ARCHIVE_DIR}/${prefix}${day}_a_U.nc.gz > ${UNZIPPED_DIR}/${day}_U.nc
	  gzip -dc ${ARCHIVE_DIR}/${prefix}${day}_a_V.nc.gz > ${UNZIPPED_DIR}/${day}_V.nc
	done    
    
done
