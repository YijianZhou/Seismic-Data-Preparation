import glob, os, shutil
from obspy.core import UTCDateTime
import subprocess
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

out_path0 = '/data3/XJ_SAC/ZSY/'
msd_paths = sorted(glob.glob('/data2/yndata/2016.11.25/B*/2016/*/*'))

# make station dictionary
sta_dic = {}
tmp = open('station_ZSY'); lines = tmp.readlines(); tmp.close()
for line in lines:
    sta, lon, lat, ele = line.split('\t')
    ele = ele.split('\n')[0]
    loc = '/'.join([lat, lon, ele])
    sta_dic[sta] = loc

# desced into raw data path
for msd_path in msd_paths:
    os.chdir(msd_path)
    print('entering {}'.format(msd_path))

    # msd2sac
    msd_files = glob.glob('*miniseed')
    if len(msd_files)==0: print('missing trace!'); continue
    for msd_file in msd_files:
        subprocess.call(['mseed2sac', msd_file])
    todel = glob.glob('*SAC')

    # merge + ch + rename (use sac)
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    for chn in ['HHE', 'HHX', 'HHN', 'HHY', 'HHZ']:
        sac_files = sorted(glob.glob('*.%s.*SAC'%chn))
        if len(sac_files)==0: continue
        net, sta, _, chn, _, year, jday, tm, _ = sac_files[0].split('.')
        if sta not in sta_dic: continue
        loc = sta_dic[sta]
        lat, lon, ele = loc.split('/')
        print('merge %s.%s.%s'%(sta, chn, jday))
        s += "r *.%s.*SAC \n" %(chn)
        s += "merge g z o a \n"
        s += "ch knetwk ZSY \n"
        s += "ch stlo %s stla %s \n" %(lon, lat)
        s += "ch stel %s \n" %ele
        s += "w ZSY.%s.%s.%s.%s.SAC \n" %(sta, year, jday, chn)
    s += "q \n"
    p.communicate(s.encode())

    for fname in todel:
        os.unlink(fname)

    # archive (mkdir + mv)
    date = UTCDateTime('%s,%s'%(year, jday))
    mon, day = str(date.month).zfill(2), str(date.day).zfill(2)
    out_path = os.path.join(out_path0, sta, year, mon, day)
    print('archive into {}'.format(out_path))
    if not os.path.exists(out_path):
       os.makedirs(out_path)
    for sac_file in glob.glob('*SAC'):
        # silently replace
#        os.rename(sac_file, os.path.join(out_path, sac_file))
        # err if file exists
        if os.path.exists(os.path.join(out_path, sac_file)):
           continue
        shutil.move(sac_file, out_path)

