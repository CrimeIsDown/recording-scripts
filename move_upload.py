#!/usr/bin/env python3

import json
import os
import re
from time import sleep
from datetime import date, timedelta
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


def compress_recordings(day_path):
    for subdir, dirs, files in os.walk(os.path.join(recording_path, day_path)):
        pool = mp.Pool()
        partial_compress_file = partial(compress_file, subdir)
        pool.map(partial_compress_file, files)
        pool.close()
        pool.join()


def upload_recordings(day_path):
    rclone_args = [
        'rclone',
        'copy',
        os.path.join(recording_path, day_path),
        'google:crimeisdown-audio/'+day_path.replace(os.sep, '/'),
        '--transfers', '1',
        '--include', '*.aac.xz',
        '--bwlimit', '100k',
        '-v'
    ]
    subprocess.run(rclone_args, shell=True)


recording_path = 'R:\\recordings'
today_path = date.today().strftime('%Y'+os.sep+'%m'+os.sep+'%d')
yesterday_path = (date.today() - timedelta(1)).strftime('%Y'+os.sep+'%m'+os.sep+'%d')

move_recordings()
print('======= Compressing and uploading '+yesterday_path+' =======')
compress_recordings(yesterday_path)
upload_recordings(yesterday_path)
print('======= Compressing and uploading '+today_path+' =======')
compress_recordings(today_path)
upload_recordings(today_path)
print('======= Compressing and uploading complete =======')
sleep(10)
