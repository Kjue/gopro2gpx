#!/usr/bin/env python
#
# 17/02/2019 
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#


import subprocess
import re
import struct
import os
import platform
import argparse
from collections import namedtuple
import array
import sys
import time
from datetime import datetime

import config
import gpmf
import fourCC
import time
import sys

import gpshelper

import json

def BuildGPSPoints(data, skip=False):
    """
    Data comes UNSCALED so we have to do: Data / Scale.
    Do a finite state machine to process the labels.
    GET
     - SCAL     Scale value
     - GPSF     GPS Fix
     - GPSU     GPS Time
     - GPS5     GPS Data
    """

    points = []
    SCAL = fourCC.XYZData(1.0, 1.0, 1.0)
    GPSU = None    
    SYST = fourCC.SYSTData(0, 0)

    stats = { 
        'ok': 0,
        'badfix': 0,
        'badfixskip': 0,
        'empty' : 0
    }

    GPSFIX = 0 # no lock.
    for d in data:
        if d.fourCC == 'SCAL':
            SCAL = d.data
        elif d.fourCC == 'STNM':
            print(d.data)
        elif d.fourCC == 'GPSU':
            GPSU = d.data
        elif d.fourCC == 'GPSF':
            if d.data != GPSFIX:
                print("GPSFIX change to %s [%s]" % (d.data,fourCC.LabelGPSF.xlate[d.data]))
            GPSFIX = d.data
        elif d.fourCC == 'GPS5':
            if d.data.lon == d.data.lat == d.data.alt == 0:
                print("Warning: Skipping empty point")
                stats['empty'] += 1
                continue

            if GPSFIX == 0:
                stats['badfix'] += 1
                if skip:
                    print("Warning: Skipping point due GPSFIX==0")
                    stats['badfixskip'] += 1
                    continue                    

            data = [ float(x) / float(y) for x,y in zip( d.data._asdict().values() ,list(SCAL) ) ]
            gpsdata = fourCC.GPSData._make(data)
            p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, datetime.fromtimestamp(time.mktime(GPSU)), gpsdata.speed)
            points.append(p)
            stats['ok'] += 1

        elif d.fourCC == 'SYST':
            data = [ float(x) / float(y) for x,y in zip( d.data._asdict().values() ,list(SCAL) ) ]
            if data[0] != 0 and data[1] != 0:
                SYST = fourCC.SYSTData._make(data)


        elif d.fourCC == 'GPRI':
            # KARMA GPRI info

            if d.data.lon == d.data.lat == d.data.alt == 0:
                print("Warning: Skipping empty point")
                stats['empty'] += 1
                continue

            if GPSFIX == 0:
                stats['badfix'] += 1
                if skip:
                    print("Warning: Skipping point due GPSFIX==0")
                    stats['badfixskip'] += 1
                    continue
                    
            data = [ float(x) / float(y) for x,y in zip( d.data._asdict().values() ,list(SCAL) ) ]
            gpsdata = fourCC.KARMAGPSData._make(data)
            
            if SYST.seconds != 0 and SYST.miliseconds != 0:
                p = gpshelper.GPSPoint(gpsdata.lat, gpsdata.lon, gpsdata.alt, datetime.fromtimestamp(SYST.miliseconds), gpsdata.speed)
                points.append(p)
                stats['ok'] += 1
                        

 

    print("-- stats -----------------")
    total_points =0
    for i in stats.keys():
        total_points += stats[i]
    print("- Ok:              %5d" % stats['ok'])
    print("- GPSFIX=0 (bad):  %5d (skipped: %d)" % (stats['badfix'], stats['badfixskip']))
    print("- Empty (No data): %5d" % stats['empty'])
    print("Total points:      %5d" % total_points)
    print("--------------------------")
    return(points)


def Build360Points(data, skip=False):
    """
    Data comes UNSCALED so we have to do: Data / Scale.
    Do a finite state machine to process the labels.
    GET
     - SCAL     Scale value
    """

    SCAL = fourCC.XYZData(1.0, 1.0, 1.0)
    DVID = None
    TSMP = None
    GPSU = None
    VPTS = None
    VPTS_init = None
    CTS = 0
    SYST = fourCC.SYSTData(0, 0)

    DATAS = ['CORI', 'IORI', 'GRAV']
    samples = []
    streams = { 'streams': {
        'datas': DATAS,
        'samples': samples
    }}

    stats = { 
        'ok': 0,
        'badfix': 0,
        'badfixskip': 0,
        'empty' : 0
    }

    GPSFIX = 0 # no lock.
    for d in data:
        if d.fourCC == 'SCAL':
            SCAL = d.data
        elif d.fourCC == 'TSMP':
            TSMP = d.data
        elif d.fourCC == 'VPTS':
            if VPTS == None:
                VPTS_init = d.data
            VPTS = d.data
            CTS = int((VPTS - VPTS_init) / 1000)
        elif d.fourCC in DATAS:
            sample = { 'CTS': CTS, 'VPTS': VPTS, 'SCAL': SCAL } if len(samples) == 0 else samples[-1]
            if sample['CTS'] < CTS:
                sample = { 'CTS': CTS, 'VPTS': VPTS, 'SCAL': SCAL }

            sample[d.fourCC] = dict(zip(['x', 'y', 'z', 'w'], d.data))
            
            if len(samples) == 0 or samples[-1]['CTS'] < CTS:
                samples.append(sample)

    return streams

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count")
    parser.add_argument("-b", "--binary", help="read data from bin file", action="store_true")
    parser.add_argument("-s", "--skip", help="Skip bad points (GPSFIX=0)", action="store_true", default=False)
    parser.add_argument("file", help="Video file or binary metadata dump")
    args = parser.parse_args()

    return args        

if __name__ == "__main__":

    args = parseArgs()
    config = config.setup_environment(args)
    parser = gpmf.Parser(config)

    if not args.binary:
        data = parser.readFromMP4()
    else:
        data = parser.readFromBinary()

    CASN = parser.readCameraSerial()

    streams = Build360Points(data, skip=args.skip)
    streams['camera_id'] = CASN
    streams['source_id'] = config.outputfile
    streams['date'] = parser.date

    if len(streams) == 0:
        print("Can't create file. No camera info in %s. Exitting" % config.file)
        sys.exit(0)

    fd = open("%s.json" % config.outputfile , "w+")
    fd.write(json.dumps(streams))
    fd.close()
