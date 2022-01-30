""" Plot data continuity 
"""
import os, glob
import matplotlib.pyplot as plt
from obspy import read, UTCDateTime
import numpy as np

# i/o paths
stream_paths = glob.glob('/data2/Ridgecrest/*/*HZ*')
title = 'Example Data Continuity Plot'
fout = 'output/example_data_continuity.pdf'
# fig params
fig_size = (12,16)
fsize_label = 14
fsize_title = 18
mark_size = 100

# stats for stations
sta_dict = {}
print('making station dict')
for stream_path in stream_paths:
    fname = os.path.split(stream_path)[-1]
    date, net, sta, chn = fname.split('.')[0:4]
    net_sta = '.'.join([net, sta])
    if net_sta not in sta_dict:
        sta_dict[net_sta] = [UTCDateTime(date).date]
    else:
        sta_dict[net_sta].append(UTCDateTime(date).date)

print('plot continuity')
plt.figure(figsize=fig_size)
ax = plt.gca()
sta_dict_keys = sorted(list(sta_dict.keys()))
for i, sta_key in enumerate(sta_dict_keys):
    x1 = sta_dict[sta_key]
    plt.scatter(x1, [i]*len(x1), marker='s', s=mark_size)
plt.setp(ax.xaxis.get_majorticklabels(), fontsize=fsize_label, rotation=20)
plt.yticks(list(range(len(sta_dict))), sta_dict_keys, fontsize=fsize_label)
plt.title(title, fontsize=fsize_title)
plt.grid(True)
plt.tight_layout()
plt.savefig(fout)
plt.show()
