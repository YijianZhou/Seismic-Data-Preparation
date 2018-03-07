# preprocess of XLS reftek data in /data2
# Yijian Zhou 2018-03-06

import os, glob, shutil
import subprocess
from obspy.core import *
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

def get_files(sac_list):
    new_files = []
    # for the same sta, sort by time
    sac_files = sorted(glob.glob('*.SAC'))
    for sac_file in sac_files:
        if sac_file not in sac_list:
           new_files.append(sac_file)
    return new_files

def add_list(sac_list, new_files):
    for new_file in new_files:
        sac_list.append(new_file)
    return sac_list

def merge_list(sac_list, sta0):
    _, sta, _, chn, _, year, jday, time, _ = sac_list[0].split('.')
    p  = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s  = "wild echo off \n"
    num = int(len(sac_list)/999) +1
    for i in range(num):
        if i<num-1: trs = sac_list[i*999:(i+1)*999]
        else      : trs = sac_list[i*999:len(sac_list)]
        s += "r tmp.sac \n"
        for tr in trs: s += "r more %s \n" %tr
        s += "merge g z o a \n"
        if i<num-1: s += "w tmp.sac \n"
        else:
           s += "ch kstnm %s \n" %sta0
           if sta[0:2]=='AB':
              s += "dec 2 \n"
              s += "dec 5 \n"
           s += "w %s.%s.%s.%s.%s.sac \n" %(sta0, year, jday ,time, chn)
    s += "q \n"
    p.communicate(s.encode())
    # rm merged traces
    for fname in sac_list:
        os.unlink(fname)
    if  os.path.exists('tmp.sac'):
        os.unlink('tmp.sac')

def get_outdir(file_info, dir0, dt):
    sta  = file_info[0]
    year = file_info[1]
    jday = file_info[2]
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
                                                         ts.microsecond/1000)
    s += "ch nzyear %s nzjday %s \n" %(ts.year, ts.julday)
    s += "w %s \n" %out_path
    s += "q \n"
    p.communicate(s.encode())

# msd dirs    
dst_dir0 = '/data3/XJ_SAC/XLS'
src_dirs = sorted(glob.glob('/data2/yndata/reftek/*/AB*/1'))
#src_dirs = sorted(glob.glob('/data2/yndata/reftek/2016245/AB95/1'))

#decsend into src_dirs
for src_dir in src_dirs:
    print('entering {}'.format(src_dir))
    os.chdir(src_dir)
    sta0 = src_dir.split('/')[-2]
    
    # for each channel
    for n in ['1','2','3']:
        msd_files = sorted(glob.glob("*_%s.msd" %n))
        for i, msd_file in enumerate(msd_files):
            subprocess.call(['mseed2sac', msd_file])
            if i==0:
               new_files = get_files([])
               sac_list  = add_list([], new_files)
               sta = new_files[0].split('.')[1]
               continue
            new_files = get_files(sac_list)
            stai = new_files[0].split('.')[1]
            if stai==sta: 
               sac_list = add_list(sac_list, new_files)
            else:
               # merge files
               merge_list(sac_list, sta0)
               sac_list = new_files
               sta = stai
            if i==len(msd_files)-1:
               merge_list(sac_list, sta0)
    
    # cut into data3
    print('cut into data3')
    for chn in ['001', '002', '003']:
        sac_files = sorted(glob.glob('*.%s.sac' %chn))
        for sac_file in sac_files:
            file_info = sac_file.split('.')
            st = read(sac_file)
            st_len = st[0].stats.npts /100
            ts     = st[0].stats.starttime
            te     = UTCDateTime(str(ts.date)) + 86400
            if st_len <= te-ts:
               out_dir = get_outdir(file_info, dst_dir0, 0)
               if os.path.exists(os.path.join(out_dir, sac_file)):
                  sac_file = '1-' + sac_file
               shutil.move(sac_file, out_dir)
               print('moved to {}/{}'.format(out_dir, sac_file))
            else:
               # cut out time before
               out_dir = get_outdir(file_info, dst_dir0, 0)
               if os.path.exists(os.path.join(out_dir, sac_file)):
                  sac_file = '1-' + sac_file
               out_name = sac_file
               out_path = os.path.join(out_dir, out_name)
               print('moved to {}'.format(out_path))
               slice_stream(sac_file, 0, te-ts, ts, out_path)
               # cut out time after
               out_dir = get_outdir(file_info, dst_dir0, 1)
               file_info[1] = str(te.year)
               file_info[2] = str(te.julday)
               file_info[3] = '000000'
               out_name = '.'.join(file_info)
               out_path = os.path.join(out_dir, out_name)
               slice_stream(sac_file, te-ts, st_len, te, out_path)
               print('moved to {}'.format(out_path))
    
    # rm merged traces
    for fname in glob.glob('*.sac'):
        os.unlink(fname)
    
# merge files in data3
print('merge files in data3')
dst_dirs = sorted(glob.glob('/data3/XJ_SAC/XLS/AB*/*/*/*'))
for dst_dir in dst_dirs:
    print('entering {}'.format(dst_dir))
    os.chdir(dst_dir)
    # check if processed
    if len(glob.glob('*sac'))==0:
       print('processed, continue')
       continue
    # get file info
    dir_info = dst_dir.split('/')
    day  = dir_info[-1]
    mon  = dir_info[-2]
    year = dir_info[-3]
    sta  = dir_info[-4]
    jday = str(UTCDateTime(year+mon+day).julday).zfill(3)
    # merge for each channel
    for chn in ['001', '002', '003']:
        out_name = '.'.join(['XLS', sta, year, jday, chn, 'SAC'])
        p  = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
        s  = "wild echo off \n"
        s += "r *.%s.sac \n" %chn
        if len(glob.glob('*.SAC'))!=0:
           s += "r *.%s.SAC \n" %chn
        s += "merge g z o a \n"
        s += "w %s \n" %out_name
        s += "q \n"
        p.communicate(s.encode())
    
    # rm merged traces
    for fname in glob.glob('*.sac'):
        os.unlink(fname)

