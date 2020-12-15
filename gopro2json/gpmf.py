'''

17/02/2019 
Juan M. Casillas <juanm.casillas@gmail.com>
https://github.com/juanmcasillas/gopro2gpx.git

Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)

based on the info from:
 - https://github.com/gopro/gpmf-parser
 - https://docs.python.org/3/library/struct.html
 - https://github.com/stilldavid/gopro-utils/blob/master/telemetry/reader.go

Modifications and code review, Mikael Lavi.

Original code borrowed under MIT license from:
GoPro Highlight Parser:  https://github.com/icegoogles/GoPro-Highlight-Parser

The code for extracting the mp4 boxes/atoms is from 'Human Analog' (https://www.kaggle.com/humananalog): 
https://www.kaggle.com/humananalog/examine-mp4-files-with-python-only

'''

import os
import array
import sys
import struct
import re

from . ffmpegtools import FFMpegTools
from . klvdata import KLVData



class Parser:
    def __init__(self, config):
        self.config = config
        self.ffmtools = FFMpegTools(self.config)

        # map some handy shortcuts
        self.verbose = config.verbose
        self.file = config.file
        self.outputfile = config.outputfile

        self.date = self.ffmtools.getDate(self.file)

    def find_boxes(self, f, start_offset=0, end_offset=float("inf")):
        """
        Returns a dictionary of all the data boxes and their absolute starting
        and ending offsets inside the mp4 file.

        Specify a start_offset and end_offset to read sub-boxes.
        """
        s = struct.Struct("> I 4s")
        boxes = {}
        offset = start_offset
        f.seek(offset, 0)
        while offset < end_offset:
            data = f.read(8)               # read box header
            if data == b"": break          # EOF
            length, text = s.unpack(data)
            f.seek(length - 8, 1)          # skip to next box
            boxes[text] = (offset, offset + length)
            offset += length or 8
        return boxes

    def parse_highlights(self, f, start_offset=0, end_offset=float('inf')):

        inHighlights = False
        inHLMT = False

        listOfHighlights = []

        offset = start_offset
        f.seek(offset, 0)

        while offset < end_offset:
            data = f.read(4)               # read box header
            if data == b'': break          # EOF

            if data == b'High' and inHighlights == False:
                data = f.read(4)
                if data == b'ligh':
                    inHighlights = True  # set flag, that highlights were reached

            if data == b'HLMT' and inHighlights == True and inHLMT == False:
                inHLMT = True  # set flag that HLMT was reached

            if data == b'MANL' and inHighlights == True and inHLMT == True:

                currPos = f.tell()  # remember current pointer/position
                f.seek(currPos - 20)  # go back to highlight timestamp

                data = f.read(4)  # readout highlight
                timestamp = int.from_bytes(data, 'big')  #convert to integer

                if timestamp != 0:
                    listOfHighlights.append(timestamp)  # append to highlightlist

                f.seek(currPos)  # go forward again (to the saved position)

        return list(map(lambda x: x / 1000, listOfHighlights))


    def extractHighlightTimecodes(self):

        if not os.path.exists(self.file):
            raise FileNotFoundError("Can't open %s" % self.file)

        with open(self.file, "rb") as f:
            boxes = self.find_boxes(f)

            if boxes[b"ftyp"][0] != 0:
                raise Exception("File is not a mp4-video-file!")

            # mdat_boxes = self.find_boxes(f, boxes[b"mdat"][0] + 8, boxes[b"mdat"][1])
            moov_boxes = self.find_boxes(f, boxes[b"moov"][0] + 8, boxes[b"moov"][1])
        
            udta_boxes = self.find_boxes(f, moov_boxes[b"udta"][0] + 8, moov_boxes[b"udta"][1])
            # mvhd_boxes = self.find_boxes(f, moov_boxes[b"mvhd"][0] + 8, moov_boxes[b"mvhd"][1])
            # iods_boxes = self.find_boxes(f, moov_boxes[b"iods"][0] + 8, moov_boxes[b"iods"][1])
            # trak_boxes = self.find_boxes(f, moov_boxes[b"trak"][0] + 8, moov_boxes[b"trak"][1])

            # mdia_boxes = self.find_boxes(f, trak_boxes[b"mdia"][0] + 8, trak_boxes[b"mdia"][1])

            ### get GPMF Box
            # highlights = parse_highlights(f, udta_boxes[b'GPMF'][0] + 8, udta_boxes[b'GPMF'][1])

            # f.seek(udta_boxes[b'GPMF'][0] + 8, 0)
            # out = f.read(udta_boxes[b'GPMF'][1])
            # return out

            highlights = self.parse_highlights(f, udta_boxes[b'GPMF'][0] + 8, udta_boxes[b'GPMF'][1])
            return highlights

            # print("")
            # print("Filename:", filename)
            # print("Found", len(highlights), "Highlight(s)!")
            # print('Here are all Highlights: ', highlights)

            # return highlights


    def readFromMP4(self):
        """read data the metadata track from video. Requires FFMPEG wrapper.
           -vv creates a dump file with the  binary data called dump_track.bin
        """
        
        if not os.path.exists(self.file):
            raise FileNotFoundError("Can't open %s" % self.file)

        track_number, lineinfo = self.ffmtools.getMetadataTrack(self.file)
        if not track_number:
            raise Exception("File %s doesn't have any metadata" % self.file)
        
        if self.verbose:
            print("Working on file %s track %s (%s)" % (self.file, track_number, lineinfo))
        metadata_raw = self.ffmtools.getMetadata(track_number, self.file)

        if self.verbose == 2:
            print("Creating output file for binary data (fromMP4): %s" % self.outputfile)
            f = open("%s.bin" % self.outputfile, "wb")
            f.write(metadata_raw)
            f.close()

        
        # process the data here
        metadata = []
        metadata.extend(self.parseStream(metadata_raw))

        # We could be processing a lot more data from the other containers too. Right now this is unstable.
        # metadata_raw_too = self.examine_mp4(self.file)
        # metadata.extend(self.parseStream(metadata_raw_too))

        return(metadata)

    def readFromBinary(self):
        """read data from binary file, instead extract the metadata track from video. Useful for quick development
           -vv creates a dump file with the  binary data called dump_binary.bin
        """
        if not os.path.exists(self.file):
            raise FileNotFoundError("Can't open %s" % self.file)

        if self.verbose:
            print("Reading binary file %s" % (self.file))
        
        fd = open(self.file, 'rb')
        data = fd.read()
        fd.close()

        if self.verbose == 2:
            print("Creating output file for binary data (from binary): %s" % self.outputfile)
            f = open("%s.bin" % self.outputfile, "wb")
            f.write(data)
            f.close() 

        # process the data here
        metadata = self.parseStream(data)   
        return metadata

    def parseStream(self, data_raw):
        """
        main code that reads the points
        """
        data = array.array('b')
        data.fromstring(data_raw)

        offset = 0
        klvlist = []

        while offset < len(data):

            try:
                klv = KLVData(data,offset)
                if not klv.skip():
                    klvlist.append(klv)
                    if self.verbose == 3:
                        print(klv)
                offset += 8
                if klv.type != 0:
                    offset += klv.padded_length
                    #print(">offset:%d length:%d padded:%d" % (offset, length, padded_length))
            except Exception as error:
                print(error)
                offset += 8
                offset += klv.padded_length
            
        return(klvlist)
    
    def readCameraSerial(self):
        fd = open(self.file, 'rb')
        id_data = fd.read(200)
        fd.close()

        ids = re.findall(r'(\d+).GoPro', id_data.decode('utf-8', errors='replace'))
        CASN = (ids[0] if ids else None)
        if self.verbose == 2:
            print("GoPro SN: %s" % CASN)
        return CASN

            