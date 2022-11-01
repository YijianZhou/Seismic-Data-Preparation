""" check data quality
"""
import os, sys, glob
from obspy import read, UTCDateTime

# i/o paths
data_root = '/data/Example_Data'
time_range = '20210520-20210527'
fsta = 'output/station_example.csv'
fout = open('output/example_bad_data.csv','w')

# get sta list
sta_dict = {}
f=open(fsta); lines=f.readlines(); f.close()
for line in lines:
    net_sta = line.split(',')[0]
    sta_dict[net_sta] = []
sta_list = list(sta_dict.keys())

# scan all data
start_date, end_date = [UTCDateTime(date) for date in time_range.split('-')]
num_days = (end_date.date - start_date.date).days
for day_idx in range(num_days):
    date = start_date + day_idx*86400
    date_code = '{:0>4}{:0>2}{:0>2}'.format(date.year, date.month, date.day)
    data_dir = os.path.join(data_root, date_code)
    for net_sta in sta_list:
        st_paths = glob.glob(os.path.join(data_dir, '%s.*'%net_sta))
        if len(st_paths)==0 and len(sta_dict[net_sta])==1 \
        and sta_dict[net_sta][0]<date: 
            fout.write('data_gap,%s,%s\n'%(date_code,net_sta))
            continue
        if len(st_paths)!=3 and len(st_paths)!=0:
            fout.write('miss_chn,%s,%s\n'%(date_code,net_sta))
        for st_path in st_paths:
            try: 
                st = read(st_path, headonly=True)
                npts_good = 86400*st[0].stats.sampling_rate
                if abs(st[0].stats.npts-npts_good)>2: fout.write('false_npts:%s,%s,%s\n'%(st[0].stats.npts, date_code,net_sta))
            except: fout.write('bad_data,%s,%s\n'%(date_code,net_sta))
            st_name = os.path.basename(st_path)
            net_sta = '.'.join(st_name.split('.')[0:2])
            if len(sta_dict[net_sta])==0: sta_dict[net_sta] = [date]
fout.close()
