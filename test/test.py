import os
import argparse
import gopro2json

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # parser.add_argument("-v", "--verbose", help="increase output verbosity", action="count")
    # parser.add_argument("-b", "--binary", help="read data from bin file", action="store_true")
    # parser.add_argument("-s", "--skip", help="Skip bad points (GPSFIX=0)", action="store_true", default=False)
    parser.add_argument("file", help="Video file or binary metadata dump")
    args = parser.parse_args()

    inFile = args.file
    outFile, ext = os.path.splitext(args.file)
    outFile = outFile + '.transform.json'

    try:
        gopro2json.Parse360ToJson([inFile], outFile)
    except Exception as error:
        print('We should be processing timelapse items only! {}'.format(error))

    # Graceful exit condition.
    exit(0)
