import os, argparse, shutil, glob
from obspy import UTCDateTime
import subprocess
import multiprocessing as mp

# i/o files
fsta = 'output/rc_scsn_sta.csv'
f=open(fsta); lines=f.readlines(); f.close()
out_root = '/data2/Ridgecrest'
# down params
date_range = '20190704-20190711'
num_proc = 7
start_date, end_date = [UTCDateTime(date) for date in date_range.split('-')]
win_len = (end_date - start_date) / num_proc

def down_data(date_range):
  num_days = (date_range[1].date - date_range[0].date).days
  # read sta file
  for line in lines:
    net_sta, chn, _, _, _ = line.split(',')
    net, sta = net_sta.split('.')
    chn += '%'
    for day_idx in range(num_days):
        date = date_range[0] + day_idx*86400
        yr  = str(date.year)
        mon = str(date.month).zfill(2)
        day = str(date.day).zfill(2)
        out_dir = os.path.join(out_root, net, sta, yr, mon, day)
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        p = subprocess.Popen(['stp'], stdin=subprocess.PIPE)
        s = "GAIN ON \n"
        s+= "WIN {} {} {} {}/{}/{},00:00:00 +1d \n".format(net, sta, chn, yr, mon, day)
        s+= "quit \n"
        p.communicate(s.encode())
        # move to out dir
        out_files = glob.glob('%s%s%s*.%s.%s.*'%(yr, mon, day, net, sta))
        if len(out_files)!=3: 
            for out_file in out_files: os.unlink(out_file)
        else:
            for out_file in out_files: shutil.move(out_file, out_dir)

# download data
pool = mp.Pool(num_proc)
for proc_idx in range(num_proc):
    t0 = UTCDateTime((start_date + proc_idx*86400).date)
    t1 = UTCDateTime((start_date + proc_idx*86400 + win_len).date)
    print(t0, t1)
    pool.apply_async(down_data, args=([t0, t1],))
pool.close()
pool.join()
