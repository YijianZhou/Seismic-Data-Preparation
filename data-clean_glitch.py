import os, sys, glob
sys.path.append('/home/zhouyj/software/data_prep')
import numpy as np
from obspy import read, UTCDateTime
from signal_lib import preprocess
import warnings
warnings.filterwarnings("ignore")

# i/o paths
data_dirs = sorted(glob.glob('/data/Example_data/*'))
bak_dir = '/data/Example_data_bak'
fout = open('output/eg_data-glitch.csv','w')
# data prep
freq_band = [1,20]
win_sta, win_lta = 0.5, 1
min_snr = 100
min_gap_npts = 10
num_glitch_bak = 100
glitch_wid = 1. # sec
to_write = 0 # 0 - not to write; 1 - write >num_glitch_bak; 2 - write all


def calc_sta_lta(data, win_lta_npts, win_sta_npts):
    npts = len(data)
    if npts < win_lta_npts + win_sta_npts:
        print('input data too short!')
        return np.zeros(1)
    sta = np.zeros(npts)
    lta = np.ones(npts)
    data_cum = np.cumsum(data)
    sta[:-win_sta_npts] = data_cum[win_sta_npts:] - data_cum[:-win_sta_npts]
    sta /= win_sta_npts
    lta[win_lta_npts:]  = data_cum[win_lta_npts:] - data_cum[:-win_lta_npts]
    lta /= win_lta_npts
    sta_lta = sta/lta
    sta_lta[0:win_lta_npts] = 0.
    sta_lta[np.isinf(sta_lta)] = 0.
    sta_lta[np.isnan(sta_lta)] = 0.
    return sta_lta

def remove_glitch(st):
    # data prep
    data_raw = st[0].data.copy()
    start_time = st[0].stats.starttime
    samp_rate = st[0].stats.sampling_rate
    win_sta_npts = int(samp_rate*win_sta)
    win_lta_npts = int(samp_rate*win_lta)
    glitch_wid_npts = int(samp_rate*glitch_wid)
    st = preprocess(st, samp_rate, freq_band)
    data_2 = st[0].data**2
    # forward & backward STA/LTA
    sta_lta_0 = calc_sta_lta(data_2, win_lta_npts, win_sta_npts)
    sta_lta_1 = calc_sta_lta(data_2[::-1], win_lta_npts, win_sta_npts)[::-1]
    gap_idx = np.where(sta_lta_0>=min_snr)[0]
    large_back = np.array(sta_lta_1>=min_snr, dtype=np.int32)
    gap_list = np.split(gap_idx, np.where(np.diff(gap_idx)!=1)[0] + 1)
    gap_list = [gap for gap in gap_list if len(gap)>0]
    glitch_times = []
    for gap in gap_list:
        if sum(large_back[gap[-1]:gap[-1]+glitch_wid_npts])==0: continue
        ref_idx = gap[-1] + glitch_wid_npts
        idx0 = gap[0]
        if sum(large_back[ref_idx:ref_idx+2*glitch_wid_npts]==0)==0: continue
        idx1 = ref_idx + np.where(large_back[ref_idx:ref_idx+2*glitch_wid_npts]==0)[0][0]
        t0, t1 = start_time + idx0/samp_rate, start_time + idx1/samp_rate
        glitch_times.append([t0, t1])
        # interploate fill
        delta = (data_raw[idx1] - data_raw[idx0]) / (idx1-idx0)
        interp_fill = np.array([data_raw[idx0] + ii*delta for ii in range(idx1-idx0)])
        data_raw[idx0:idx1] = interp_fill
    st[0].data = data_raw
    return st, glitch_times

def remove_gap(st):
    data = st[0].data
    npts = len(data)
    gap_idx = np.where(data==0)[0]
    gap_list = np.split(gap_idx, np.where(np.diff(gap_idx)!=1)[0] + 1)
    gap_list = [gap for gap in gap_list if len(gap)>=min_gap_npts]
    for gap in gap_list:
        idx0, idx1 = max(0, gap[0]-1), min(npts-1, gap[-1]+1)
        delta = (data[idx1] - data[idx0]) / (idx1-idx0)
        interp_fill = np.array([data[idx0] + ii*delta for ii in range(idx1-idx0)])
        data[idx0:idx1] = interp_fill
    st[0].data = data
    return st


for data_dir in data_dirs:
    print('cleaning', data_dir)
    stz_paths = sorted(glob.glob(os.path.join(data_dir,'*Z.%s'%data_format)))
    for stz_path in stz_paths:
        stz_dir, fname = os.path.split(stz_path)
        net, sta = fname.split('.')[1:3]
        st_paths = sorted(glob.glob('%s/*.%s.%s.*'%(stz_dir,net,sta)))
        is_bad, st_raw = False, []
        for st_path in st_paths:
            try: st = read(st_path)
            except: print('error in reading file', st_path); continue
            bak_path = os.path.join(bak_dir, os.path.basename(st_path))
            st_raw.append([st.copy(), bak_path])
            st = remove_gap(st)
            st, glitch_times = remove_glitch(st)
            num_glitch = len(glitch_times)
            for [t0,t1] in glitch_times: fout.write('%s.%s,%s,%s\n'%(net,sta,t0,t1))
            if num_glitch>=num_glitch_bak: 
                is_bad = True
                if to_write==1: st.write(st_path)
            elif num_glitch>0: 
                if to_write==2: st.write(st_path)
        if is_bad: 
            for st, bak_path in st_raw: st.write(bak_path)
fout.close()
