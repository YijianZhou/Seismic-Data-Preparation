import os, glob, shutil
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')
import subprocess
from obspy.core import *

def merge(net, sta, year, jday, chn):
    p  = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s  = "wild echo off \n"
    s += "r *.%s.* \n" %chn # SAC v101.6 or later
    s += "merge g z o a \n"
    s += "w %s.%s.%s.%s.%s.SAC \n" %(net, sta, year, jday, chn)
    s += "q \n"
    p.communicate(s.encode())

def slice_stream(fname, begin, end, ts, out_path):
    p  = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s  = "wild echo off \n"
    s += "cuterr fillz \n"
    s += "cut b %s %s \n" %(begin, end)
    s += "r %s \n" %fname
    s += "ch b 0 \n"
    s += "ch nzhour %s nzmin %s nzsec %s nzmsec %s \n" %(ts.hour,
                                                         ts.minute,
                                                         ts.second,
                                                         ts.microsecond)/1000)
    s += "ch nzyear %s nzjday %s \n" %(ts.year, ts.julday)
    s += "w %s \n" %out_path
    s += "q \n"
    p.communicate(s.encode())

def get_outdir(file_info, dir0, dt):
    sta  = file_info[7]
    year = file_info[0]
    jday = file_info[1]
    date = UTCDateTime(year+jday) + 86400*dt
    # shifted date
    yr  = str(date.year)
    mon = str(date.month).zfill(2)
    day = str(date.day).zfill(2)
    rela_dir = os.path.join(sta, yr, mon, day)
    out_dir  = os.path.join(dir0, rela_dir)
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)
    return out_dir


dst_dir0 = '/data3/XJ_SAC/YN'
src_dirs = sorted(glob.glob('/data2/yndata/2016.11.25/YN/*'))

# descend into source paths
for src_dir in src_dirs:
    os.chdir(src_dir)
    print('entering {}'.format(src_dir))
    
    # rdseed (to SAC)
    print('read seed files, convert to SAC')
    seed_files = sorted(glob.glob('*seed'))
    for seed_file in seed_files:
        subprocess.call(['rdseed', '-df', seed_file])
    
    # archive into /data3
    print('archive into data3')
    sac_files = sorted(glob.glob('*SAC'))
    for sac_file in sac_files:
        print('sac_file {}'.format(sac_file))
        file_info = sac_file.split('.')
        st = read(sac_file)
        st_len = st[0].stats.npts /100
        ts     = st[0].stats.starttime
        te     = UTCDateTime(ts.year, ts.julday) + 86400
        if st_len <= te-ts:
           out_dir = get_outdir(file_info, dst_dir0, 0)
           shutil.move(sac_file, out_dir)
        else:
           # cut out time before
           out_dir  = get_outdir(file_info, dst_dir0, 0)
           out_name = sac_file
           out_path = os.path.join(out_dir, out_name)
           slice_stream(sac_file, 0, te-ts, ts, out_path)
           # cut out time after
           out_dir = get_outdir(file_info, dst_dir0, 1)
           file_info[0] = str(te.year)
           file_info[1] = str(te.julday)
           file_info[2] = '00'
           file_info[3] = '00'
           file_info[4] = '00'
           file_info[5] = '0000'
           out_name = '.'.join(file_info)
           out_path = os.path.join(out_dir, out_name)
           slice_stream(sac_file, te-ts, st_len, te, out_path)

    # rm SAC files in data2
    todel = glob.glob('*SAC')
    for fname in todel:
        os.unlink(fname)

# merge files in data3
print('merge files in data3')
dst_dirs = sorted(glob.glob('/data3/XJ_SAC/YN/*/*/*/*')) # sta/year/month/day
for dst_dir in dst_dirs:
    print('entering {}'.format(dst_dir))
    os.chdir(dst_dir)
    todel = glob.glob('*SAC')
    sac_file  = sorted(glob.glob('*SAC'))[0]
    file_info = sac_file.split('.')
    # get out_name
    year = file_info[0]
    jday = file_info[1]
    net  = file_info[6]
    sta  = file_info[7]
    for chn in ['BHE', 'BHN', 'BHZ']:
    	merge(net, sta, year, jday, chn)
    # rm previous SAC files
    for fname in todel:
        os.unlink(fname)

