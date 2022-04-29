""" File reader
"""
import os
import glob
import numpy as np
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

# slice catalog (in struct np)
def slice_ctlg(events, ot_rng=None, lat_rng=None, lon_rng=None, dep_rng=None, mag_rng=None):
    if ot_rng: events = events[(events['ot']>=ot_rng[0])*(events['ot']<ot_rng[1])]
    if lat_rng: events = events[(events['lat']>=lat_rng[0])*(events['lat']<lat_rng[1])]
    if lon_rng: events = events[(events['lon']>=lon_rng[0])*(events['lon']<lon_rng[1])]
    if dep_rng: events = events[(events['dep']>=dep_rng[0])*(events['dep']<dep_rng[1])]
    if mag_rng: events = events[(events['mag']>=mag_rng[0])*(events['mag']<mag_rng[1])]
    return events

# slicing catalog by circle (fixed epicentral distance)
def slice_ctlg_circle(events, ref_lat, ref_lon, radius):
    cos_lat = np.cos(ref_lat*np.pi/180)
    cond = (events['lat']-ref_lat)**2 + ((events['lon']-ref_lon)*cos_lat)**2 < radius**2
    return events[cond]

# read phase file
def read_fpha(fpha):
    f=open(fpha); lines=f.readlines(); f.close()
    event_list = []
    for line in lines:
        codes = line.split(',')
        if len(codes[0])>10:
            ot = UTCDateTime(codes[0])
            lat, lon, dep, mag = [float(code) for code in codes[1:5]]
            event_loc = [ot, lat, lon, dep, mag]
            event_list.append([event_loc, {}])
        else:
            net_sta = codes[0]
            tp, ts = [UTCDateTime(code) for code in codes[1:3]]
            event_list[-1][-1][net_sta] = [tp, ts]
    return event_list

# read phase file into dict
def read_fpha_dict(fpha):
    f=open(fpha); lines=f.readlines(); f.close()
    event_dict = {}
    for line in lines:
        codes = line.split(',')
        if len(codes[0])>10:
            ot = UTCDateTime(codes[0])
            event_name = dtime2str(ot)
            lat, lon, dep, mag = [float(code) for code in codes[1:5]]
            event_loc = [ot, lat, lon, dep, mag]
            event_dict[event_name] = [event_loc, {}]
        else:
            net_sta = codes[0]
            tp = UTCDateTime(codes[1]) if codes[1]!='-1' else -1
            ts = UTCDateTime(codes[2]) if codes[2][:-1]!='-1' else -1
            event_dict[event_name][-1][net_sta] = [tp, ts]
    return event_dict

# read station file 
def read_fsta(fsta):
    f=open(fsta); lines=f.readlines(); f.close()
    sta_dict = {}
    for line in lines:
        codes = line.split(',')
        net_sta = codes[0]
        lat, lon, ele = [float(code) for code in codes[1:4]]
        sta_dict[net_sta] = [lat, lon, ele]
    return sta_dict

# read fault data (in GMT format)
def read_fault(ffault, lat_rng, lon_rng):
    faults = []
    f=open(ffault, errors='replace'); lines=f.readlines(); f.close()
    for line in lines:
        if line[0]=='>': 
            if faults==[]: faults.append([])
            elif faults[-1]!=[]: faults.append([])
        elif line[0]!='#': 
            lon, lat = [float(code) for code in line.split()]
            if lon<lon_rng[0] or lon>lon_rng[1]: continue
            if lat<lat_rng[0] or lat>lat_rng[1]: continue
            faults[-1].append([lon, lat])
    if faults[-1]==[]: faults = faults[:-1]
    for i in range(len(faults)): faults[i] = np.array(faults[i])
    return np.array(faults)

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

# UTCDateTime to string
def dtime2str(dtime):
    date = ''.join(str(dtime).split('T')[0].split('-'))
    time = ''.join(str(dtime).split('T')[1].split(':'))[0:9]
    return date + time

""" Custimized functions
"""

