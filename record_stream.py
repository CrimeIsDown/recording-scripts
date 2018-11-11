#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import time

onWindows = os.name == 'nt'

if onWindows:
    recordingPath = 'R:\\recordings'
else:
    recordingPath = '/mnt/hgfs/R/recordings'
    #recordingPath = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'recordings')

def start_ffmpeg(channel, record=True, stream=False, broadcastify=False):
    ffmpeg_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', 'ffmpeg') if os.name == 'nt' else '/usr/bin/ffmpeg'
    inputopts = [
        '-f', 'dshow' if onWindows else 'pulse',
        '-i', ('audio=' + channel['audio']) if onWindows else (channel['slug'] + '.monitor')
    ]
    if not onWindows:
        inputopts = inputopts + ['-af', 'bandpass=f=1650:width_type=h:w=2700']
    recordingopts = []
    streamopts = []

    if record:
        recordingopts = [
            '-c:a', 'aac',
            '-b:a', '32k',
            '-ac', '1',
            '-ar', '22050',
            '-f', 'segment',
            '-segment_time', '3600',
            '-segment_atclocktime', '1',
            '-strftime', '1',
            os.path.join(recordingPath, channel['slug'], channel['slug'] + '_%Y%m%d_%H%M%S.aac'),
        ]
        if onWindows:
            args = ['start', 'Record: ' + channel['name'], ffmpeg_path] + inputopts + recordingopts
            subprocess.run(args, shell=True)
        else:
            args = ['mate-terminal', '-t', '\'Record: %s\'' % channel['name'], '-e', '\'sh -c "' + ' '.join([ffmpeg_path] + inputopts + recordingopts) + '; sleep 15"\'']
            subprocess.run(' '.join(args), shell=True)

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
        if onWindows:
            args = ['start', 'Stream: ' + channel['name'], ffmpeg_path] + inputopts + streamopts
            subprocess.run(args, shell=True)
        else:
            args = ['mate-terminal', '-t', '\'Stream: %s\'' % channel['name'], '-e', '\'sh -c "' + ' '.join([ffmpeg_path] + inputopts + streamopts) + '; sleep 15"\'']
            subprocess.run(' '.join(args), shell=True)

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
                subprocess.run(args, shell=True)
            else:
                args = ['mate-terminal', '-t', '\'Broadcastify: %s\'' % channel['name'], '-e', '\'sh -c "' + ' '.join([ffmpeg_path] + inputopts + streamopts) + '; sleep 15"\'']
                subprocess.run(' '.join(args), shell=True)

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
    broadcastify = True
    singlestream = False

with open('channels.json') as channels_file:
    channels = json.load(channels_file)
    for channel in channels:
        if not singlestream or any(channel['slug'] == arg for arg in sys.argv):
            start_ffmpeg(channel, record=record, stream=stream, broadcastify=broadcastify)
            time.sleep(2)
