# preprocess of XLS reftek data in /data2
# Yijian Zhou 2018-03-06

import os, glob, subprocess
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
           s += "w %s.%s.%s.%s.%s.sac \n" %(sta, year, jday ,time, chn)
    s += "q \n"
    p.communicate(s.encode())
    # rm merged traces
    for fname in sac_list:
        os.unlink(fname)
    if  os.path.exists('tmp.sac'):
        os.unlink('tmp.sac')

# msd dirs    
dst_dir0 = '/data3/XJ_SAC/XLS'
src_dirs = sorted(glob.glob('/data2/yndata/reftek/*/AB*/1'))
#src_dirs = sorted(glob.glob('/data2/yndata/reftek/2016245/AB95/1'))

#decsend into src_dirs
for src_dir in src_dirs:
    print('entering {}'.format(src_dir))
    os.chdir(src_dir)
    sta0 = src_dir.split('/')[-2]
    date = src_dir.split('/')[-3]
    year0 = date[0:4]
    jday0 = date[4:7]
    # get out_dir
    date = UTCDateTime(date)
    mon  = str(date.month).zfill(2)
    day  = str(date.day  ).zfill(2)
    out_dir  = os.path.join(dst_dir0, sta0, year0, mon, day)
    if not os.path.exists(out_dir):
       os.makedirs(out_dir)
    
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
               
    # merge merged traces
    for chn in ['001', '002', '003']:
        out_name = '.'.join(['XLS', sta0, year0, jday0, chn, 'SAC'])
        out_path = os.path.join(out_dir, out_name)
        p  = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
        s  = "wild echo off \n"
        s += "r *.%s.sac \n" %chn
        s += "merge g z o a \n"
        s += "w %s \n" %out_path
        s += "q \n"
        p.communicate(s.encode())
    
    # rm merged traces
    for fname in glob.glob('*.sac'):
        os.unlink(fname)
