#! /bin/bash
python TimeList_generator.py -s 20060101-12:00:00 -e 20170103-12:00:00 --days 1 > timelist.txt

INPUTDIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/fiumi_squerin
OUTDIR=/marconi_scratch/userexternal/vdibiagi/REA_IC_BC/fiumi_squerin/river_meteo_data

python river_gen.py -t timelist.txt -i $INPUTDIR/Isonzo_dd_2006_2016_added.txt -o $OUTDIR/Isonzo.txt
python river_gen.py -t timelist.txt -i $INPUTDIR/Po_dd_2006_2016_added.txt     -o $OUTDIR/Po.txt
python river_gen.py -t timelist.txt -i $INPUTDIR/Timavo_dd_2006_2016_added.txt -o $OUTDIR/Timavo.txt

