""" Compare two phase files
1. event detection rate of 2 in 1
2. phase detection rate of 2 in 1
3. phase picking precison (fout for dt hist)
"""
from obspy import UTCDateTime
import numpy as np
import multiprocessing as mp
import warnings
warnings.filterwarnings("ignore")

# i/o paths
fpha1 = 'input/reference.pha' # 1 - ref / target
fpha2 = 'input/new.pha' # 2 - new / pred
fout = open('output/example_phase-compare.csv','w')
out_event1 = 'input/eg-ref_pha.npy'
out_event2 = 'input/eg-new_pha.npy'
ctlg_names = ['Reference','New']
# params
ot_dev = 3 # sec
ot_range = '20190704-20190717'
ot_range = [UTCDateTime(date) for date in ot_range.split('-')]
lat_range = [35.45, 36.05]
lon_range = [-117.85, -117.25]
num_workers = 10

# read phase file
def read_fpha(fpha):
    f=open(fpha); lines=f.readlines(); f.close()
    event_list = []
    dtype = [('ot','O'),('line','O'),('picks','O')]
    for line in lines:
        codes = line.split(',')
        if len(codes[0])>10:
            to_add = True
            ot = UTCDateTime(codes[0])
            lat, lon, dep, mag = [float(code) for code in codes[1:5]]
            if not ot_range[0]<ot<ot_range[1] \
            and lat_range[0]<lat<lat_range[1] \
            and lon_range[0]<lon<lon_range[1]: to_add = False; continue
            event_list.append((ot, line, {}))
        else:
            if not to_add: continue
            sta = codes[0]
            tp = UTCDateTime(codes[1])
            ts = UTCDateTime(codes[2])
            event_list[-1][-1][sta] = [tp, ts]
    return np.array(event_list, dtype=dtype)

print('reading phase file')

# if first read
event_list1 = read_fpha(fpha1)
event_list2 = read_fpha(fpha2)
np.save(out_event1, event_list1)
np.save(out_event2, event_list2)
"""
# if saved in npy
event_list1 = np.load(out_event1, allow_pickle=True)
event_list2 = np.load(out_event2, allow_pickle=True)
"""
num_event1, num_event2 = len(event_list1), len(event_list2)
print('{} events in {}'.format(num_event1, ctlg_names[0]))
print('{} events in {}'.format(num_event2, ctlg_names[1]))

# 1. event det rate
def get_recall(ot2):
    event1 = event_list1[abs(event_list1['ot'] - ot2) < ot_dev]
    return event1

print('getting recalled events')
pool = mp.Pool(num_workers)
mp_out = pool.map_async(get_recall, event_list2['ot'])
pool.close()
pool.join()
event_recall, pha_recall = 0, 0
num_pha1, num_pha2 = 0, 0 
print('writing recalled events & picks')
for i,event1 in enumerate(mp_out.get()):
    if len(event1)==0: continue
    event_recall += 1
    event1 = event1[0]
    event2 = event_list2[i]
    fout.write(event1['line'])
    # pha det & pick
    picks2 = event2['picks']
    picks1 = event1['picks']
    num_pha1 += len(picks1)
    num_pha2 += len(picks2)
    recall_sta = [sta for sta in picks2.keys() if sta in picks1.keys()]
    pha_recall += len(recall_sta)
    for sta in recall_sta:
        tp1, ts1 = picks1[sta]
        tp2, ts2 = picks2[sta]
        fout.write('{},{},{},{},{}\n'.format(sta, tp1, ts1, tp2, ts2))

print('-'*20)
print('1. Event detection accuracy')
print('recall num: {} | recall rate: {:.2f}%'.format(event_recall, 100*(event_recall / num_event1)))
print('num new: %s'%(num_event2-event_recall))
print('-'*20)
print('2. Phase detection accuracy (for recalled events)')
print('recall num: {} | recalll rate {:.2f}%'.format(pha_recall, 100*pha_recall/num_pha2))
print('num new: %s'%(num_pha2-pha_recall))
fout.close()
