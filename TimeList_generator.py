import argparse


def argument():
    parser = argparse.ArgumentParser("Generates an ordered time list")
    parser.add_argument(   '--datestart',"-s",
                                type = str,
                                required = True,
                                help = '20120101-12:00:00')
    parser.add_argument(   '--dateend',"-e",
                                type = str,
                                required = True,
                                help = '20120110-12:00:00')
    parser.add_argument(   '--delta',"-d",
                                type = str,
                                required = True,
                                help = 'days = 1')    
    
    
    return parser.parse_args()

args = argument()
import genUserDateList as DL

TL   = DL.getTimeList(args.datestart, args.dateend, args.delta )
dateFormat="%Y%m%d-%H:%M:%S"
for t in TL:
    print t.strftime(dateFormat)

