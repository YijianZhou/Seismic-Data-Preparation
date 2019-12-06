import os, sys, glob
sys.path.append('/home/zhouyj/software/data_prep')
import sac
import obspy
from obspy import read, UTCDateTime

def date2dir(date):
    yr  = str(date.year)
    mon = str(date.month).zfill(2)
    day = str(date.day).zfill(2)
    return '%s/%s/%s'%(yr, mon, day)


# i/o paths
raw_dirs = sorted(glob.glob('/data1/201503-201508/*/201*')) # root/sta/date
sac_root = '/data3/XJ_SAC'
start_date = UTCDateTime(2015,1,1)
end_date   = UTCDateTime(2019,6,1)
net = 'XLS'

# 1. gcf to sac in raw dir
for raw_dir in raw_dirs:

    # go to raw_dir
    if not os.path.isdir(raw_dir): continue
    os.chdir(raw_dir)
    sta, date = raw_dir.split('/')[-2:]
    date = UTCDateTime(date)
    if date<start_date or date>end_date: continue
    print('processing %s'%raw_dir)
    raw_e = sorted(glob.glob('*_*E[1-9].gcf'))
    raw_n = sorted(glob.glob('*_*N[1-9].gcf'))
    raw_z = sorted(glob.glob('*_*Z[1-9].gcf'))
    fnames = raw_e + raw_n + raw_z

    for fname in fnames:

      # read data
      print('read %s'%fname)
      try: st = read(fname)
      except: obspy.io.segy.segy.SEGYTraceReadingError; print('bad data!'); continue

      # maybe multi traces
      for tr in st:
        # get header
        header = tr.stats
        t0, t1 = header.starttime, header.endtime
        chn = header.channel
#        sta = header.station
        if not chn in ['HHE','HHN','HHZ']: print('bad channel!'); continue

        # set out path
        out_dir = os.path.join(sac_root, sta, date2dir(date))
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        out_name = '%s.%s.%s.sac'%(sta, t0, chn)
        out_path = os.path.join(out_dir, out_name)
        tr.slice(date, date+86400).write(out_path)
        if t0 < date:
            out_dir = os.path.join(sac_root, sta, date2dir(date-86400))
            if not os.path.exists(out_dir): os.makedirs(out_dir)
            out_path = os.path.join(out_dir, out_name)
            tr = tr.slice(t0, date).write(out_path)
        if t1 > date+86400: 
            out_dir = os.path.join(sac_root, sta, date2dir(date+86400))
            if not os.path.exists(out_dir): os.makedirs(out_dir)
            out_path = os.path.join(out_dir, out_name)
            tr = tr.slice(date+86400, t1).write(out_path)


# 2. merge sac files in sac dir
sac_dirs = sorted(glob.glob(os.path.join(sac_root, '*/*/*/*')))
for sac_dir in sac_dirs:
    print('merge sac files in %s' %sac_dir)
    os.chdir(sac_dir)
    info = os.getcwd().split('/')
    sta = info[-4]
    date = info[-3] + info[-2] + info[-1]
    sac.merge(glob.glob('*.HHE.sac'), '%s.%s.%s.HHE.SAC' %(net, sta, date))
    sac.merge(glob.glob('*.HHN.sac'), '%s.%s.%s.HHN.SAC' %(net, sta, date))
    sac.merge(glob.glob('*.HHZ.sac'), '%s.%s.%s.HHZ.SAC' %(net, sta, date))
    # delete sac segments
    todel = glob.glob('*.sac')
    for fname in todel: os.unlink(fname)
