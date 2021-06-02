import os, sys, glob
sys.path.append('/home/zhouyj/software/data_prep')
import sac
from obspy import read, UTCDateTime

# i/o paths
raw_dir = '/data/SEED_raw'
seed_paths = glob.glob(os.path.join(raw_dir, '*.seed'))
sac_root = '/data/SEED_SAC'
if not os.path.exists(sac_root): os.makedirs(sac_root)


# 1. seed2sac
for seed_path in seed_paths:
    sac.seed2sac(seed_path, sac_root)


# 2. cut sac into day_dirs
raw_paths = sorted(glob.glob(os.path.join(sac_root, '*.SAC')))
for raw_path in raw_paths:
    print('cutting %s'%raw_path)
    st = read(raw_path, headonly=True)
    if len(st)!=1: print('false number of traces'); continue
    header = st[0].stats
    start_time, end_time = header.starttime, header.endtime
    nsec = end_time - start_time
    start_date = UTCDateTime(start_time.date)
    end_date = UTCDateTime(end_time.date) + 86400
    num_days = int((end_date - start_date) / 86400)
    net, sta, chn = header.network, header.station, header.channel
    for day_idx in range(num_days):
        t0 = start_date + 86400*day_idx
        t1 = start_date + 86400*(day_idx+1)
        date_code = ''.join(str(t0.date).split('-'))
        out_dir = os.path.join(sac_root, date_code)
        if not os.path.exists(out_dir): os.makedirs(out_dir)
        out_name = '%s.%s.%s.%s.sac'%(net,sta,start_time,chn)
        out_path = os.path.join(out_dir, out_name)
        b = max(0, t0 - start_time)
        e = min(nsec, t1 - start_time)
        sac.cut(raw_path, b, e, out_path)
for raw_path in raw_paths: os.unlink(raw_path)


# 3. merge sac segments
def get_sta_codes(sac_dir):
    sta_codes = []
    os.chdir(sac_dir)
    fnames = glob.glob('*.sac')
    for fname in fnames:
        codes = fname.split('.')
        net, sta = codes[0:2]
        chn = codes[-2]
        sta_code = '%s.%s.%s'%(net, sta, chn)
        if not sta_code in sta_codes: sta_codes.append(sta_code)
    return sta_codes

sac_dirs = sorted(glob.glob(os.path.join(sac_root,'*')))
for sac_dir in sac_dirs:
    if not os.path.isdir(sac_dir): continue
    print('merge sac segments: %s'%sac_dir)
    date = os.path.basename(sac_dir)
    sta_codes = get_sta_codes(sac_dir)
    for sta_code in sta_codes:
        net, sta, chn = sta_code.split('.')
        sac_paths = glob.glob(os.path.join(sac_dir,'%s.%s.*.%s.sac'%(net,sta,chn)))
        out_path = os.path.join(sac_dir,'%s.%s.%s.%s.SAC'%(net,sta,date,chn))
        sac.merge(sac_paths, out_path)
        for sac_path in sac_paths: 
            if os.path.exists(sac_path): os.unlink(sac_path)

