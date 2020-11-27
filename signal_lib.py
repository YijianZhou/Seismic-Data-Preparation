""" Signal processing library
"""
import numpy as np
from obspy import UTCDateTime

def preprocess(stream, samp_rate, freq_band):
    # time alignment
    start_time = max([trace.stats.starttime for trace in stream])
    end_time = min([trace.stats.endtime for trace in stream])
    if start_time>end_time: print('bad data!'); return []
    st = stream.slice(start_time, end_time)
    # resample data
    org_rate = int(st[0].stats.sampling_rate)
    rate = np.gcd(org_rate, samp_rate)
    if rate==1: print('warning: bad sampling rate!'); return []
    decim_factor = int(org_rate / rate)
    resamp_factor = int(samp_rate / rate)
    if decim_factor!=1: st = st.decimate(decim_factor)
    if resamp_factor!=1: st = st.interpolate(samp_rate)
    # filter
    st = st.detrend('demean').detrend('linear').taper(max_percentage=0.05, max_length=10.)
    flt_type, freq_rng = freq_band
    if flt_type=='highpass':
        return st.filter(flt_type, freq=freq_rng).normalize()
    if flt_type=='bandpass':
        return st.filter(flt_type, freqmin=freq_rng[0], freqmax=freq_rng[1]).normalize()




