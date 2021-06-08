""" Download SCSN data by STP
STP can be downloaded from https://scedc.caltech.edu/data/stp/index.html
"""
import os, shutil, glob
from obspy import UTCDateTime
import subprocess
import multiprocessing as mp

# i/o files
time_range = '20190704-20190725'
num_workers = 10
fsta = 'output/rc_scsn.sta'
out_root = '/data2/Ridgecrest'
if not os.path.exists(out_root): os.makedirs(out_root)

# prepare input
start_time, end_time = [UTCDateTime(date) for date in time_range.split('-')]
num_days = (end_time.date - start_time.date).days

def down_stp_data(net, sta, chn, date):
    # make out_dir
    year = str(date.year)
    mon = str(date.month).zfill(2)
    day = str(date.day).zfill(2)
    out_dir = os.path.join(out_root, year+mon+day)
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    # download & move
    p = subprocess.Popen(['stp'], stdin=subprocess.PIPE)
    s = "GAIN ON \n"
    s+= "WIN {} {} {} {}/{}/{},00:00:00 +1d \n".format(net, sta, chn, year, mon, day)
    s+= "quit \n"
    p.communicate(s.encode())
    # move to out dir
    out_files = glob.glob('%s%s%s*.%s.%s.*'%(year, mon, day, net, sta))
    if len(out_files)!=3:
        for out_file in out_files: os.unlink(out_file)
    else:
        for out_file in out_files: shutil.move(out_file, out_dir)

# download data
pool = mp.Pool(num_workers)
f=open(fsta); lines=f.readlines(); f.close()
for line in lines:
    net, sta, chn = line.split(',')[0:3]
    chn = chn[0:2]+'%'
    for i in range(num_days):
        date = start_time + i*86400
        pool.apply_async(down_stp_data, args=(net, sta, chn, date,))

pool.close()
pool.join()
