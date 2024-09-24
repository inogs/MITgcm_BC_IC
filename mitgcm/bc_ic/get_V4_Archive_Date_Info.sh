#! /bin/bash


####     get_V4_Archive_Date_Info.sh          ######
#                                                  #
#        Returns the date of the Tuesday to        #
#        access V4 archives, and the number        #
#        of weeks (chain runs) to cover the        #
#        requirement                               #
#                                                  #
#   Author: GB. 2015.02.21                         #
####################################################



usage() {
echo "Gets info to access V4 archive data "
echo "SYNOPSYS"
echo "get_V4_Archive_Date_Settings [ -s DATESTART] [-e DATEEND ]"
echo "Datestart and DateEnd must be expressed at least by yyyymmdd, longer formats are accepted "
echo "Prints on stdout : "
echo " -the date of the last suitable tuesday, the date to access V4 archive"
echo " -the number of weeks needed (Analysis data) to cover the period between two dates"
echo "EXAMPLE"
echo "get_Archive_Date_Settings.sh -s 20141001 -e 20141005"
}

if [ $# -lt 4 ] ; then
  usage
  exit 1
fi

for I in 1 2 ; do
case $1 in
"-s" ) DATESTART=$2;;
"-e" ) DATE__END=$2;;
*  ) echo "Unrecognized option $1." ; usage;  exit 1;;
esac
shift 2
done




# Find the last Tuesday

for (( day =-6; day<1 ; day++ )) ; do
#echo $day
   DAY=`date -d "${DATESTART:0:8} + $day days " +%Y%m%d `
   WEEKDAY=`date -d  $DAY +%A `
#echo $WEEKDAY
   if [[ $WEEKDAY == Tuesday ]] ; then
     ARCHIVE_DATESTART=$DAY
    fi
done




D2=`date -d ${DATE__END:0:8} +%Y%m%d `

for (( week =0 ; week<100 ; week++ )) ; do
   RUN_DATE=`date -d "$ARCHIVE_DATESTART + $(( week * 7 )) days" +%Y%m%d `
if [ $RUN_DATE -gt $D2 ] ; then
   break

fi
done


echo $ARCHIVE_DATESTART
echo $week

