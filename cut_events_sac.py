import sys, os, glob, shutil
sys.path.append('/home/zhouyj/software/data_prep')
import numpy as np
import torch.multiprocessing as mp
from torch.utils.data import Dataset, DataLoader
from obspy import read, UTCDateTime
import sac
from signal_lib import preprocess
from reader import read_fpha, get_data_dict, dtime2str
import warnings
warnings.filterwarnings("ignore")

# i/o paths
data_dir = '/data/Example_data'
fpha = 'output/eg.pha'
out_root = '/data/Example_events'
if not os.path.exists(out_root): os.makedirs(out_root)
# cut params
num_workers = 10
win_len = [10, 20]
freq_band = [1, 20]
samp_rate = 100
get_data_dict = get_data_dict # modify this if use customized function


class Cut_Events(Dataset):
  """ Dataset for cutting templates
  """
  def __init__(self, event_list):
    self.event_list = event_list

  def __getitem__(self, index):
    data_paths_i = []
    # get event info
    event_loc, pick_dict = self.event_list[index]
    ot, lat, lon, dep, mag = event_loc
    event_name = dtime2str(ot)
    data_dict = get_data_dict(ot, data_dir)
    event_dir = os.path.join(out_root, event_name)
    if not os.path.exists(event_dir): os.makedirs(event_dir)
    # cut event
    for net_sta, [tp, ts] in pick_dict.items():
        data_paths = data_dict[net_sta]
        chn_codes = [data_path.split('.')[-2] for data_path in data_paths]
        out_paths = [os.path.join(event_dir,'%s.%s'%(net_sta,chn)) for chn in chn_codes]
        # cut event
        b_list = [tp - read(data_path, headonly=True)[0].stats.starttime - win_len[0] \
            for data_path in data_paths]
        sac.cut(data_paths[0], b_list[0], b_list[0]+sum(win_len), out_paths[0])
        sac.cut(data_paths[1], b_list[1], b_list[1]+sum(win_len), out_paths[1])
        sac.cut(data_paths[2], b_list[2], b_list[2]+sum(win_len), out_paths[2])
        # preprocess
        st  = read(out_paths[0])
        st += read(out_paths[1])
        st += read(out_paths[2])
        st = preprocess(st, samp_rate, freq_band)
        if len(st)!=3: 
            for out_path in out_paths: os.unlink(out_path)
            continue
        # write header & record out_paths
        t0 = win_len[0]
        t1 = ts - tp + win_len[0]
        for ii in range(3): 
            st[ii].stats.sac.t0, st[ii].stats.sac.t1 = t0, t1
            st[ii].write(out_paths[ii], format='sac')
        data_paths_i.append(out_paths)
    return data_paths_i

  def __len__(self):
    return len(self.event_list)


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True) # 'spawn' or 'forkserver'
    event_list = read_fpha(fpha)
    data_paths  = []
    dataset = Cut_Events(event_list)
    dataloader = DataLoader(dataset, num_workers=num_workers, batch_size=None)
    for i, data_paths_i in enumerate(dataloader):
        data_paths += data_paths_i
        if i%10==0: print('%s/%s events done/total'%(i,len(dataset)))
    fout_data_paths = os.path.join(out_root,'data_paths.npy')
    np.save(fout_data_paths, data_paths)

