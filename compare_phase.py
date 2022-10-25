""" Compare two phase files
1. event detection rate of fpha2 in ref of fpha1
2. phase detection rate of fpha2 in ref of fpha1
3. phase picking precison (fout for dt hist)
"""
from obspy import UTCDateTime
import numpy as np
import multiprocessing as mp
import warnings
warnings.filterwarnings("ignore")

# i/o paths
fpha1 = 'input/ref.pha' # 1 - target / ref
fpha2 = 'input/new.pha' # 2 - prediction
out_match = open('output/eg_phase-match.csv','w')
out_miss = open('output/eg_phase-miss.csv','w')
out_event1 = 'input/eg-ref_pha.npy'
out_event2 = 'input/eg-new_pha.npy'
# params
ot_dev = 2.5 # sec
loc_dev = 5 # km
ot_range = '20190704-20190717'
ot_range = [UTCDateTime(date) for date in ot_range.split('-')]
lat_range = [35.45, 36.05]
lon_range = [-117.85, -117.25]
num_workers = 10

# read phase file
def read_fpha(fpha):
    f=open(fpha); lines=f.readlines(); f.close()
    event_list = []
    dtype = [('ot','O'),('lat','O'),('lon','O'),('line','O'),('picks','O')]
    for line in lines:
        codes = line.split(',')
        if len(codes[0])>10:
            to_add = True
            ot = UTCDateTime(codes[0])
            lat, lon, dep, mag = [float(code) for code in codes[1:5]]
            if not ot_range[0]<ot<ot_range[1] \
            and lat_range[0]<lat<lat_range[1] \
            and lon_range[0]<lon<lon_range[1]: to_add = False; continue
            event_list.append((ot, lat, lon, line, {}))
        else:
            if not to_add: continue
            sta = codes[0]
            tp = UTCDateTime(codes[1])
            ts = UTCDateTime(codes[2])
            event_list[-1][-1][sta] = [tp, ts]
    return np.array(event_list, dtype=dtype)


# if first read
print('reading phase file')
events1 = read_fpha(fpha1)
events2 = read_fpha(fpha2)
np.save(out_event1, events1)
np.save(out_event2, events2)
"""
# if saved in npy
events1 = np.load(out_event1, allow_pickle=True)
events2 = np.load(out_event2, allow_pickle=True)
"""
num_event1, num_event2 = len(events1), len(events2)
print('{} events in {} (ref)'.format(num_event1, fpha1))
print('{} events in {}'.format(num_event2, fpha2))

# 1. event det rate
def get_recall(event_ref):
    ot, lat, lon = event_ref['ot'], event_ref['lat'], event_ref['lon']
    cos_lat = np.cos(lat*np.pi/180)
    cond_ot = abs(events_pred['ot']-ot) < ot_dev
    cond_lat = 111*abs(events_pred[cond_ot]['lat']-lat) < loc_dev
    cond_lon = 111*abs(events_pred[cond_ot]['lon']-lon)*cos_lat < loc_dev
    return events_pred[cond_ot][cond_lat*cond_lon]

print('getting recalled events')
events_pred = event2
pool = mp.Pool(num_workers)
mp_out = pool.map_async(get_recall, events1)
pool.close()
pool.join()
num_evt_recall, num_pha_recall = 0, 0
num_pha1, num_pha2 = 0, 0 
print('writing recalled events & picks')
for ii,event_recall in enumerate(mp_out.get()):
    if len(event_recall)==0: continue
    num_evt_recall += 1
    event1 = events1[ii]
    event2 = event_recall[0] #TODO, multi-recall
    # find matched station 
    picks1 = event1['picks']
    picks2 = event2['picks']
    num_pha1 += len(picks1)
    num_pha2 += len(picks2)
    sta_recall = [sta for sta in picks1.keys() if sta in picks2.keys()]
    sta_miss = [sta for sta in picks1.keys() if sta not in picks2.keys()]
    num_pha_recall += len(sta_recall)
    # write match & miss
    out_match.write(event1['line'])
    out_match.write(event2['line'])
    for sta in sta_recall:
        tp1, ts1 = picks1[sta]
        tp2, ts2 = picks2[sta]
        out_match.write('{},{},{},{},{}\n'.format(sta, tp1, ts1, tp2, ts2))
    if len(sta_miss)==0: continue
    out_miss.write(event2['line'])
    for sta in sta_miss:
        tp2, ts2 = picks2[sta]
        out_miss.write('{},{},{}\n'.format(sta, tp2, ts2))

print('-'*20)
print('1. Event detection accuracy')
print('recall / target num: {} / {} | recall rate: {:.2f}%'.format(num_evt_recall, num_event1, 100*num_evt_recall/num_event1))
print('num new: %s'%(num_event2-num_evt_recall))
print('-'*20)
print('2. Phase detection accuracy (for recalled events)')
print('recall / target num: {} / {} | recall rate {:.2f}%'.format(num_pha_recall, num_pha1, 100*num_pha_recall/num_pha1))
print('num new: %s'%(num_pha2-num_pha_recall))
out_match.close()
out_miss.close()
