import os 
import glob 
import sys

import data_extractor 


def interpolate(
    inputDir, 
    timeList, 
    maskFile,   
    varNames, 
    outputDir 
):
    with open( timeList ) as f:
        times = f.read().split( '\n' )

    dates = set()
    for time in times:
        date = time.strip().split('-')[0]
        if len(date) < 1:
            continue
        
        while len(date) < 10: 
            date = date + '0' 

        dates.add( date )
    dates = sorted([ date for date in dates ])

    print( 'interpolating gribs for dates:', dates )

    gribsFolder = f'{inputDir}/gribs'
    for date in dates:
        print( f'working on date {date} ... ', end = '' )

        try:
            lsm_filepath = glob.glob( os.path.join( gribsFolder, 'lsm', 'grib78.grib' ) )[0]
            ins_filepath = glob.glob( os.path.join( gribsFolder, date, 'inst', 'grib78.grib' ) )[0]
            acc_filepath = glob.glob( os.path.join( gribsFolder, date, 'acc', 'grib78.grib' ) )[0]
            avg_filepath = glob.glob( os.path.join( gribsFolder, date, 'ave', 'grib78.grib' ) )[0]
        except:
            print("not found")
            continue

        extractor = data_extractor.DataExtractor(
            lsm_filepath, 
            ins_filepath, 
            acc_filepath, 
            avg_filepath,  
            maskFile
        )   

        extractor.write_binaries(
           varNames, 
           outputDir,
           date
        )
        print( 'done' )

    for var in varNames:
        file_list = glob.glob(os.path.join(outputDir, f'BC_*_{var}'))
        date_list = [date.split("_")[1] for date in file_list]
        # print (var, date_list)
        if set(dates) - set(date_list) != set():
            print("impossible to continue")
            exit(1)

        outpath = f'BC_{var}'
        if os.path.exists(outpath):
            os.remove(outpath)

        with open(outpath, 'ab') as outfile:
            for date in dates:
                inpath = f'{outputDir}/BC_{date}_{var}'
                with open(inpath, 'rb') as infile:
                    outfile.write(infile.read())
        
        
    print("all binaries have been generated")

    return None
