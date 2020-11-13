""" Preprocess of data recorded by QS-SP instruments
"""
import sys
sys.path.append('/home/zhouyj/software/data_prep')
import os, glob
from obspy import read, UTCDateTime
import obspy
import numpy as np
import multiprocessing as mp
import sac
import warnings
warnings.filterwarnings("ignore")

# i/o paths
raw_dirs = glob.glob('/data3/XC_PKU_raw/*')
sac_root = '/data2/XC_PKU_SAC'
# cut params
num_workers = 20


# 1. read & cut into sac dir
def cut_days(st_path):
    try: stream = read(st_path)
    except: obspy.io.segy.segy.SEGYTraceReadingError; return
    for trace in stream:
        # get header info
        sta = trace.stats.station
        chn = trace.stats.channel
        # get time range
        start_time = trace.stats.starttime
        end_time = trace.stats.endtime
        start_date = UTCDateTime(start_time.date)
        end_date = UTCDateTime(end_time.date)
        num_days = int((end_date - start_date)/86400)
        for day_idx in range(num_days+1):
            # sliding date: current time step
            date = start_date + day_idx*86400
            date_code = ''.join(str(date.date).split('-'))
            # slice trace
            tr = trace.slice(date, date+86400)
            time_code = str(tr.stats.starttime)
            out_name = '%s.%s.%s.sac'%(sta, time_code, chn)
            out_dir = os.path.join(sac_root, date_code)
            out_path = os.path.join(sac_root, date_code, out_name)
            if os.path.exists(out_path): continue
            if not os.path.exists(out_dir): os.makedirs(out_dir)
            tr.write(out_path)

# 2. merge sac pieces in sac_dir
def get_sta_chn(sac_dir):
    st_paths = glob.glob(os.path.join(sac_dir,'*.sac'))
    sta_chn_list = []
    for st_path in st_paths:
        codes = os.path.basename(st_path).split('.')
        sta_chn = '%s.%s'%(codes[0], codes[-2])
        if sta_chn not in sta_chn_list: sta_chn_list.append(sta_chn)
    return sta_chn_list

def merge_sta_chn(sac_dir, sta_chn):
    date_code = os.path.basename(sac_dir)
    sta, chn = sta_chn.split('.')
    st_paths = glob.glob(os.path.join(sac_dir, '%s.*.%s.sac'%(sta, chn)))
    out_path = os.path.join(sac_dir, '%s.%s.%s.SAC'%(sta,date_code,chn))
    sac.merge(st_paths, out_path)
    for st_path in st_paths: os.unlink(st_path)


if __name__ == '__main__':
  mp.set_start_method('spawn', force=True) # or 'forkserver'

  # 1. read raw & write sac
  st_path_list = []
  for raw_dir in raw_dirs:
    print('processing %s'%raw_dir)
    sta = os.path.basename(raw_dir)
    if sta=='bad_data': continue
    st_paths = glob.glob(os.path.join(raw_dir,'E00*'))
    for st_path in st_paths: 
        if st_path.split('.')[-1]=='LOG': continue
#        cut_days(st_path)
        st_path_list.append(st_path)
  
  # apply multiprocessing
  pool = mp.Pool(num_workers)
  pool.map_async(cut_days, st_path_list)
  pool.close()
  pool.join()
  
  
  # 2. merge sac
  sac_dirs = sorted(glob.glob(os.path.join(sac_root,'*')))
  pool = mp.Pool(num_workers)
  for sac_dir in sac_dirs:
    print('processing %s'%sac_dir)
    sta_chn_list = get_sta_chn(sac_dir)
    for sta_chn in sta_chn_list:
#        merge_sta_chn(sac_dir, sta_chn)
        pool.apply_async(merge_sta_chn, args=(sac_dir, sta_chn,))
  pool.close()
  pool.join()
  
