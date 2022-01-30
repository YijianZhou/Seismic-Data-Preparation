""" File reader
"""
import os
import glob
from obspy import UTCDateTime

# read catalog file
def read_fctlg(fctlg):
    f=open(fctlg); lines=f.readlines(); f.close()
    event_list = []
    for line in lines:
        codes = line.split(',')
        ot = UTCDateTime(codes[0])
        lat, lon, dep, mag = [float(code) for code in codes[1:5]]
        event_list.append([ot, lat, lon, dep, mag])
    return event_list

# read catalog into an np.array
def read_fctlg_np(fctlg):
    dtype = [('ot','O'),('lat','O'),('lon','O'),('dep','O'),('mag','O')]
    f=open(fctlg); lines=f.readlines(); f.close()
    event_list = []
    for line in lines:
        codes = line.split(',')
        ot = UTCDateTime(codes[0])
        lat, lon, dep, mag = [float(code) for code in codes[1:5]]
        event_list.append((ot, lat, lon, dep, mag))
    return np.array(event_list, dtype=dtype)

def slice_ctlg(events, ot_rng=None, lat_rng=None, lon_rng=None, dep_rng=None, mag_rng=None):
    if ot_rng: events = events[(events['ot']>=ot_rng[0])*(events['ot']<ot_rng[1])]
    if lat_rng: events = events[(events['lat']>=lat_rng[0])*(events['lat']<lat_rng[1])]
    if lon_rng: events = events[(events['lon']>=lon_rng[0])*(events['lon']<lon_rng[1])]
    if dep_rng: events = events[(events['dep']>=dep_rng[0])*(events['dep']<dep_rng[1])]
    if mag_rng: events = events[(events['mag']>=mag_rng[0])*(events['mag']<mag_rng[1])]
    return events

# read phase file
def read_fpha(fpha):
    f=open(fpha); lines=f.readlines(); f.close()
    pha_list = []
    for line in lines:
        codes = line.split(',')
        if len(codes[0])>10:
            ot = UTCDateTime(codes[0])
            lat, lon, dep, mag = [float(code) for code in codes[1:5]]
            event_loc = [ot, lat, lon, dep, mag]
            pha_list.append([event_loc, {}])
        else:
            net_sta = codes[0]
            tp, ts = [UTCDateTime(code) for code in codes[1:3]]
            pha_list[-1][-1][net_sta] = [tp, ts]
    return pha_list

# read station file in PAL format
def read_pal_fsta(fsta):
    print('reading %s'%fsta)
    f=open(fsta); lines=f.readlines(); f.close()
    sta_dict = {}
    for line in lines:
        codes = line.split(',')
        net_sta = codes[0]
        lat, lon, ele, gain = [float(code) for code in codes[1:5]]
        sta_dict[net_sta] = [lat, lon, ele, gain]
    return sta_dict

# read station file 
def read_fsta(fsta):
    print('reading %s'%fsta)
    f=open(fsta); lines=f.readlines(); f.close()
    sta_dict = {}
    for line in lines:
        codes = line.split(',')
        net_sta = codes[0]
        lat, lon, ele = [float(code) for code in codes[1:4]]
        sta_dict[net_sta] = [lat, lon, ele]
    return sta_dict

# get data dict, given path structure
def get_data_dict(date, data_dir):
    # get data paths
    data_dict = {}
    date_dir = '{:0>4}{:0>2}{:0>2}'.format(date.year, date.month, date.day)
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

