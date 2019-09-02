# preprocess of XLS scream data in /data2
# First version by Yijian Zhou on 17.4.9.
# modified 2018-03-05

import os, glob, subprocess
from obspy.core import *
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

dst_dir0 = '/data3/XJ_SAC/XLS'
src_dirs = sorted(glob.glob('/data2/yndata/scream/*'))

#decsend into src_dirs
for src_dir in src_dirs:
    print('entering {}'.format(src_dir))
    os.chdir(src_dir)
    
    # scream data are arranged by day
    chn_Es = glob.glob("*e2.msd")
    chn_Ns = glob.glob("*n2.msd")
    chn_Zs = glob.glob("*z2.msd")   
    for chn_E in chn_Es:
        subprocess.call(['mseed2sac', chn_E])
    for chn_N in chn_Ns:
        subprocess.call(['mseed2sac', chn_N])
    for chn_Z in chn_Zs:
        subprocess.call(['mseed2sac', chn_Z])
    
    sets = {}
    sac_files = glob.glob('.*.SAC')
    todel = sac_files
    for sac_file in sac_files:
        _, sta, _, chn, _, year, jday, time, _ = sac_file.split('.')
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
        tmp = '.%s..%s.D.%s.%s.*.SAC'%(sta, chn, year, jday)
        traces = sorted(glob.glob(tmp))
        # for trace number >1000
        if value<=1000:
           s += "r .%s..%s.D.%s.%s.*.SAC \n" %(sta, chn, year, jday) # SAC v101.6 or later
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

