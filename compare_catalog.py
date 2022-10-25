""" Compare two catalogs
1. overall recall rate of fctlg2 in ref of fctlg1
2. recall rate of large events
"""
from obspy import UTCDateTime
import numpy as np
import multiprocessing as mp
import warnings
warnings.filterwarnings("ignore")

# i/o paths
fctlg1 = 'input/ref.ctlg' # 1 - ref / target
fctlg2 = 'input/new.ctlg' # 2 - new / prediction
out_match = open('output/eg_event-match.csv','w')
out_miss = open('output/eg_event-miss.csv','w')
out_event1 = 'input/eg-ref_ctlg.npy'
out_event2 = 'input/eg-new_ctlg.npy'
# params
ot_dev = 2.5 # sec
loc_dev = 5 # km
ot_range = '20080101-20190704'
ot_range = [UTCDateTime(date) for date in ot_range.split('-')]
lat_range = [35.2, 36.3]
lon_range = [-118.2, -117.1]
mag_ranges = [[3,4],[4,5],[5,6]]
num_workers = 20

# read phase file
def read_fctlg(fctlg):
    event_list = []
    dtype = [('ot','O'),('lat','O'),('lon','O'),('dep','O'),('mag','O'),('line','O')]
    f=open(fctlg); lines=f.readlines(); f.close()
    for line in lines:
        codes = line.split(',')
        ot = UTCDateTime(codes[0])
        lat, lon, dep, mag = [float(code) for code in codes[1:5]]
        if ot_range[0]<ot<ot_range[1] \
        and lat_range[0]<lat<lat_range[1] \
        and lon_range[0]<lon<lon_range[1]: event_list.append((ot, lat, lon, dep, mag, line))
    return np.array(event_list, dtype=dtype)

def slice_ctlg(events, ot_rng=None, lat_rng=None, lon_rng=None, dep_rng=None, mag_rng=None):
    if ot_rng: events = events[(events['ot']>=ot_rng[0])*(events['ot']<ot_rng[1])]
    if lat_rng: events = events[(events['lat']>=lat_rng[0])*(events['lat']<lat_rng[1])]
    if lon_rng: events = events[(events['lon']>=lon_rng[0])*(events['lon']<lon_rng[1])]
    if dep_rng: events = events[(events['dep']>=dep_rng[0])*(events['dep']<dep_rng[1])]
    if mag_rng: events = events[(events['mag']>=mag_rng[0])*(events['mag']<mag_rng[1])]
    return events

# if first read
print('reading catalog file')
events1 = read_fctlg(fctlg1)
events2 = read_fctlg(fctlg2)
np.save(out_event1, events1)
np.save(out_event2, events2)
"""
# if saved in npy
events1 = np.load(out_event1, allow_pickle=True)
events2 = np.load(out_event2, allow_pickle=True)
"""
num_ref, num_pred = len(events1), len(events2)
print('{} events in {} (ref)'.format(num_ref, fctlg1))
print('{} events in {}'.format(num_pred, fctlg2))

def get_recall(event_ref):
    ot, lat, lon = event_ref['ot'], event_ref['lat'], event_ref['lon']
    cos_lat = np.cos(lat*np.pi/180)
    cond_ot = abs(events_pred['ot']-ot) < ot_dev
    cond_lat = 111*abs(events_pred[cond_ot]['lat']-lat) < loc_dev
    cond_lon = 111*abs(events_pred[cond_ot]['lon']-lon)*cos_lat < loc_dev
    return events_pred[cond_ot][cond_lat*cond_lon]

print('-'*20)
print('1. Overall event detection')
events_pred = events2
pool = mp.Pool(num_workers)
mp_out = pool.map_async(get_recall, events1)
pool.close()
pool.join()
num_recall = 0
for ii,event_recall in enumerate(mp_out.get()):
    if len(event_recall)==0: out_miss.write(events1[ii]['line'])
    else: out_match.write(event_recall[0]['line']); num_recall += 1
print('recall / target num: {} / {} | recall rate: {:.2f}%'.format(num_recall, num_ref, 100*num_recall/num_ref))
print('num new: %s'%(num_pred-num_recall))
print('-'*20)
print('2. Large event detection')
for mag_range in mag_ranges:
    print('magnitude range: %s - %s'%(mag_range[0], mag_range[1]))
    events_ref = slice_ctlg(events1.copy(), mag_rng=mag_range)
    num_ref, num_recall = len(events_ref), 0
    if num_ref==0: continue
    for event_ref in events_ref:
        event_recall = get_recall(event_ref)
        if len(event_recall)>0: num_recall+=1
    print('recall / target num: {} / {} | recall rate: {:.2f}%'.format(num_recall, num_ref, 100*num_recall/num_ref))
out_match.close()
out_miss.close()
