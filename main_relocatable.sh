#! /bin/bash

. ./profile.inc
MIT_RUNDATE=20210916

MASKFILE=/g100_work/OGS_prod100/MIT/V1M-prod/wrkdir/BC_IC/mask.nc
MASKFILE=/gpfs/work/OGS_prod_0/MIT/V1-prod/wrkdir/BC_IC/mask.nc
MASK_006_014=/g100_scratch/userexternal/gbolzon0/RA_24/meshmask_006_014.nc
MASK_006_014_RED=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/mask_ogstm_reduced.nc
PRODUCT_TABLE=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/product_table.txt
medmit_prex_or_die "python3 get_cut_Locations.py -c $MASK_006_014 -f $MASKFILE > set_cut_indexes_006_014_vs_local.sh"
JSON=/g100_work/OGS_prod100/MIT/V1M-prod/etc/motu-config/motu_downloader.json
source ./set_cut_indexes_006_014_vs_local.sh

medmit_prex_or_die "python maskgen_006_014.py -i /g100_work/OGS_prod100/MIT/V1M-dev/V1/devel/wrkdir/MARINE_COPERNICUS -o $MASK_006_014"

medmit_prex_or_die "ncks -F -d x,$((Index_W+1)),$((Index_E+1)) -d y,$((Index_S+1)),$((Index_N+1)) -d z,1,$Index_B $MASK_006_014 -O $MASK_006_014_RED"

if [ 1 == 1 ] ; then
jq '.services[].products[] | .name as $name | .variables[] | $name + " " + .' $JSON | cut -d "\"" -f 2 > $PRODUCT_TABLE


OUTPUTDIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/AVE/PHYS
rm -rf $OUTPUTDIR
mkdir -p $OUTPUTDIR
grep cmcc $PRODUCT_TABLE | while read dataset var ; do 
   INPUTFILE=/g100_work/OGS_prod100/MIT/V1M-dev/V1/devel/wrkdir/MARINE_COPERNICUS/${dataset}-$MIT_RUNDATE.nc
   medmit_prex_or_die "python3 products_converter.py -v $var -i $INPUTFILE -o $OUTPUTDIR -m $MASK_006_014_RED"
done 

OUTPUTDIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/AVE/BIO
rm -rf $OUTPUTDIR
mkdir -p $OUTPUTDIR
grep ogs $PRODUCT_TABLE | while read dataset var ; do 
   INPUTFILE=/g100_work/OGS_prod100/MIT/V1M-dev/V1/devel/wrkdir/MARINE_COPERNICUS/${dataset}-$MIT_RUNDATE.nc
   medmit_prex_or_die "python3 products_converter.py -v $var -i $INPUTFILE -o $OUTPUTDIR -m $MASK_006_014_RED"
done

TIMELIST_START=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/timelist.start.txt
PHYSCUT_IC_DIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/PHYSCUT_IC_DIR
PHYSIC_DIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/PHYSIC_DIR
medmit_prex_or_die "python IC_files_gen.py -m $MASKFILE --nativemask $MASK_006_014_RED  -i $PHYSCUT_IC_DIR -o $PHYSIC_DIR -t $TIMELIST_START "



PHYSCUT_BC_DIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/BC_CUT
mkdir -p PHYSCUT_BC_DIR/SOUTH
python3 get_cut_Locations.py -c $MASK_006_014_RED -f $MASK_006_014_RED > set_cut_indexes_local_itself.sh
source ./set_cut_indexes_local_itself.sh
PHYS_DIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/AVE/PHYS
medmit_prex_or_die "./cutter.sh -i $PHYS_DIR -o $PHYSCUT_BC_DIR/SOUTH  -c 'ncks -F -d longitude,$((Index_W+1)),$((Index_E+1)) -d latitude,$((Index_S+1)),$((Index_S+1)) ' "
 

TIMES_DAILY=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/timelist.txt
PHYS_BC_DIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/BC_PHYS
mkdir -p $PHYS_BC_DIR
export RIVERDATA=static-data/masks/CADEAU/discharges_CADEAU_N2.xlsx
export RIVERMETEODIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/
medmit_prex_or_die " python BC_files_gen_PHYS.py -t $TIMES_DAILY -m $MASKFILE --nativemask $MASK_006_014_RED -s S -i $PHYSCUT_BC_DIR/SOUTH  -o $PHYS_BC_DIR"
fi

OUTPUTDIR=/g100_scratch/userexternal/gbolzon0/MIT_CHAIN/BIO_IC_DIR
medmit_prex_or_die "python IC_files_gen.py -m $MASKFILE --nativemask /g100_work/OGS_prod100/MIT/V1M-dev/V1/devel/wrkdir/BC_IC/mask_006_014_reduced.nc  -i /g100_work/OGS_prod100/MIT/V1M-dev/V1/devel/wrkdir/BC_IC/BIO/AVE/DAILY -o $OUTPUTDIR  -t /g100_work/OGS_prod100/MIT/V1M-dev/V1/devel/wrkdir/t0.txt -v /g100_work/OGS_prod100/MIT/V1M-dev/V1/devel/wrkdir/ogstm_state_vars.txt"


