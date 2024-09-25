#! /bin/bash

usage() {
echo "set nco indexes (i.e starting by 1) by using a bash file defined for python indexes (starting by 0)"
echo "Increments indexes by 1, conversion needed for cutting with nco package "
echo "Argument file has been created by get_cut_Locations.py"
echo "SYNOPSYS"
echo "nco_indexer.sh [ filename]"
echo "EXAMPLE"
echo '. /nco_indexer.sh set_cut_indexes_mask1_vs_mask2.sh '
echo ""
}


if [ $# -lt 1 ] ; then
  usage
  exit 1
fi

filename=$1

. $filename

Index_W=$(( Index_W + 1 ))
Index_E=$(( Index_E + 1 ))
Index_S=$(( Index_S + 1 ))
Index_N=$(( Index_N + 1 ))
