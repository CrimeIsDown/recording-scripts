#!/usr/bin/env python3

import json
import os
import re
from time import sleep
from datetime import date, datetime, timedelta
import lzma
import subprocess
import multiprocessing.dummy as mp
from functools import partial


def move_recordings():
    with open('channels.json') as channels_file:
        channels = json.load(channels_file)
        for channel in channels:
            for root, dirs, files in os.walk(os.path.join(recording_path, channel['slug'])):
                for file in files:
                    match = re.match('^'+channel['slug']+'_([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})\.aac$', file)
                    if match:
                        newfolderpath = os.path.join(recording_path, match.group(1), match.group(2), match.group(3), match.group(4))
                        if not os.path.exists(newfolderpath):
                            os.makedirs(newfolderpath)
                        oldpath = os.path.join(recording_path, channel['slug'], file)
                        newpath = os.path.join(newfolderpath, file)
                        try:
                            os.rename(oldpath, newpath)
                            print(oldpath + ' moved to ' + newpath)
                        except OSError:
                            pass  # do nothing because this file is in use


def compress_file(subdir, file):
    match = re.match('^(zone|citywide)([0-9][0-9]?)_([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})\.aac$', file)
    if match:
        path = os.path.join(subdir, file)
        with lzma.open(path + '.xz', 'wb') as compressed:
            with open(path, 'rb') as original:
                compressed.write(original.read())
        if os.path.exists(path + '.xz'):
            os.remove(path)
            print('Compressed ' + path)
        else:
            print('Could not compress '+path)


def compress_recordings(path):
    for subdir, dirs, files in os.walk(path):
        pool = mp.Pool()
        partial_compress_file = partial(compress_file, subdir)
        pool.map(partial_compress_file, files)
        pool.close()
        pool.join()


def upload_recordings(path):
    rclone_args = [
        'rclone',
        'copy',
        path,
        'google:crimeisdown-audio/'+path.replace(recording_path + os.sep, '').replace(os.sep, '/'),
        '--transfers', '1',
        '--include', '*.aac.xz', '--include', '*.ogg',
        '--bwlimit', '100k',
        '-v'
    ]
    subprocess.run(rclone_args, shell=True)


recording_path = 'R:\\recordings'

now = datetime.now()
advance1hr = timedelta(hours=1)
maxdifference = 24

# first, ensure we have enough directories for coming recordings
currenthour = now + advance1hr
while currenthour < now + timedelta(hours=(maxdifference+1)):
    newfolder = os.path.join(recording_path, currenthour.strftime('%Y'+os.sep+'%m'+os.sep+'%d'+os.sep+'%H'))
    print('Making path %s' % newfolder)
    if not os.path.exists(newfolder):
        os.makedirs(newfolder)
    currenthour = currenthour + advance1hr

# once we have enough directories for new recordings, upload ones from the past 24hrs (usually we really only need to do 1hr)
currenthour = now - timedelta(hours=maxdifference)
while currenthour < datetime.now() - advance1hr:
    path = os.path.join(recording_path, currenthour.strftime('%Y'+os.sep+'%m'+os.sep+'%d'+os.sep+'%H'))
    print('======= Compressing and uploading %s =======' % path)
    compress_recordings(path)
    upload_recordings(path)
    currenthour = currenthour + advance1hr

print('======= Compressing and uploading complete =======')
sleep(10)
