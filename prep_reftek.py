import os, sys, glob
sys.path.append('/home/zhouyj/Documents/data_prep')
import obspy
from obspy import read, UTCDateTime
import sac
import warnings
warnings.filterwarnings("ignore")

def date2dir(date):
    yr  = str(date.year)
    mon = str(date.month).zfill(2)
    day = str(date.day).zfill(2)
    return '%s/%s/%s'%(yr, mon, day)


# i/o paths
raw_dirs = sorted(glob.glob('/data2/201508-201603/*/2016*/*/1')) # root/sta/date/das/1/rt_files
#raw_dirs = sorted(glob.glob('/data2/201603-201702/*/2016*/*/1')) # root/sta/date/das/1/rt_files
sac_root = '/data/XJ_SAC/XLS'
start_date = UTCDateTime(2016,1,1)
end_date   = UTCDateTime(2017,1,1)
net = 'XLS'
chn_seq = ['HHZ','HHN','HHE']
extension = '_006DDD00'

# 1. reftek (raw dir) to sac (sac dir): r raw dir & w sac dir
for raw_dir in raw_dirs:
    if not os.path.isdir(raw_dir): continue
    os.chdir(raw_dir)
    date = UTCDateTime(raw_dir.split('/')[-3])
    sta = raw_dir.split('/')[-2]
    if date<start_date or date>end_date: continue
    print('processing %s' %raw_dir)
    rt_files = sorted(glob.glob('*%s'%extension))
    for rt_file in rt_files:
      print('read %s' %rt_file)
      try: st = read(rt_file)
      except: obspy.io.segy.segy.SEGYTraceReadingError; print('bad data!'); continue
      if len(st)!=3: print('channel error!'); continue
      for idx,tr in enumerate(st):
        header = tr.stats
        t0, t1 = header.starttime, header.endtime
        # set out path
        out_dir = os.path.join(sac_root, sta, date2dir(date))
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        dtime = ''.join(date2dir(date).split('/')) + rt_file[0:2]
        chn = chn_seq[idx]
        out_name = '%s.%s.%s.sac'%(sta, dtime, chn)
        out_path = os.path.join(out_dir, out_name)
        tr.slice(date, date+86400).write(out_path)
        if t0 < date:
            tr0 = tr.slice(t0, date)
            out_dir0 = os.path.join(sac_root, sta, date2dir(date-86400))
            if not os.path.exists(out_dir0): os.makedirs(out_dir0)
            out_name0 = 'aug0.' + out_name
            out_path0 = os.path.join(out_dir0, out_name0)
            tr0.write(out_path0)
        if t1 > date+86400: 
            tr1 = tr.slice(date+86400, t1)
            out_dir1 = os.path.join(sac_root, sta, date2dir(date+86400))
            if not os.path.exists(out_dir1): os.makedirs(out_dir1)
            out_name1 = 'aug1.' + out_name
            out_path1 = os.path.join(out_dir1, out_name1)
            tr1.write(out_path1)


# 2. merge sac files in sac dir
""" This can be done seperatly
"""
sac_dirs = sorted(glob.glob(os.path.join(sac_root, '*/*/*/*')))
for sac_dir in sac_dirs:
    print('merge sac files in %s' %sac_dir)
    os.chdir(sac_dir)
    codes = os.getcwd().split('/')
    sta = codes[-4]
    date = codes[-3] + codes[-2] + codes[-1]
    sac.merge(glob.glob('*.%s.*'%chn_seq[0]), '%s.%s.%s.%s.SAC' %(net, sta, date, chn_seq[0]))
    sac.merge(glob.glob('*.%s.*'%chn_seq[1]), '%s.%s.%s.%s.SAC' %(net, sta, date, chn_seq[1]))
    sac.merge(glob.glob('*.%s.*'%chn_seq[2]), '%s.%s.%s.%s.SAC' %(net, sta, date, chn_seq[2]))
    # delete sac segments
    todel = glob.glob('*.sac')
    for fname in todel: os.unlink(fname)

