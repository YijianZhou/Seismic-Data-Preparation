import os
import glob
from obspy import UTCDateTime

# read phase file
def read_pha(fpha):
    f=open(fpha); lines=f.readlines(); f.close()
    pha_list = []
    for line in lines:
        codes = line.split(',')
        if len(codes)==5:
            ot = UTCDateTime(codes[0])
            lat, lon, dep, mag = [float(code) for code in codes[1:]]
            event_loc = [ot, lat, lon, dep, mag]
            pha_list.append([event_loc, {}])
        else:
            net_sta = '.'.join(codes[0:2])
            tp, ts = [UTCDateTime(code) for code in codes[2:4]]
            pha_list[-1][-1][net_sta] = [tp, ts]
    return pha_list


# get data dict, given path structure
def get_data_dict(date, data_dir):
    # get data paths
    data_dict = {}
    date_dir = '{:0>4}/{:0>2}/{:0>2}'.format(date.year, date.month, date.day)
    st_paths = sorted(glob.glob(os.path.join(data_dir, date_dir, '*')))
    for st_path in st_paths:
        fname = os.path.split(st_path)[-1]
        net_sta = '.'.join(fname.split('.')[0:2])
        if net_sta in data_dict: data_dict[net_sta].append(st_path)
        else: data_dict[net_sta] = [st_path]
    # drop bad sta
    todel = [net_sta for net_sta in data_dict if len(data_dict[net_sta])!=3]
    for net_sta in todel: data_dict.pop(net_sta)
    return data_dict


def dtime2str(dtime):
    date = ''.join(str(dtime).split('T')[0].split('-'))
    time = ''.join(str(dtime).split('T')[1].split(':'))[0:9]
    return date + time


""" Custimized functions
"""

def get_rc_data(date, data_dir):
    # get data paths
    data_dict = {}
    date_dir = '{:0>4}/{:0>2}/{:0>2}'.format(date.year, date.month, date.day)
    st_paths = sorted(glob.glob(os.path.join(data_dir, date_dir, '*')))
    for st_path in st_paths:
        fname = os.path.split(st_path)[-1]
        net_sta = '.'.join(fname.split('.')[1:3])
        if net_sta in data_dict: data_dict[net_sta].append(st_path)
        else: data_dict[net_sta] = [st_path]
    # drop bad sta
    todel = [net_sta for net_sta in data_dict if len(data_dict[net_sta])!=3]
    for net_sta in todel: data_dict.pop(net_sta)
    return data_dict


# read phase file
def read_rc_pha(fpha):
    f=open(fpha); lines=f.readlines(); f.close()
    pha_list = []
    for line in lines:
        codes = line.split(',')
        if len(codes[0])>14:
            ot = UTCDateTime(codes[0])
            lat, lon, dep, mag = [float(code) for code in codes[1:]]
            event_loc = [ot, lat, lon, dep, mag]
            pha_list.append([event_loc, {}])
        else:
            net_sta = codes[0]
            if codes[1]=='-1': continue
            tp = UTCDateTime(codes[1])
            ts = UTCDateTime(codes[2]) if codes[2][:-1]!='-1' else None
            pha_list[-1][-1][net_sta] = [tp, ts]
    return pha_list

