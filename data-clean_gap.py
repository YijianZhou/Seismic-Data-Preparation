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

def ave_fill(st):
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
    return st, len(gap_list)

for data_dir in data_dirs:
    print('cleaning', data_dir)
    st_paths = sorted(glob.glob(os.path.join(data_dir,'*')))
    for st_path in st_paths:
        try: st = read(st_path)
        except: print('error in reading file', st_path); continue
        fname = os.path.basename(st_path)
        bak_path = os.path.join(bak_dir, fname)
        st, num_gap = ave_fill(st)
        if num_gap>0: print('average filled %s gaps: %s'%(num_gap, st_path))
        if num_gap>=num_gap_bak: shutil.copy(st_path, bak_path)
        st.write(st_path)

