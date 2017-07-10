#!/usr/bin/env python3

import json
import os
import subprocess

recordingPath = 'R:\\recordings'


def start_ffmpeg(channel, record=True, stream=False):
    ffmpeg_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'bin', 'ffmpeg')
    inputopts = [
        '-f', 'dshow' if os.name == 'nt' else 'pulse',
        '-i', ('audio=' + channel['audio']) if os.name == 'nt' else channel['audio']
        # '-af', 'volume=1.25'
    ]

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
            os.path.join(recordingPath, channel['slug'], channel['slug'] + '_%Y%m%d_%H%M%S.aac')
        ]
        args = ['start', 'Record: ' + channel['name'], ffmpeg_path] + inputopts + recordingopts
        subprocess.run(args, shell=True)

    if stream:
        streamopts = [
            '-c:a', 'aac',
            '-b:a', '32k',
            '-ac', '1',
            '-ar', '22050',
            '-f', 'rtsp',
            '-rtsp_transport', 'udp',
            '-muxdelay', '0',
            'rtsp://dev.tendian.io:5545/' + channel['slug']
        ]
        args = ['start', 'Stream: ' + channel['name'], ffmpeg_path] + inputopts + streamopts
        subprocess.run(args, shell=True)


with open('channels.json') as channels_file:
    channels = json.load(channels_file)
    for channel in channels:
        start_ffmpeg(channel, True, False)
