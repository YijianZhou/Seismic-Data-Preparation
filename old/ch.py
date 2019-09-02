import os, glob
import subprocess
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

# station positions
sta_lst={}
tmp = open('station_ZSY'); lines = tmp.readlines(); tmp.close()
for line in lines:
  sta, lon, lat, ele = line.split('\t')
  ele = ele.split('\n')[0]
  loc = '/'.join([lat, lon, ele])
  sta_lst[sta] = loc

streams = sorted(glob.glob('/data3/XJ_SAC/ZSY/*/*/*/*/*SAC'))
p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
s = "wild echo off \n"
for stream in streams:
    print('processing {}'.format(stream))
    net, sta, yr, jday, chn, _ = stream.split('.')
    loc = sta_lst[sta]
    lat, lon, ele = loc.split('/')
    s += "rh %s \n" %(stream)
    s += "ch stlo %s stla %s \n" %(lon, lat)
    s += "ch stel %s \n" %(ele)
    s += "ch knetwk ZSY \n"
    s += "wh \n"
s += "q \n"
p.communicate(s.encode())
