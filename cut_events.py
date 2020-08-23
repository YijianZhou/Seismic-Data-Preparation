""" Cut event waveforms
"""
import os, sys, glob, shutil
sys.path.append('/home/zhouyj/software/data_prep')
import numpy as np
import multiprocessing as mp
from obspy import read, UTCDateTime
from reader import read_rc_pha, get_rc_data, dtime2str
import sac


# i/o paths
data_dir = '/data2/Ridgecrest/*/*'
fpha = 'output/rc_scsn_pha.csv'
out_root = '/data3/bigdata/zhouyj/RC_events'
# cut params
num_workers =10
event_win = [10, 20] # sec before & after P
get_data_dict = get_rc_data
read_pha = read_rc_pha
pha_list = read_pha(fpha)

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
        b = tp - UTCDateTime(ot.date) - event_win[0]
        if net_sta not in data_dict: continue
        data_paths = data_dict[net_sta]
        chn_codes = [data_path.split('.')[-2] for data_path in data_paths]
        out_paths = [os.path.join(event_dir,'%s.%s'%(net_sta,chn)) for chn in chn_codes]
        # cut event
        sac.cut(data_paths[0], b, b+event_win[1], out_paths[0])
        sac.cut(data_paths[1], b, b+event_win[1], out_paths[1])
        sac.cut(data_paths[2], b, b+event_win[1], out_paths[2])
        # write header
        t0 = event_win[0]
        t1 = ts - tp + event_win[0] if ts else ts
        sac.ch_event(out_paths[0], lon, lat, dep, mag, [t0,t1])
        sac.ch_event(out_paths[1], lon, lat, dep, mag, [t0,t1])
        sac.ch_event(out_paths[2], lon, lat, dep, mag, [t0,t1])

# cut all events data
pool = mp.Pool(num_workers)
pool.map_async(cut_event, range(len(pha_list)))
pool.close()
pool.join()

