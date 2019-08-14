import os, sys, glob
sys.path.append('/home/zhouyj/software/mycode')
import sac
import obspy
from obspy import read, UTCDateTime

def date2dir(date):
    yr  = str(date.year)
    mon = str(date.month).zfill(2)
    day = str(date.day).zfill(2)
    return '%s/%s/%s'%(yr, mon, day)


# i/o paths
#raw_dirs = sorted(glob.glob('/data1/201508-201603/*/*')) # root/sta/date
raw_dirs = sorted(glob.glob('/data1/201603-201702/*/*')) # root/sta/date
sac_root = '/data3/XJ_SAC/XLS'
start_date = UTCDateTime(2016,1,1)
end_date   = UTCDateTime(2016,9,1)

# 1. gcf to sac in raw dir
for raw_dir in raw_dirs:
    if not os.path.isdir(raw_dir): continue
    os.chdir(raw_dir)
    date = UTCDateTime(os.path.split(os.getcwd())[-1])
    if date<start_date or date>end_date: continue
    print('processing %s'%raw_dir)
    raw_e = sorted(glob.glob('*_*E[1-9].gcf'))
    raw_n = sorted(glob.glob('*_*N[1-9].gcf'))
    raw_z = sorted(glob.glob('*_*Z[1-9].gcf'))
    for i,fnames in enumerate([raw_e, raw_n, raw_z]):
      for fname in fnames:
        print('read %s'%fname)
        try: st = read(fname)
        except: obspy.io.segy.segy.SEGYTraceReadingError; print('bad data!'); continue
        header = st[0].stats
        t0, t1 = header.starttime, header.endtime
        sta = header.station
        # set out path
        out_dir = os.path.join(sac_root, sta, date2dir(date))
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        dtime = fname.split('_')[0]
        chn = ['HHE','HHN','HHZ'][i]
        out_name = '%s.%s.%s.sac'%(sta, dtime, chn)
        out_path = os.path.join(out_dir, out_name)
        st.slice(date, date+86400).write(out_path)
        if t0 < date:
            st0 = st.slice(t0, date)
            out_dir0 = os.path.join(sac_root, sta, date2dir(date-86400))
            if not os.path.exists(out_dir0): os.makedirs(out_dir0)
            out_name0 = 'aug0.' + out_name
            out_path0 = os.path.join(out_dir0, out_name0)
            st0.write(out_path0)
        if t1 > date+86400: 
            st1 = st.slice(date+86400, t1)
            out_dir1 = os.path.join(sac_root, sta, date2dir(date+86400))
            if not os.path.exists(out_dir1): os.makedirs(out_dir1)
            out_name1 = 'aug1.' + out_name
            out_path1 = os.path.join(out_dir1, out_name1)
            st1.write(out_path1)


# 2. merge sac files in sac dir
sac_dirs = sorted(glob.glob(os.path.join(sac_root, '*/*/*/*')))
for sac_dir in sac_dirs:
    print('merge sac files in %s' %sac_dir)
    os.chdir(sac_dir)
    info = os.getcwd().split('/')
    sta = info[-4]
    date = info[-3] + info[-2] + info[-1]
    sac.merge(glob.glob('*.HHE.sac'), 'XLS.%s.%s.HHE.SAC' %(sta, date))
    sac.merge(glob.glob('*.HHN.sac'), 'XLS.%s.%s.HHN.SAC' %(sta, date))
    sac.merge(glob.glob('*.HHZ.sac'), 'XLS.%s.%s.HHZ.SAC' %(sta, date))
    # delete sac segments
    todel = glob.glob('*.sac')
    for fname in todel: os.unlink(fname)

