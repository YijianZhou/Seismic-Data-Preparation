""" Signal processing library
"""
import numpy as np
from obspy import UTCDateTime
from scipy.signal import correlate

# preprocess obspy stream
def preprocess(stream, samp_rate, freq_band, max_gap=5.):
    # time alignment
    start_time = max([trace.stats.starttime for trace in stream])
    end_time = min([trace.stats.endtime for trace in stream])
    if start_time>end_time: print('bad data!'); return []
    st = stream.slice(start_time, end_time)
    # remove nan & inf
    for ii in range(len(st)):
        st[ii].data[np.isnan(st[ii].data)] = 0
        st[ii].data[np.isinf(st[ii].data)] = 0
    # remove data gap
    max_gap_npts = int(max_gap*samp_rate)
    for tr in st:
        npts = len(tr.data)
        data_diff = np.diff(tr.data)
        gap_idx = np.where(data_diff==0)[0]
        gap_list = np.split(gap_idx, np.where(np.diff(gap_idx)!=1)[0] + 1)
        gap_list = [gap for gap in gap_list if len(gap)>=10]
        num_gap = len(gap_list)
        for ii,gap in enumerate(gap_list):
            idx0, idx1 = max(0, gap[0]-1), min(npts-1, gap[-1]+1)
            if ii<num_gap-1: idx2 = min(idx1+(idx1-idx0), idx1+max_gap_npts, gap_list[ii+1][0])
            else: idx2 = min(idx1+(idx1-idx0), idx1+max_gap_npts, npts-1)
            if idx1==idx2: continue
            if idx2==idx1+(idx1-idx0): tr.data[idx0:idx1] = tr.data[idx1:idx2]
            else:
                num_tile = int(np.ceil((idx1-idx0)/(idx2-idx1)))
                tr.data[idx0:idx1] = np.tile(tr.data[idx1:idx2], num_tile)[0:idx1-idx0]
    # resample 
    st = st.detrend('demean').detrend('linear').taper(max_percentage=0.05, max_length=5.)
    org_rate = st[0].stats.sampling_rate
    if org_rate!=samp_rate: st = st.resample(samp_rate)
    # filter
    freq_min, freq_max = freq_band
    if freq_min and freq_max:
        return st.filter('bandpass', freqmin=freq_min, freqmax=freq_max)
    elif not freq_max and freq_min:
        return st.filter('highpass', freq=freq_min)
    elif not freq_min and freq_max:
        return st.filter('lowpass', freq=freq_max)
    else:
        print('filter type not supported!'); return []

# change sac header: ref time
def sac_ch_time(st):
    for tr in st:
        if not 'sac' in tr.stats: continue
        t0 = tr.stats.starttime
        tr.stats.sac.nzyear = t0.year
        tr.stats.sac.nzjday = t0.julday
        tr.stats.sac.nzhour = t0.hour
        tr.stats.sac.nzmin = t0.minute
        tr.stats.sac.nzsec = t0.second
        tr.stats.sac.nzmsec = int(t0.microsecond / 1e3)
    return st

# calc epicentral distance in km
def calc_dist_km(lat, lon):
    cos_lat = np.cos(np.mean(lat) * np.pi / 180)
    dx = cos_lat * (lon[1] - lon[0])
    dy = lat[1] - lat[0]
    return 111*(dx**2 + dy**2)**0.5

# calc cross-correlation function (normalized)
def calc_cc(data, temp, norm_data=None, norm_temp=None):
    ntemp, ndata = len(temp), len(data)
    if ntemp>ndata: return [0]
    if not norm_temp:
        norm_temp = np.sqrt(np.sum(temp**2))
    if not norm_data:
        data_cum = np.cumsum(data**2)
        norm_data = np.sqrt(data_cum[ntemp:] - data_cum[:-ntemp])
    cc = correlate(data, temp, mode='valid')[1:]
    cc /= norm_data * norm_temp
    cc[np.isinf(cc)] = 0.
    cc[np.isnan(cc)] = 0.
    return cc

# calc azm & back-azm, given [evt, sta] lat & lon
def calc_azm_deg(lat, lon):
    cos_lat = np.cos(np.mean(lat) * np.pi / 180)
    dx = cos_lat * (lon[1] - lon[0])
    dy = lat[1] - lat[0]
    azm = np.arctan(dx/dy) * 180 / np.pi
    if dx>0 and azm<0: azm += 180
    elif dx<0 and azm<0: azm += 360
    elif dx<0 and azm>0: azm += 180
    if azm<180: baz = azm + 180
    else:       baz = azm - 180
    return azm, baz