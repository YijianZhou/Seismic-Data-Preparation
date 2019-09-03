"""
plot data continuity
"""
import os, glob
import matplotlib.pyplot as plt
from obspy import UTCDateTime
import numpy as np

# data dirs
stream_paths = glob.glob('/data3/XJ_SAC/XLS/*/*/*/*/*Z.SAC') # net/sta/year/mon/day/sac_files
start_date = UTCDateTime(2016,1,1)
end_date   = UTCDateTime(2017,1,1)

# stats for stations
sta_dict = {}
print('making station dict')
for stream_path in stream_paths:
    fname = os.path.split(stream_path)[-1]
    codes = fname.split('.')
    net, sta, date, chn = codes[0:4]
    date = UTCDateTime(codes[2])
    if date>end_date or date<start_date: continue
    if sta not in sta_dict:
       sta_dict[sta] = [date.date]
    else:
       sta_dict[sta].append(date.date)

# plot continuity
print('plot continuity')
sta_dict_keys = sorted(list(sta_dict.keys()))
for i,sta_key in enumerate(sta_dict_keys):
    xi = sta_dict[sta_key]
    plt.scatter(xi, [i]*len(xi), marker='s', s=100)

fontsize=16
ax = plt.gca()
plt.setp(ax.xaxis.get_majorticklabels(), fontsize=fontsize, rotation=20)
plt.yticks(list(range(i+1)), sta_dict_keys, fontsize=fontsize)
plt.title('Continuity Analysis for {} Network'.format(net), fontsize=fontsize+2)
plt.grid(True)
plt.show()
