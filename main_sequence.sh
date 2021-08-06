#! /bin/bash

# executed on fluxus

DATESTART=20141001-12:00:00
DATE__END=20141201-12:00:00

write REQUEST for pico
send  REQUEST  to pico
./main_ICBC_Nadri.sh on pico
wait

get Results from pico

./mainMeteo.sh


run MITgcm on NADRI

./main_ICBC_Got.sh

run MITgcm on GoT



