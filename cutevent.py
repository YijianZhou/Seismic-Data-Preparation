"""
cutevent by Yijian ZHOU 2018-01-02
input:
catalog; stream_path; time window
output:
./events/[origin time]/net.sta.ot.chn.SAC
head file: 
stlo stla stel
evlo evla evdp
kztime
b = 0
"""
import os, glob, shutil
from obspy.core import *
import subprocess
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--stream_path", type = str,
                    default = '/data3/XJ_SAC/ZSY')
parser.add_argument("--catalog", type = str,
                    default = 'catalog.csv')
parser.add_argument("--time_win", type = float,
                    nargs=2, default=(0, 50))
args = parser.parse_args()

# set the time window
time_before = args.time_win[0]
time_after = args.time_win[1]
# i/o path
stream_path = args.stream_path
out_path = os.path.join(os.getcwd(), 'events')
if os.path.exists(out_path):
    print('check your output path!')
os.mkdir(out_path)

tmp = open(args.catalog); ctlg_lines = tmp.readlines(); tmp.close()
for ctlg_line in ctlg_lines:
    print('cutting event {}'.format(ctlg_line))
    date_time, lat, lon, mag = ctlg_line.split(',')
    mag = mag.split('\n')[0]
    t0 = UTCDateTime(date_time)
    # make output dir
    date, time = date_time.split('T')
    time_key = ''.join(date.split('-')) +\
               ''.join(time.split(':'))[0:6]
    out_dir = os.path.join(out_path, time_key)
    if not os.path.exists(out_dir):
       os.mkdir(out_dir)
    # find stream paths
    rela_path = '/'.join(str(date).split('-'))
    paths = glob.glob(os.path.join(stream_path, '*', rela_path))
    # time window for slicing
    ts = t0 + time_before
    te = t0 + time_after

    # use sac
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    for path in paths:
      os.chdir(path)
      for stream in glob.glob('*'):
          net, sta, yr, jday, chn, _ = stream.split('.')
          fname = '.'.join([net, sta, time_key, chn, 'SAC'])
          b = ts - UTCDateTime(yr+jday)
          e = te - UTCDateTime(yr+jday)
          print('cutting stream {}, {} to {}'.format(stream, b, e))
          # some types of err
          if e > 86400:
             print('window out of range!')
             continue
          # cut event and change the head file
          s += "cuterr fillz \n"
          s += "cut b %s %s \n" %(b, e)
          s += "r %s \n" %os.path.join(path, stream)
          s += "ch b %s \n" %time_before
          s += "ch nzhour %s nzmin %s nzsec %s \n" %(t0.hour, t0.minute, t0.second)
          s += "ch nzmsec %s \n" %str(t0.microsecond)[0:3]
          s += "ch evlo %s evla %s evdp 5 \n" %(lon, lat)
          s += "ch mag %s \n" %mag
          s += "w %s \n" %os.path.join(out_dir, fname)
    s += "q \n"
    p.communicate(s.encode())
