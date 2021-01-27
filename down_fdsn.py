import os, sys
sys.path.append('/home/zhouyj/software/data_prep')
import obspy
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
import multiprocessing as mp
from reader import dtime2str
import time
import signal

# i/o paths
fsta = 'output/station_cascadia_pnsn.csv'
data_root = '/data3/Cascadia_PNSN'
fbad = open('output/bad_cascadia_path.dat','w')
# down params
client = Client("IRIS")
time_range = '20180301-20180401'
start_date, end_date = [UTCDateTime(date) for date in time_range.split('-')]
num_days = int((end_date - start_date) / 86400) + 1
# read fsta
f=open(fsta); lines=f.readlines(); f.close()
net_sta_list = [line.split(',')[0].split('.') for line in lines]

for day_i in range(num_days):
  for (net,sta) in net_sta_list:
    t0 = start_date + 86400*day_i
    t1 = start_date + 86400*(day_i+1)
    print(net, sta, t0, t1)
    try:
        st = client.get_waveforms(net, sta, "*", "*", t0, t1)
        print(net, sta, st[0].stats["starttime"])
        dtime = dtime2str(t0)
        msd_name = '.'.join([net,sta,dtime,'mseed'])
        msd_dir = os.path.join(data_root,net,sta)
        out_path = os.path.join(msd_dir, msd_name)
        if not os.path.exists(msd_dir): os.makedirs(msd_dir)
        st.write(out_path, format="MSEED")
    except:
        print('no data')
        fbad.write('{},{},{}\n'.format(net,sta,t0))
fbad.close()
