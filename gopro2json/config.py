#
# 17/02/2019 
# Juan M. Casillas <juanm.casillas@gmail.com>
# https://github.com/juanmcasillas/gopro2gpx.git
#
# Released under GNU GENERAL PUBLIC LICENSE v3. (Use at your own risk)
#

import os
import subprocess
import platform
import sys

class Config:
    def __init__(self, ffmpeg, ffprobe):
        self.ffmpeg_cmd = ffmpeg
        self.ffprobe_cmd = ffprobe

def setup_environment(filename="", outputfile=None, binary=False, verbose=False):
    """
    The output of platform.system() is as follows:
    Linux: Linux
    Mac: Darwin
    Windows: Windows
    """
    if platform.system().lower() == 'windows':
        # config = Config('C:\\Software\\ffmpeg\\bin\\ffmpeg.exe', 'C:\\Software\\ffmpeg\\bin\\ffprobe.exe')
        config = Config('ffmpeg.exe', 'ffprobe.exe')
    else:
        ffmpeg = subprocess.run(["which", "ffmpeg"], capture_output=True).stdout.decode('utf-8')
        ffprobe = subprocess.run(["which", "ffprobe"], capture_output=True).stdout.decode('utf-8')
        print('Configuring ffmpeg to: ', ffmpeg)
        print('Configuring ffprobe to: ', ffprobe)
        config = Config(ffmpeg, ffprobe)

    if (len(filename)):
        file_name, ext = os.path.splitext(filename)

        # configure arguments
        config.verbose = verbose
        config.file = filename
        if (outputfile != None):
            config.outputfile = outputfile
        else:
            config.outputfile = '{}.json'.format(file_name)

    return config

    