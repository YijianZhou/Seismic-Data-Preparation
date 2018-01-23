import os, glob
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')
import subprocess
from obspy.core import *

def merge(net, sta, year, jday, chn):
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "r *.%s.*.%s.* \n" %(sta, chn) # SAC v101.6 or later
    s += "merge g z o a \n"
    s += "w %s.%s.%s.%s.%s.SAC \n" %(net, sta, year, jday, chn)
    s += "q \n"
    p.communicate(s.encode())

def get_outname(path0, kstnm, chn, ts):
    out_path = os.path.join(path0, 'PJ%s'%kstnm[1:3],
                            str(ts.year),
                            str(ts.month).zfill(2),
                            str(ts.day).zfill(2))
    if not os.path.exists(out_path):
       os.makedirs(out_path)
    fname = '.'.join(['PJ%s'%kstnm[1:3], kstnm[3:5],
                      str(ts.year).zfill(4),
                      str(ts.julday).zfill(3),
                      ''.join([str(ts.hour).zfill(2),
                               str(ts.minute).zfill(2),
                               str(ts.second).zfill(2)]),
                      chn, 'SAC'])
    return os.path.join(out_path, fname)

def slice_stream(fname, begin, end, ts, out_name):
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "cuterr fillz \n"
    s += "cut b %s %s \n" %(begin, end)
    s += "r %s \n" %fname
    s += "ch b 0 \n"
    s += "ch nzhour %s nzmin %s nzsec %s nzmsec %s \n" %(ts.hour,
                                                         ts.minute,
                                                         ts.second,
                                                         str(ts.microsecond)[0:3])
    s += "ch nzyear %s nzjday %s \n" %(ts.year, ts.julday)
    s += "w %s \n" %out_name
    s += "q \n"
    p.communicate(s.encode())

dst_path0 = '/data/JZ_SAC/'
src_paths = sorted(glob.glob('/data/JZ_raw/00*/*/*')) # net/sta/date/msd_files
for src_path in src_paths:
    print('processing {}'.format(src_path))
    os.chdir(src_path)

    # msd2sac
    print('msd2sac')
    msd_files = glob.glob('E00*')
    for msd_file in msd_files:
      if msd_file.split('.')[-1] != 'LOG':
         subprocess.call(['mseed2sac', msd_file])

    # archiving sac files
    sac_files = glob.glob('*.SAC')
    for sac_file in sac_files:
        _, kstnm, _, chn, _, year, jday, time, _ = sac_file.split('.')
        st = read(sac_file)
        ts = st[0].stats.starttime
        te = st[0].stats.endtime
        t0 = UTCDateTime(str(ts.year) + str(ts.julday+1).zfill(3))
        tn = UTCDateTime(te.year, te.month, te.day)
        days = int((tn-t0)/86400)
        print('archving sac_file {}, from {} to {}'.\
              format(sac_file, ts, te))
        if days<0:
           out_name = get_outname(dst_path0, kstnm, chn, ts)
           os.rename(sac_file, out_name)
        else:
           # cut time_win before t0
           begin = 0
           end = t0-ts
           out_name = get_outname(dst_path0, kstnm, chn, ts)
           slice_stream(sac_file, begin, end, ts, out_name)

           # cut days
           for nd in range(days):
               begin = nd*86400 + (t0-ts)
               end = begin + 86400
               ti = t0 + nd*86400
               out_name = get_outname(dst_path0, kstnm, chn, ti)
               slice_stream(sac_file, begin, end, ti, out_name)

           # cut time_win after tn
           begin = tn-ts
           end = te-ts
           out_name = get_outname(dst_path0, kstnm, chn, tn)
           slice_stream(sac_file, begin, end, tn, out_name)

    todel = glob.glob('*.SAC')
    for fname in todel:
        os.unlink(fname)

dst_paths = glob.glob(os.path.join(dst_path0, '*/*/*/*')) # net/year/month/day
for dst_path in dst_paths:
    os.chdir(dst_path)
    sac_files = glob.glob('*.SAC')
    todel = sac_files
    print('merge streams')
    # make dictionary
    sets = {}
    for sac_file in sac_files:
        net, sta, year, jday, time, chn, _ = sac_file.split('.')
        key = '.'.join([net, sta, year, jday, chn])
        if key not in sets:
           sets[key] = 1
        else:
           sets[key] += 1

    # merge
    for key, value in sets.items():
        net, sta, year, jday, chn = key.split('.')
        merge(net, sta, year, jday, chn)

    for fname in todel:
        os.unlink(fname)
