""" Data clean: data gaps that are zero-filled
    Zero-filled gaps will become glitches after rmean; rtr; taper; filter. 
    This code change the zero-filled fata into interpolation
    If the data is merged with interpolation strategy, no need to run this code.
"""
import os, shutil, glob
import numpy as np
from obspy import read, UTCDateTime

# i/o paths
data_dirs = sorted(glob.glob('/data/Example_data/*'))
bak_dir = '/data/Example_bak'
# data clean params
min_gap_npts = 10 
num_gap_bak = 50 # if num_gap>num_gap_bak, backup

def fill_gap(st):
    data = st[0].data
    npts = len(data)
    gap_idx = np.where(data==0)[0]
    gap_list = np.split(gap_idx, np.where(np.diff(gap_idx)!=1)[0] + 1)
    gap_list = [gap for gap in gap_list if len(gap)>=min_gap_npts]
    num_gap = len(gap_list)
    for ii,gap in enumerate(gap_list):
        idx0, idx1 = max(0, gap[0]-1), min(npts-1, gap[-1]+1)
        if ii<num_gap-1: idx2 = min(idx1+(idx1-idx0), gap_list[ii+1][0])
        else: idx2 = min(idx1+(idx1-idx0), npts-1)
        if idx2==idx1+(idx1-idx0): data[idx0:idx1] = data[idx1:idx2]
        else:
            num_tile = int(np.ceil((idx1-idx0)/(idx2-idx1)))
            data[idx0:idx1] = np.tile(data[idx1:idx2], num_tile)[0:idx1-idx0]    st[0].data = data
    st[0].data = data
    return st, len(gap_list)

for data_dir in data_dirs:
    print('cleaning', data_dir)
    st_paths = sorted(glob.glob(os.path.join(data_dir,'*')))
    for st_path in st_paths:
        try: st = read(st_path)
        except: print('error in reading file', st_path); continue
        fname = os.path.basename(st_path)
        bak_path = os.path.join(bak_dir, fname)
        st, num_gap = fill_gap(st)
        if num_gap>=num_gap_bak: shutil.copy(st_path, bak_path)
        if num_gap>0: 
            print('average filled %s gaps: %s'%(num_gap, st_path))
            st.write(st_path)

