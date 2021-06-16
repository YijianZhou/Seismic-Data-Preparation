""" Cut event waveforms with SAC
"""
import os, sys, glob, shutil
sys.path.append('/home/zhouyj/software/data_prep')
import numpy as np
import multiprocessing as mp
from obspy import read, UTCDateTime
from reader import read_fpha, get_data_dict, dtime2str
import sac

# i/o paths
data_dir = '/data/Example_data'
fpha = 'output/example_pha.csv'
out_root = '/data3/bigdata/zhouyj/Example_events'
# cut params
num_workers = 10
event_win = [10, 20] # sec before & after P
get_data_dict = get_data_dict
pha_list = read_fpha(fpha)

def cut_event(event_id):
    # get event info
    [event_loc, pick_dict] = pha_list[event_id]
    ot, lat, lon, dep, mag = event_loc
    data_dict = get_data_dict(ot, data_dir)
    event_name = dtime2str(ot)
    event_dir = os.path.join(out_root, event_name)
    if not os.path.exists(event_dir): os.makedirs(event_dir)
    # cut event
    print('cutting {}'.format(event_name))
    for net_sta, [tp, ts] in pick_dict.items():
      if net_sta not in data_dict: continue
      for data_path in data_dict[net_sta]:
        b = tp - read(data_path)[0].stats.starttime - event_win[0]
        chn_code = data_path.split('.')[-2]
        out_path = os.path.join(event_dir,'%s.%s'%(net_sta,chn_code))
        # cut event
        sac.cut(data_path, b, b+sum(event_win), out_path)
        # write header
        tn = {}
        tn['t0'] = event_win[0]
        if ts: tn['t1'] = ts - tp + event_win[0]
        sac.ch_event(out_path, lat, lon, dep, mag, tn)

# cut all events data
pool = mp.Pool(num_workers)
pool.map_async(cut_event, range(len(pha_list)))
pool.close()
pool.join()
