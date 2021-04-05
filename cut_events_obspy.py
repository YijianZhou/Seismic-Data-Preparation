""" Cut event waveforms with Obspy (for miniseed data)
"""
import os, sys, glob, shutil
sys.path.append('/home/zhouyj/software/data_prep')
import numpy as np
import multiprocessing as mp
from obspy import read, UTCDateTime
from reader import read_pal_pha, get_data_dict, dtime2str
import sac


# i/o paths
data_dir = '/data/Example_data'
fpha = 'input/example_pal.pha'
out_root = '/data3/bigdata/zhouyj/Example_events'
# cut params
num_workers = 10
event_win = [10, 30] # sec before & after P
get_data_dict = get_data_dict
read_pha = read_pal_pha
pha_list = read_pha(fpha)

def cut_event(event_id):
    # get event info
    [event_loc, pick_dict] = pha_list[event_id]
    if len(event_loc)==5: 
        ot, lat, lon, dep, mag = event_loc
    if len(event_loc)==4: 
        ot, lat, lon, mag = event_loc
        dep = -1
    data_dict = get_data_dict(ot, data_dir)
    event_name = dtime2str(ot)
    event_dir = os.path.join(out_root, event_name)
    if not os.path.exists(event_dir): os.makedirs(event_dir)

    # cut event
    print('cutting {}'.format(event_name))
    for net_sta, [tp, ts] in pick_dict.items():
        time_range = [tp-event_win[0], tp+event_win[1]]
        t0 = event_win[0]
        t1 = ts - tp + event_win[0] if ts else None
        if net_sta not in data_dict: continue
        data_paths = data_dict[net_sta]
        chn_codes = [data_path.split('.')[3][0:3] for data_path in data_paths]
        out_paths = [os.path.join(event_dir,'%s.%s.sac'%(net_sta,chn)) for chn in chn_codes]
        # cut event
        for i in range(3):
            st = read(data_paths[i], starttime=time_range[0], endtime=time_range[1])
            st.write(out_paths[i])
            sac.ch_event(out_paths[i], lon, lat, dep, mag, [t0,t1])

# cut all events data
pool = mp.Pool(num_workers)
pool.map_async(cut_event, range(len(pha_list)))
pool.close()
pool.join()
