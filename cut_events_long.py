import sys, os, glob, shutil
sys.path.append('/home/zhouyj/software/data_prep')
import numpy as np
import torch.multiprocessing as mp
from torch.utils.data import Dataset, DataLoader
from obspy import read, UTCDateTime
from signal_lib import preprocess, sac_ch_time
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

def cut_event_window(stream_paths, tp, ts, out_paths):
    t0 = tp - win_len[0] - sum(win_len)/2
    t1 = t0 + sum(win_len)*2
    st  = read(stream_paths[0], starttime=t0, endtime=t1)
    st += read(stream_paths[1], starttime=t0, endtime=t1)
    st += read(stream_paths[2], starttime=t0, endtime=t1)
    if len(st)!=3: return False
    st = preprocess(st, samp_rate, freq_band)
    st = st.slice(tp-win_len[0], tp+win_len[1])
    if len(st)!=3: return False
    for ii, tr in enumerate(st):
        tr.write(out_paths[ii], format='sac')
        tr = sac_ch_time(read(out_paths[ii]))[0]
        tr.stats.sac.t0, tr.stats.sac.t1 = tp-t0, ts-t0
        tr.write(out_paths[ii], format='sac')
    return True

class Cut_Events(Dataset):
  """ Dataset for cutting events
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
        if net_sta not in data_dict: continue
        stream_paths = data_dict[net_sta]
        out_paths = [os.path.join(event_dir,'%s.%s'%(net_sta,ii)) for ii in range(3)]
        is_cut = cut_event_window(stream_paths, tp, ts, out_paths)
        if not is_cut: continue
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

