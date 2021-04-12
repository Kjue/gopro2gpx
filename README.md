# About gopro2json

Python script that parses the gpmd stream for GOPRO data track embedded in MP4-files and extract the interesting data into a JSON document.

Gopro cameras write out a lot of sensor information into the MP4-videos produced by the cameras. Gopro's [Quik](https://es.shop.gopro.com/softwareandapp/quik-%7C-desktop/Quik-Desktop.html) (old now)
allows you to process the metadata stored along the videos, and show it as an overlay. Intent here is to extract the data from the `MP4` file. The data is stored in a format called **GPMF**, you can get all the info in this repo [https://github.com/gopro/gpmf-parser](https://github.com/gopro/gpmf-parser).
Also, there are some implementations in **go**. Check this repo [https://github.com/stilldavid/gopro-utils/](https://github.com/stilldavid/gopro-utils/).

This fork intends to dig out the data embedded in **GoPro MAX video files** (extension .360) and especially the more esoteric parts. My main concern is to access the data and extract it to a JSON document.

-- Mikael Lavi

# Versions

## 0.2.2, 0.2.1

- Fix FPS calculation to be based on observed sampling interval.
- Issues with array handling fixed.

## 0.2.0

- Preliminary support for arrayd data from dataframes. Able to pick out the first on the line of the arrayed datas. WIP for handling them all.
- Extract highlights from the video files.

## 0.1.0

- First working version in my use case. This one will handle individual outputs from dataframes and not arrays of data. Dataframe may contain 200Hz ACCL data and this cannot handle it.

# Development with local deployment

In order to try out this library and to install it in local pip you may use this command. It makes it easier to test out the integration with other code.

```bash
python setup.py develop
```

And in order to install this repository to your Python app you may use the github repository to directly install the dependency by directly installing with pip or adding this reference to your `requirements.txt` for installation as dependency.

```
git+https://github.com/Kjue/gopro2json.git#egg=gopro2json
```

# Dependencies

- [Python3](https://www.python.org/download/releases/3.0/)
- [FFmpeg and FFprobe binaries](https://www.ffmpeg.org/download.html)
- Valid MP4 with GPS data inside. Record something with your cam.

# Installation

1. Clone the repo [gopro2json](https://github.com/kjue/gopro2json.git) in your machine, extract it.
2. Ensure you have **python3**, **FFmpeg** and **FFprobe** installed in your system.

_Optional:_ Edit `config.py` and modify the following lines to point to your binaries:

```python
     if platform.system().lower() == 'windows':
        config = Config('C:\\Software\\ffmpeg\\bin\\ffmpeg.exe', 'C:\\Software\\ffmpeg\\bin\\ffprobe.exe')
    else:
        config = Config('/usr/local/bin/ffmpeg', '/usr/local/bin/ffprobe')
```

3.  Run it to output a JSON-file containing the GYRO, CORI, and IORI vector streams for the video.

```shell
   % python gopro2json.py samples/hero6.mp4
```

# Arguments and options WIP

```
% python gopro2gpx.py  --help
usage: gopro2gpx.py [-h] [-v] [-b] [-s] file outputfile

positional arguments:
  file           Video file or binary metadata dump
  outputfile     output file. builds KML and GPX

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  increase output verbosity
  -b, --binary   read data from bin file
  -s, --skip     Skip bad points (GPSFIX=0)
```

- `file`: Gopro MP4 file or binary file with the gpmd dump.
- `outputfile`: Dump the GPS info into `outputfile.kml` and `outputfile.gpx`. Don't use extension.
- `-v`, `-vv`, `-vvv`: Verbose mode. First show some info, second dumps the `gpmd` track info a file called `outputfile.bin` and third (`-vvv`) shows the labels.
- `-b`: read the data from a binary dump fo the gpmd track istead of the MP4 video. Useful for testing, so I don't need to move big MP4 files.
- `-s`: skip "bad" GPS points. When `GPSFIX=0` (no GPS satellite signal received) GPS data is unacurrate. Ignore these points.

# Technnical info

To get the **gpmd** data, we need to explore the MP4 container, and extract the stream marked as _gpmd_. The script does it
automatically, but here is the output from `ffprobe`:

```
    % ffprobe GH010039.MP4

    The channel marked as gpmd (Stream #0:3(eng): Data: none (gpmd / 0x646D7067), 29 kb/s (default))
    In this case, the stream #0:3 is the required one (get the 3)

    Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'GH010039.MP4':
    Metadata:
        major_brand     : mp41
        minor_version   : 538120216
        compatible_brands: mp41
        creation_time   : 2019-02-10 10:59:19
    Duration: 00:00:21.80, start: 0.000000, bitrate: 60420 kb/s
        Stream #0:0(eng): Video: h264 (High) (avc1 / 0x31637661), yuvj420p(pc, bt709), 2704x1520 [SAR 1:1 DAR 169:95],
        60173 kb/s, 50 fps, 50 tbr, 90k tbn, 100 tbc (default)
        Metadata:
        creation_time   : 2019-02-10 10:59:19
        handler_name    : GoPro AVC
        encoder         : GoPro AVC encoder
        timecode        : 10:59:19:31
        Stream #0:1(eng): Audio: aac (LC) (mp4a / 0x6134706D), 48000 Hz, stereo, fltp, 189 kb/s (default)
        Metadata:
        creation_time   : 2019-02-10 10:59:19
        handler_name    : GoPro AAC
        timecode        : 10:59:19:31
        Stream #0:2(eng): Data: none (tmcd / 0x64636D74), 0 kb/s (default)
        Metadata:
        creation_time   : 2019-02-10 10:59:19
        handler_name    : GoPro TCD
        timecode        : 10:59:19:31
        Stream #0:3(eng): Data: none (gpmd / 0x646D7067), 29 kb/s (default)
        Metadata:
        creation_time   : 2019-02-10 10:59:19
        handler_name    : GoPro MET
        Stream #0:4(eng): Data: none (fdsc / 0x63736466), 12 kb/s (default)
        Metadata:
        creation_time   : 2019-02-10 10:59:19
        handler_name    : GoPro SOS
```

We need the stream called in this clase, `#0:3(eng)` that is, the `0:3` stream:

```
        [...]
        Stream #0:3(eng): Data: none (gpmd / 0x646D7067), 29 kb/s (default)
        Metadata:
        creation_time   : 2019-02-10 10:59:19
        handler_name    : GoPro MET
        [...]
```

# Extracting the binary GPS data from MP4

With this data, we can create a **binary file with the gpmd data inside**. The following command
copy the stream `0:3` from the file `GH010039.MP4` as raw, and stores it in `GH010039.bin`

```sh
%ffmpeg -y -i GH010039.MP4 -codec copy -map 0:3 -f rawvideo GH010039.bin
```

The binary looks like:

```
00000000: 44 45 56 43 00 01 14 A4 44 56 49 44 4C 04 00 01    DEVC...$DVIDL...
00000010: 00 00 00 01 44 56 4E 4D 63 01 00 0B 48 65 72 6F    ....DVNMc...Hero
00000020: 37 20 42 6C 61 63 6B 00 53 54 52 4D 00 01 05 AC    7.Black.STRM...,
00000030: 54 53 4D 50 4C 04 00 01 00 00 00 DB 53 54 4E 4D    TSMPL......[STNM
00000040: 63 01 00 0E 41 63 63 65 6C 65 72 6F 6D 65 74 65    c...Acceleromete
00000050: 72 00 00 00 53 49 55 4E 63 04 00 01 6D 2F 73 B2    r...SIUNc...m/s2
00000060: 53 43 41 4C 73 02 00 01 01 A2 00 00 4D 54 52 58    SCALs...."..MTRX
00000070: 66 24 00 01 00 00 00 00 00 00 00 00 3F 80 00 00    f$..........?...
00000080: 00 00 00 00 BF 80 00 00 00 00 00 00 3F 80 00 00    ....?.......?...
00000090: 00 00 00 00 00 00 00 00 4F 52 49 4E 63 01 00 03    ........ORINc...
000000a0: 59 78 5A 00 4F 52 49 4F 63 01 00 03 5A 58 59 00    YxZ.ORIOc...ZXY.
000000b0: 41 43 43 4C 73 06 00 DB FD 35 FF 2D 0D C7 FD 39    ACCLs..[}5.-.G}9
000000c0: FF 19 0D 87 FC CD FE F9 0D 4B FC 05 FE 45 0C AF    ....|M~y.K|.~E./
000000d0: FB B5 FD ED 0C 8F FB 65 FD E1 0C 6B FB 11 FE 6D    {5}m..{e}a.k{.~m
000000e0: 0C 47 FA E5 FE ED 0C 53 FA C5 FF 89 0C 87 FA C1    .Gze~m.SzE....zA
000000f0: FF F9 0C B3 FA AD 00 9F 0D 33 FA A9 00 B3 0D 6F    .y.3z-...3z).3.o
00000100: FA 95 00 B7 0D BB FA 65 00 C7 0E 3B FA 45 00 D7    z..7.;ze.G.;zE.W
00000110: 0E 73 FA 49 00 EF 0E A3 FA 25 00 E7 0E FB F9 FD    .szI.o.#z%.g.{y}
00000120: 00 E3 0E FF F9 E9 00 F3 0E FF F9 E9 00 E3 0E F3    .c..yi.s..yi.c.s
[...]
```

# Testing

Sample videos are downloaded from [here](https://github.com/gopro/gpmf-parser/tree/master/samples). I will try to put an original Gopro7 file
later. The gps data is extracted from the .MP4 file. The gpx, kml and bin files are stored in the repo. Karma introduces a new way of read GPS
information and time, based on `SYST` and `GPRI` labels. I did my best trying to parse it. Seems accurate. If you have some long files to do,
please extract the raw data and send me them (see [extracting data](#extracting-the-binary-gps-data-from-mp4)).

- fusion ![Fusion](doc/fusion.png 'Fusion')
- hero5 ![Fusion](doc/hero5.png 'Fusion')
- hero6 (all the points) ![Fusion](doc/hero6_noskip.png 'Fusion')
- hero6 (only `GPSFIX!=0`) ![Fusion](doc/hero6_skip.png 'Fusion')
- karma ![Fusion](doc/karma.png 'Fusion')
- Gopro7 ![Gopro7](doc/gopro7.png 'Gopro7')

# Status and future work

Currently, `gopro2gpx` generates _hard-formatted_ `kml`, and a useful `gpx` file. But:

- Not all tags are parsed. see `fourCC.skip_labels` and `fourCC.labels` for more info.
- The are a little error detecting code.
- Karma drone GPS info has been infered from debug. Maybe the `SYST` label is parsed wrong.
- `UNIT` labels are parsed hardcoded.
- Need `ffmpeg` and `ffprobe` to extract the data.
