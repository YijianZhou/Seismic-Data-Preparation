import os, sys, glob
sys.path.append('/home/zhouyj/software/data_prep')
import obspy
from obspy import read, UTCDateTime
import sac

def date2dir(date):
    year = str(date.year)
    mon  = str(date.month).zfill(2)
    day  = str(date.day).zfill(2)
    return os.path.join(year, mon, day)

# i/o paths
#raw_dirs = sorted(glob.glob('/data2/ZSY_raw/20161125/YN/*'))
#raw_dirs = sorted(glob.glob('/data2/ZSY_raw/20170327/YN/*'))
#raw_dirs = sorted(glob.glob('/data2/ZSY_raw/20171226/YN/*'))
#raw_dirs = sorted(glob.glob('/data2/ZSY_raw/20180331/YN/*'))
#raw_dirs = sorted(glob.glob('/data2/ZSY_raw/20180918/YN/*'))
#raw_dirs = sorted(glob.glob('/data2/ZSY_raw/20180930/YN/*'))
raw_dirs = sorted(glob.glob('/data2/ZSY_raw/20190218/YN/*'))
sac_root = '/data2/ZSY_SAC/YN'

# 1. raw dir: seed2sac
for raw_dir in raw_dirs:
  # go to raw dir
  os.chdir(raw_dir)
  print('processing %s'%raw_dir)
  fnames = glob.glob('*.seed')
  for fname in fnames:
    print('seed2sac: %s'%fname)
    date, net, sta, _ = fname.split('.')
    year, mon, day = date[0:4], date[4:6], date[6:8]
    out_dir = os.path.join(sac_root, sta, year, mon, day)
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    sac.seed2sac(fname, out_dir)


# 2. check date
sac_dirs = sorted(glob.glob(os.path.join(sac_root, 'KMI/*/*/*'))) # sta/year/mon/day
for sac_dir in sac_dirs:
  print('check %s'%sac_dir)
  codes = sac_dir.split('/')
  sta = codes[-4]
  date0 = UTCDateTime(''.join(codes[-3:]))
  date1 = date0 + 86400
  os.chdir(sac_dir)
  fnames = glob.glob('*.D.SAC')
  for fname in fnames:
    head = read(fname, headonly=True)[0].stats
    t0, t1 = head.starttime, head.endtime
    if date0<t0 and date1>t1: continue
    if t0<date0:
        out_dir = os.path.join(sac_root, sta, date2dir(t0))
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        out_path = os.path.join(out_dir, 'aug.'+fname)
        sac.cut(fname, 0, date0-t0, out_path)
    if t1>date1:
        out_dir = os.path.join(sac_root, sta, date2dir(t1))
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        out_path = os.path.join(out_dir, 'aug.'+fname)
        sac.cut(fname, date1-t0, t1-t0, out_path)
    if date1<t0 or date0>t1: os.unlink(fname)
    else: sac.cut(fname, date0-t0, date1-t0, fname)


# 3. merge in sac dir
sac_dirs = sorted(glob.glob(os.path.join(sac_root, 'KMI/201[8-9]/*/*')))
for sac_dir in sac_dirs:
    print('merge sac files in %s' %sac_dir)
    os.chdir(sac_dir)
    codes = sac_dir.split('/')
    net, sta = codes[-5:-3]
    date = UTCDateTime(''.join(codes[-3:]))
    year = str(date.year)
    jday = str(date.julday).zfill(3)
    sac.merge(glob.glob('*.BHE.D.SAC'), '%s.%s.%s.%s.BHE.SAC' %(net, sta, year, jday))
    sac.merge(glob.glob('*.BHN.D.SAC'), '%s.%s.%s.%s.BHN.SAC' %(net, sta, year, jday))
    sac.merge(glob.glob('*.BHZ.D.SAC'), '%s.%s.%s.%s.BHZ.SAC' %(net, sta, year, jday))
    # delete sac segments
    todel = glob.glob('*.D.SAC')
    for fname in todel: os.unlink(fname)
