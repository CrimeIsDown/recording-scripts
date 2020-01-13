#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import time
import urllib.request
from glob import glob
from datetime import datetime

onWindows = os.name == 'nt'

if onWindows:
    recordingPath = 'C:\\Users\\Eric\\Documents\\ChicagoScanner\\recordings'
else:
    recordingPath = '/mnt/hgfs/R/recordings'
    #recordingPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'recordings')

def start_ffmpeg(channel, record=True, stream=False, broadcastify=False):
    started = False

    ffmpeg_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', 'ffmpeg') if os.name == 'nt' else '/usr/bin/ffmpeg'
    inputopts = [
        '-f', 'dshow' if onWindows else 'pulse',
        '-i', ('audio=' + channel['audio']) if onWindows else (channel['slug'] + '.monitor')
    ]
    if not onWindows:
        inputopts = inputopts + ['-af', 'bandpass=f=1650:width_type=h:w=2700']
    recordingopts = []
    streamopts = []
    environment = os.environ.copy()
    #environment['FFREPORT'] = 'file=%p_%t_'+channel['slug']+'.log:level=16'

    if record:
        recordingopts = [
            # '-c:a', 'aac',
            # '-b:a', '32k',
            # '-ac', '1',
            # '-ar', '22050',
            '-c:a', 'libopus',
            '-application', 'voip',
            '-b:a', '24k',
            '-ac', '1',
            '-ar', '16000',
            '-f', 'segment',
            '-segment_time', '3600',
            '-segment_atclocktime', '1',
            '-strftime', '1',
            '-reset_timestamps', '1',
            os.path.join(recordingPath, '%Y', '%m', '%d', '%H', channel['slug'] + '_%Y%m%d_%H%M%S.ogg'),
        ]
        current_recording_path = datetime.now().replace(microsecond=0, second=0, minute=0).strftime(recordingopts[-1].replace('%H%M%S', '*'))
        if not any([path for path in glob(current_recording_path) if os.path.isfile(path)]):
            if onWindows:
                # args = ['taskkill', '/F', '/FI', 'WindowTitle eq Record: ' + channel['name']]
                # subprocess.run(args, shell=True)
                args = ['start', 'Record: ' + channel['name'], ffmpeg_path] + inputopts + recordingopts
                subprocess.run(args, shell=True, env=environment)
            else:
                args = ['mate-terminal', '-t', '\'Record: %s\'' % channel['name'], '-e', '\'sh -c "' + ' '.join([ffmpeg_path] + inputopts + recordingopts) + '; sleep 15"\'']
                subprocess.run(' '.join(args), shell=True, env=environment)
            started = True
        else:
            print("Not starting recorder for %s as we already have a file at %s" % (channel['name'], current_recording_path))

    if stream:
        # ffmpeg will launch and error out for any streams already running
        streamopts = [
            '-c:a', 'aac',
            '-b:a', '16k',
            '-ac', '1',
            '-ar', '22050',
            '-f', 'flv',
            'rtmp://audio.crimeisdown.com:1935/live/' + channel['slug']
        ]
        # streamopts = [
        #     '-c:a', 'libopus',
        #     '-application', 'voip',
        #     '-b:a', '24k',
        #     '-ac', '1',
        #     '-ar', '16000',
        #     '-content_type', 'application/ogg',
        #     '-ice_name', channel['name'],
        #     '-ice_description', channel['description'],
        #     'icecast://source:password@audio.crimeisdown.com:8001/' + channel['slug'] + '.ogg'
        # ]
        try:
            urllib.request.urlopen('https://audio.crimeisdown.com/streaming/dash/' + channel['slug'] + '/')
            urllib.request.urlopen('https://audio.crimeisdown.com/streaming/dash/' + channel['slug'] + '/init.m4a')
            with urllib.request.urlopen('https://audio.crimeisdown.com/streaming/stat') as response:
                if str(response.read()).find('<name>'+channel['slug']+'</name>') == -1:
                    raise Exception()
            print("Not starting stream for %s as it is already running" % channel['name'])
        except:
            if onWindows:
                args = ['taskkill', '/F', '/FI', 'WindowTitle eq Stream: ' + channel['name']]
                subprocess.run(args, shell=True)
                args = ['start', 'Stream: ' + channel['name'], ffmpeg_path] + inputopts + streamopts
                subprocess.run(args, shell=True, env=environment)
            else:
                args = ['mate-terminal', '-t', '\'Stream: %s\'' % channel['name'], '-e', '\'sh -c "' + ' '.join([ffmpeg_path] + inputopts + streamopts) + '; sleep 15"\'']
                subprocess.run(' '.join(args), shell=True, env=environment)
            started = True

    if broadcastify:
        if 'icecast_url' in channel:
            # Stream to Broadcastify
            streamopts = [
                '-c:a', 'mp3',
                '-b:a', '16k',
                '-ac', '1',
                '-ar', '22050',
                '-f', 'mp3',
                '-legacy_icecast', '1',
                '-content_type', 'audio/mpeg',
                '-ice_name', channel['name'],
                channel['icecast_url']
            ]
            if onWindows:
                args = ['start', 'Broadcastify: ' + channel['name'], ffmpeg_path] + inputopts + streamopts
                subprocess.run(args, shell=True, env=environment)
            else:
                args = ['mate-terminal', '-t', '\'Broadcastify: %s\'' % channel['name'], '-e', '\'sh -c "' + ' '.join([ffmpeg_path] + inputopts + streamopts) + '; sleep 15"\'']
                subprocess.run(' '.join(args), shell=True, env=environment)
            started = True

    # args = ['start', 'Record/Stream: ' + channel['name'], ffmpeg_path] + inputopts + recordingopts + streamopts
    # subprocess.run(args, shell=True)


if len(sys.argv) > 1:
    record = 'record' in sys.argv
    stream = 'stream' in sys.argv
    broadcastify = 'broadcastify' in sys.argv
    singlestream = 'only' in sys.argv
else:
    record = True
    stream = True
    broadcastify = False
    singlestream = False

with open('channels.json') as channels_file:
    channels = json.load(channels_file)
    for channel in channels:
        if not singlestream or any(channel['slug'] == arg for arg in sys.argv):
            if start_ffmpeg(channel, record=record, stream=stream, broadcastify=broadcastify):
                time.sleep(5)
