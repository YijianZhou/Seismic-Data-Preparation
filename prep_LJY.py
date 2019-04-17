import os, glob
import sys
sys.path.append('/home/zhouyj/Documents/mycode')
from obspy import read, UTCDateTime
import sac

def get_outpath(root_dir, net, sta, chn, ts):
    out_dir = os.path.join(root_dir, net, sta,
                           str(ts.year),
                           str(ts.month).zfill(2),
                           str(ts.day).zfill(2))
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)
    fname = '.'.join([net, sta,
                      str(ts.year).zfill(4),
                      str(ts.julday).zfill(3),
                      ''.join([str(ts.hour).zfill(2),
                               str(ts.minute).zfill(2),
                               str(ts.second).zfill(2)]),
                      chn, 'SAC'])
    return os.path.join(out_dir, fname)


dst_root = '/data/LJY_SAC/'
src_dirs = sorted(glob.glob('/data/LJY_raw/*/*')) # net/sta

# 1. mseed2sac + mv to dst_dir
for src_dir in src_dirs:
    print('processing {}'.format(src_dir))
    os.chdir(src_dir)

    # msd2sac
    print('msd2sac for all mseed files')
    msd_files = glob.glob('E00*')
    for msd_file in msd_files:
      if msd_file.split('.')[-1] != 'LOG':
        sac.mseed2sac(msd_file)

    # cut sac files
    sac_files = glob.glob('*.SAC')
    for sac_file in sac_files:
        _, net0, _, chn, _, _, _, _, _ = sac_file.split('.')
        net = 'LJ'+net0[1:3]
        sta = net0[3:5]
        st = read(sac_file)
        ts = st[0].stats.starttime
        te = st[0].stats.endtime
        t0 = UTCDateTime(ts.date)+86400
        tn = UTCDateTime(te.date)
        days = int((tn-t0)/86400)
        print('archving sac_file {}, from {} to {}'.\
              format(sac_file, ts, te))

        # if in one day
        if days<0:
            out_path = get_outpath(dst_root, net, sta, chn, ts)
            os.rename(sac_file, out_path)

        # head + body(days) + tail
        else:

            # cut head (before t0)
            out_path = get_outpath(dst_root, net, sta, chn, ts)
            sac.cut(sac_file, 0, t0-ts, out_path)

            # cut body (days)
            for nd in range(days):
                begin = nd*86400 + (t0-ts)
                end = begin + 86400
                ti = t0 + nd*86400
                out_path = get_outpath(dst_root, net, sta, chn, ti)
                sac.cut(sac_file, begin, end, out_path)

            # cut tail (after tn)
            out_path = get_outpath(dst_root, net, sta, chn, tn)
            sac.cut(sac_file, tn-ts, te-ts, out_path)

    todel = glob.glob('*.SAC')
    for fname in todel:
        os.unlink(fname)


# 2. merge sac files in dst_dir
dst_dirs = glob.glob(os.path.join(dst_root, '*/*/*/*/*')) # net/sta/year/month/day
for dst_dir in dst_dirs:
    os.chdir(dst_dir)
    sac_files = glob.glob('*.SAC')
    todel = sac_files
    print('merge streams: {}'.format(dst_dir))

    # merge
    for chn in ['BHE','BHN','BHZ']:
        tomerge = glob.glob("*.%s.*" %chn)
        net, sta, year, jday, time, chn, _ = tomerge[0].split('.')
        fname = "%s.%s.%s.%s.%s.SAC" %(net, sta, year, jday, chn)
        sac.merge(tomerge, fname)

    for fname in todel:
        if os.path.exists(fname): os.unlink(fname)

