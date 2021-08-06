#! /bin/bash

usage() {
echo "Cuts NetCDF files from a directory to another preserving file names"
echo "using ncks as a kernel"
echo "SYNOPSYS"
echo "cutter.sh [ -i INPUTDIR] [-o outputdir ] [-c command ]"
echo "EXAMPLE"
echo 'cutter.sh -i /input/path/ -o /output/path/ -c "ncks -F -a -d x,487,487 -d y,1,253 " '
echo ""
}

if [ $# -lt 6 ] ; then
  usage
  exit 1
fi

for I in 1 2 3 ; do
   case $1 in
      "-i" ) INPUTDIR=$2;;
      "-c" ) COMMAND=$2;;
      "-o" ) OUTPUTDIR=$2;;
        *  ) echo "Unrecognized option $1." ; usage;  exit 1;;
   esac
   shift 2
done

mkdir -p $OUTPUTDIR

FILELIST=$(ls $INPUTDIR/*.nc)
   
  
for I in $FILELIST; do
	filename=`basename $I`   #20141123_T.nc
        echo $filename
	$COMMAND ${INPUTDIR}/$filename -O ${OUTPUTDIR}/$filename
done
