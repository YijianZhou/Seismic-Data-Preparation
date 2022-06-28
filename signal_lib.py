""" Signal processing library
"""
import numpy as np
from obspy import UTCDateTime
from scipy.signal import correlate

def preprocess(stream, samp_rate, freq_band):
    # time alignment
    start_time = max([trace.stats.starttime for trace in stream])
    end_time = min([trace.stats.endtime for trace in stream])
    if start_time>end_time: print('bad data!'); return []
    st = stream.slice(start_time, end_time)
    # resample data
    org_rate = st[0].stats.sampling_rate
    if org_rate!=samp_rate: st = st.interpolate(samp_rate)
    for ii in range(3):
        st[ii].data[np.isnan(st[ii].data)] = 0
        st[ii].data[np.isinf(st[ii].data)] = 0
    # filter
    st = st.detrend('demean').detrend('linear').taper(max_percentage=0.05, max_length=10.)
    freq_min, freq_max = freq_band
    if freq_min and freq_max:
        return st.filter('bandpass', freqmin=freq_min, freqmax=freq_max)
    elif not freq_max and freq_min:
        return st.filter('highpass', freq=freq_min)
    elif not freq_min and freq_max:
        return st.filter('lowpass', freq=freq_max)
    else:
        print('filter type not supported!'); return []

def calc_dist_km(lat, lon):
    cos_lat = np.cos(np.mean(lat) * np.pi / 180)
    dx = cos_lat * (lon[1] - lon[0])
    dy = lat[1] - lat[0]
    return 111*(dx**2 + dy**2)**0.5

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

# [evt, sta]
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