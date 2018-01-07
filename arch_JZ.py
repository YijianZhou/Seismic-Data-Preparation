"""
archive the SAC files (msd2sac) in /data2/JZ
each SAC file is a continuous waveform of tens of days.
slice into files of one day's data and move to /data3/JZ_SAC
"""
import glob, os, shutil
from obspy.core import read
from obspy.core import UTCDateTime
import obspy
import numpy as np
# origin path in /data2
paths = glob.glob('/data2/JZ/00*/*/1710')
path_arc = '/data3/JZ_SAC/'
for path in paths:
  os.chdir(path)
  print('entering path %s'%(path))
  streams = glob.glob('*SAC')
  for stream in streams:
    net, sta, chn, _ = stream.split('.')
    st = read(stream)
    ts, te = st[0].stats.starttime, st[0].stats.endtime
    print('archiving file %s, from %s to %s'%(stream, ts, te))
    t0, tn = UTCDateTime(ts.year, ts.month, ts.day+1), UTCDateTime(te.year, te.month, te.day)
    days = int(np.floor((tn - ts)/86400))
    st0 = st.slice(ts, t0)
    st0.write(os.path.join(path_arc, net, '2017', str(ts.month).zfill(2), str(ts.day).zfill(2),
                '.'.join([net,sta,chn,'2017',str(ts.julday).zfill(3), 'SAC'])),format='SAC')
    stn = st.slice(tn, te)
    stn.write(os.path.join(path_arc, net, '2017', str(te.month).zfill(2), str(te.day).zfill(2),
                '.'.join([net,sta,chn,'2017',str(te.julday).zfill(3), 'SAC'])), format='SAC')
    for nd in range(days):
      starttime = t0 + 86400*nd
      endtime = t0 + 86400*(nd+1)
      sti = st.slice(starttime, endtime)
      sti.write(os.path.join(path_arc, net, '2017', str(starttime.month).zfill(2), str(starttime.day).zfill(2),
                  '.'.join([net,sta,chn,'2017',str(starttime.julday).zfill(3), 'SAC'])),format='SAC')
