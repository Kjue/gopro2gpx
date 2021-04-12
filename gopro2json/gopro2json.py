#!/usr/bin/env python
#
# 05/06/2020
# Mikael Lavi <mikael.lavi@gmail.com>
# https://github.com/kjue/gopro2json.git
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
from collections import Counter

from . import config
from . import gpmf
from . import fourCC
import time
import sys

import json

  
def most_frequent(List):
    occurence_count = Counter(List)
    return occurence_count.most_common(1)[0][0]

def Build360Points(data, skip=False):
    """
    Data comes UNSCALED so we have to do: Data / Scale.
    Do a finite state machine to process the labels.
    Data does contain the scale.
    GET
     - SCAL     Scale value
    """

    # Stream name
    STNM = ''
    
    # Total Samples delivered
    TSMP = ''
    
    SCAL = fourCC.XYZData(1.0, 1.0, 1.0)
    VPTS = None
    VPTS_init = None
    CTS = 0

    DATAS = ['CORI', 'ACCL', 'GRAV', 'MAGN', 'GYRO']
    samples = []
    streams = {'streams': {
        'datas': DATAS,
        'samples': samples
    }}

    for d in data:
        if d.fourCC == 'STNM':
            STNM = d.data
        elif d.fourCC == 'TSMP':
            TSMP = d.data
        elif d.fourCC == 'SCAL':
            SCAL = d.data
        elif d.fourCC == 'VPTS':
            if VPTS == None:
                VPTS_init = d.data
            VPTS = d.data
            CTS = int((VPTS - VPTS_init) / 1001)
        # Disabled DISP data for now.
        # elif d.fourCC == 'DISP':
        #     sample[d.fourCC] = d.data
        elif d.fourCC in DATAS:
            sample = { 'CTS': CTS, 'VPTS': VPTS, 'SCAL': SCAL } if len(samples) == 0 else samples[-1]
            if sample['CTS'] < CTS:
                sample = { 'CTS': CTS, 'VPTS': VPTS, 'SCAL': SCAL }

            if not d.data:
                continue

            sample[d.fourCC] = d.data._asdict()
            # listdict = list(map(lambda x: x._asdict(), d.data))

            # Correct the polarity of the data to right handed coordsys.
            if (type(d.data) == fourCC.WXYZData):
                sample[d.fourCC]['z'] = -sample[d.fourCC]['z']

            if (type(d.data) == fourCC.XYZData):
                sample[d.fourCC]['y'] = -sample[d.fourCC]['y']
                sample[d.fourCC]['z'] = -sample[d.fourCC]['z']

            if len(samples) == 0 or samples[-1]['CTS'] < CTS:
                samples.append(sample)

    mapped = list(map(lambda a: \
        (a[1]['VPTS'] or 0) - (a[0]['VPTS'] or 0), \
        zip(samples, samples[1:])))
    streams['streams']['FPS'] = 1 / (most_frequent(mapped) / 1000 / 1000)
    return streams

def Parse360ToJson(files=[], output=None, binary=False, verbose=None):
    datas = []
    anchors = []
    for f in files:
        cfg = config.setup_environment(f, outputfile=output)
        parser = gpmf.Parser(cfg)
        datas.extend(parser.readFromMP4())
        anchors.extend(parser.extractHighlightTimecodes())
        CASN = parser.readCameraSerial()

    streams = Build360Points(datas)
    streams['camera'] = CASN
    streams['source'] = cfg.outputfile
    streams['date'] = parser.date
    streams['anchors'] = anchors

    if len(streams) == 0:
        print("Can't create file. No camera info in %s. Exitting" % cfg.file)
        sys.exit(0)

    fd = open("%s" % cfg.outputfile, "w+")
    fd.write(json.dumps(streams))
    fd.close()

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
    config = config.setup_environment(args.file, args.binary, args.verbose)
    parser = gpmf.Parser(config)

    if not args.binary:
        data = parser.readFromMP4()
    else:
        data = parser.readFromBinary()

    CASN = parser.readCameraSerial()

    streams = Build360Points(data, skip=args.skip)

    if len(streams) == 0:
        print("Can't create file. No camera info in %s. Exitting" % config.file)
        sys.exit(0)

    streams['camera'] = CASN
    streams['source'] = config.outputfile
    streams['date'] = parser.date

    #
    # Write the results
    #
    fd = open("%s.json" % config.outputfile, "w+")
    fd.write(json.dumps(streams))
    fd.close()
