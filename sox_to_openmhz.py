#!/usr/bin/env python3

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import json
import logging
import os
import re
import requests
import subprocess
import sys

class NewTransmissionHandler(FileSystemEventHandler):
    """docstring for NewTransmissionHandler"""
    def __init__(self):
        super(NewTransmissionHandler, self).__init__()
        with open('channels.json') as channels_file:
            self.channels = json.load(channels_file)


    def on_modified(event):
        if not event.is_directory:
            print(event.src_path)


    def convert_call(src_path):
        converted = src_path + '.m4a'
        # command from trunk-recorder
        command = 'ffmpeg -y -i %s -c:a libfdk_aac -b:a 32k -filter:a "volume=5" -cutoff 18000 -hide_banner -loglevel error %s' % (src_path, converted)
        subprocess.run(command)


    def upload_call(converted_path, duration):
        url = 'https://api.openmhz.com'

        headers = {'User-Agent': 'TrunkRecorder1.0'}

        files = {'call': open(converted_path, 'rb')}

        start_time = duration
        stop_time = os.path.getmtime(converted_path)

        filename_no_ext = os.path.splitext(os.path.basename(converted_path))[0]

        channel = next((c for c in self.channels if c['slug'] in filename_no_ext), None)
        talkgroup_num = re.search('filter-code=([0-9]+)', channel['openmhz']).group(1)

        body = {
            'freq': '{:g}'.format(channel['freq']),
            'start_time': start_time,
            'stop_time': start_time,
            'talkgroup_num': int(talkgroup_num),
            'emergency': 0,
            'api_key': os.getenv('OPENMHZ_APIKEY'),
            'source_list': [],
            'freq_list': []
        }

        r = requests.post(url, files=files, data=body)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    handler = NewTransmissionHandler()
    observer = Observer()
    observer.schedule(handler, path, recursive=True)
    observer.start()
    try:
        while observer.isAlive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()