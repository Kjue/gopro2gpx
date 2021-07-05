#
# 17/02/2019 
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#

import subprocess
import re
from datetime import datetime
class FFMpegTools:

    def __init__(self, config):
        self.config = config

    def runCmd(self, cmd, args):
        result = subprocess.run([ cmd ] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stderr.decode('utf-8')
        return output

    def runCmdRaw(self, cmd, args):
        result = subprocess.run([ cmd ] + args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        output = result.stdout
        return output

    def getMetadataTrack(self, fname):
        """
        % ffprobe GH010039.MP4 2>&1

        The channel marked as gpmd (Stream #0:3(eng): Data: none (gpmd / 0x646D7067), 29 kb/s (default))
        In this case, the stream #0:3 is the required one (get the 3)

        Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'GH010039.MP4':
            Stream #0:1(eng): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, stereo, fltp, 189 kb/s (default)
            Stream #0:2(eng): Data: none (tmcd / 0x64636D74), 0 kb/s (default)
            Stream #0:3(eng): Data: none (gpmd / 0x646D7067), 29 kb/s (default)
            Stream #0:4(eng): Data: none (fdsc / 0x63736466), 12 kb/s (default)
        """      
        output = self.runCmd(self.config.ffprobe_cmd, [fname])
        # Stream #0:3(eng): Data: bin_data (gpmd / 0x646D7067), 29 kb/s (default)
        # Stream #0:2(eng): Data: none (gpmd / 0x646D7067), 29 kb/s (default)
        reg = re.compile('Stream #\d:(\d)\(.+\): Data: \w+ \(gpmd', flags=re.I|re.M)
        m = reg.search(output)
        
        if not m:
            return(None)
        return(int(m.group(1)), m.group(0))

    def getMetadata(self, track, fname):

        output_file = "-"
        args = [ '-y', '-i', fname, '-codec', 'copy', '-map', '0:%d' % track, '-f', 'rawvideo', output_file ] 
        output = self.runCmdRaw(self.config.ffmpeg_cmd, args)
        return(output)

    def getDate(self, fname):
        """
        $ ffprobe -v error -show_format -show_streams GS010064.360 | grep -i TAG:creation_time=
        TAG:creation_time=2020-07-10T16:28:24.000000Z
        TAG:creation_time=2020-07-10T16:28:24.000000Z

        $ ffprobe GS010064.360
        Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'GS010064.360':
        Metadata:
            major_brand     : mp41
            minor_version   : 538120216
            compatible_brands: mp41
            creation_time   : 2020-07-10T16:28:24.000000Z
            firmware        : H19.03.01.50.00
        Duration: 00:00:06.17, start: 0.000000, bitrate: 60610 kb/s
            Stream #0:0(eng): Video: hevc (Main) (hvc1 / 0x31637668), yuvj420p(pc, bt709), 4096x1344 [SAR 1:1 DAR 64:21], 30126 kb/s, 29.97 fps, 29

        The datetime object is ready to consume as it is just read from the file.
        Every stream has this same information, so just one is good enough.
        """
        output = self.runCmd(self.config.ffprobe_cmd, [fname])
        # Stream #0:3(eng): Data: bin_data (gpmd / 0x646D7067), 29 kb/s (default)
        # Stream #0:2(eng): Data: none (gpmd / 0x646D7067), 29 kb/s (default)
        # reg = re.compile('Stream #\d:(\d)\(.+\): Data: \w+ \(gpmd', flags=re.I|re.M)
        # m = reg.search(output)

        dates = re.findall(r'creation_time   : (.+Z)', output)
        date = (dates[0] if dates else '')
        if self.config.verbose == 2:
            print("GoPro recording date: %s" % date)
        return date

    def getDuration(self, fname):
        """
        In case you run ffprobe on a video, it will print out duration and chapters data for you automatically:

        $ ffprobe -sexagesimal <fname> 
        Duration: 00:02:16.04, start: 0.000000, bitrate: 60270 kb/s
          Chapter #0:0: start 6.240000, end 34.200000
          Chapter #0:1: start 34.200000, end 55.400000
          Chapter #0:2: start 55.400000, end 70.120000
          Chapter #0:3: start 70.120000, end 97.720000
          Chapter #0:4: start 97.720000, end 124.200000
          Chapter #0:5: start 124.200000, end 136.040000
          Stream #0:0(eng): Video: hevc (Main) (hvc1 / 0x31637668), yuvj420p(pc, bt709), 4096x1344 [SAR 1:1 DAR 64:21], 29996 kb/s, 25 fps, 25 tbr, 90k tbn, 25

        Args:
            fname (String): Specified filename to target
        """
        args = '-v error -select_streams v:0 -show_entries stream=duration -sexagesimal -of default=noprint_wrappers=1:nokey=1 ' + fname
        args = args.split(' ')
        output = self.runCmdRaw(self.config.ffprobe_cmd, args).decode('utf-8').strip()
        duration = datetime.strptime(output, '%H:%M:%S.%f') - datetime(1900, 1, 1)

        if self.config.verbose == 2:
            print("GoPro recording duration: %s" % duration)
        return duration.total_seconds()

    def getFps(self, fname):
        """Get actual fps of specified video file."""
        args = '-v 0 -of csv=p=0 -select_streams v:0 -show_entries stream=r_frame_rate ' + fname
        args = args.split(' ')
        output = self.runCmdRaw(self.config.ffprobe_cmd, args).decode('utf-8').strip()
        fps = eval(output)

        if self.config.verbose == 2:
            print("GoPro recording actual fps: %s" % fps)
        return fps

    def getChapters(self, fname):
        """
        In case you run ffprobe on a video, it will print out duration and chapters data for you automatically:

        $ ffprobe -sexagesimal <fname> 
        Duration: 00:02:16.04, start: 0.000000, bitrate: 60270 kb/s
          Chapter #0:0: start 6.240000, end 34.200000
          Chapter #0:1: start 34.200000, end 55.400000
          Chapter #0:2: start 55.400000, end 70.120000
          Chapter #0:3: start 70.120000, end 97.720000
          Chapter #0:4: start 97.720000, end 124.200000
          Chapter #0:5: start 124.200000, end 136.040000
          Stream #0:0(eng): Video: hevc (Main) (hvc1 / 0x31637668), yuvj420p(pc, bt709), 4096x1344 [SAR 1:1 DAR 64:21], 29996 kb/s, 25 fps, 25 tbr, 90k tbn, 25

        Args:
            fname (String): Specified filename to target
        """
        output = self.runCmd(self.config.ffprobe_cmd, [fname])

        chapters = re.findall(r'.*start (\d+\.\d+), end (\d+\.\d+)', output)
        chapters[:] = [{ 'start': float(x[0]), 'end': float(x[1]) } for x in chapters]
        if self.config.verbose == 2:
            print("GoPro recording date: %s" % chapters)
        return chapters

