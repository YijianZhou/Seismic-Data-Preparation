# preprocess of XLS reftek data in /data2
# Yijian Zhou 2018-03-06

import os, glob, subprocess
from obspy.core import *
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

dst_dir0 = '/data3/XJ_SAC/XLS'
src_dirs = sorted(glob.glob('/data2/yndata/reftek/*/AB*/1'))

#decsend into src_dirs
for src_dir in src_dirs:
    print('entering {}'.format(src_dir))
    os.chdir(src_dir)
    
    # scream data are arranged by day
    msd_files = glob.glob("*.msd")
    for msd_file in msd_files:
        subprocess.call(['mseed2sac', msd_file])
    
    # make dictonary
    sets = {}
    sac_files = glob.glob('*.SAC')
    todel = sac_files
    for sac_file in sac_files:
        net, sta, _, chn, _, year, jday, time, _ = sac_file.split('.')
        key = '.'.join([sta, year, jday, chn])
        if key not in sets:
           sets[key]  = 1
        else:
           sets[key] += 1
        
    # merge sac files        
    for key, value in sets.items():
        p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
        s = "wild echo off \n"  
        print("merge %s: %d traces" %(key, value))
        sta, year, jday, chn = key.split('.')
        # get out_dir
        date = UTCDateTime(year+jday)
        mon  = str(date.month).zfill(2)
        day  = str(date.day  ).zfill(2)
        out_dir  = os.path.join(dst_dir0, sta, year, mon, day)
        out_name = os.path.join(out_dir, 'XLS.%s.SAC'%key)
        if not os.path.exists(out_dir):
           os.makedirs(out_dir)
        tmp = '*.%s.*.%s.D.%s.%s.*.SAC'%(sta, chn, year, jday)
        traces = sorted(glob.glob(tmp))
        # for trace number >1000
        if value<=1000:
           s += "r *.%s.*.%s.D.%s.%s.*.SAC \n" %(sta, chn, year, jday) # SAC v101.6 or later
           s += "merge g z o a \n"
           s += "w %s \n" %out_name # renaming
        else:
           num = int(len(traces)/999) +1
           for i in range(num):
               if i<num-1: trs = traces[i*999:(i+1)*999]
               else:       trs = traces[i*999:len(traces)]
               s += "r tmp.sac \n"
               for tr in trs: s += "r more %s \n" %tr
               s += "merge g z o a \n"
               if i<num-1: s += "w tmp.sac \n"
               else:       s += "w %s \n" %out_name # renaming
        if os.path.exists('tmp.sac'):
           os.unlink('tmp.sac')
        s += "q \n"
        p.communicate(s.encode())
        
    # rm original sac files
    for fname in todel:
        os.unlink(fname)

