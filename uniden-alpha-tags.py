#!/usr/bin/env python3

from urllib.parse import quote_plus
import time
import serial
import requests

def monitor(scanner):
  """Get reception status.
  The Scanner returns GLG,,,,,,,,,[\r] until it detects a frequency or a TGID.
  FRQ/TGID  Frequency or TGID
  MOD   Modulation (AM/FM/NFM/WFM/FMB)
  ATT   Attenuation (0:OFF / 1:ON)
  CTCSS/DCS CTCSS/DCS Status (0-231)
  NAME1   System, Site or Search Name
  NAME2   Group Name
  NAME3   Channel Name
  SQL   Squelch Status (0:CLOSE / 1:OPEN)
  MUT   Mute Status (0:OFF / 1:ON)
  SYS_TAG   Current system number tag (0-999/NONE)
  CHAN_TAG  Current channel number tag (0-999/NONE)
  P25NAC    P25 NAC Status ( 0-FFF: 0-FFF / NONE: Nac None)"""

  current_freq = None
  last_received = 0

  while True:
    scanner.write(b"GLG\r")

    result = scanner.readall().decode('ascii').strip('\r')

    status = {}

    (cmd,freq,mod,att,ctcss_dcs,name1,name2,name3,
      sql,mut,sys_tag,chan_tag,p25nac) = result.split(",")

    receiving = mut == '0'

    now = time.perf_counter()

    if receiving:
      last_received = now
      if current_freq != freq:
        current_freq = freq
        update_status(current_freq)

    elif current_freq != None and now - last_received > 2:
        current_freq = None
        last_freq_updated = now
        update_status(current_freq)

    time.sleep(0.1)

def update_status(freq):
  msg = ' '
  if freq:
    msg = get_freq_name(freq)
    print(msg)
  else:
    print('Scanning')
  requests.get(
    "http://{}/admin/metadata?mount=/{}&mode=updinfo&song={}".format(CONFIG['icecast_host'], CONFIG['icecast_mount'], quote_plus(msg)),
    auth=('source', CONFIG['icecast_password']), timeout=1.0)


def get_freq_name(freq):
  names = {
    '470.9875': 'Rail Emergency / Power Control',
    '471.0375': 'Blue and Pink Line Ops',
    '471.0625': 'Green and Orange Line Ops',
    '471.0875': 'Brown, Purple, and Yellow Line Ops',
    '471.1125': 'Red Line Ops',
  }
  try:
    return f'%s (%s)' % (names[freq], freq)
  except KeyError:
    return f'%s MHz' % freq


CONFIG = {
  'serial_port': '/dev/ttyUSB0',
  'icecast_host': '',
  'icecast_mount': '',
  'icecast_password': ''
}

scanner = serial.Serial(CONFIG['serial_port'], 57600, timeout=0.1)

try:
  monitor(scanner)
except KeyboardInterrupt:
  pass

scanner.close()
