""" Download FDSN data with obspy MassDownloader
"""
import os
from obspy import UTCDateTime
from obspy.clients.fdsn.header import URL_MAPPINGS
URL_MAPPINGS['NCEDC'] = "https://service.ncedc.org"
from obspy.clients.fdsn.mass_downloader import RectangularDomain, Restrictions, MassDownloader
import numpy as np

# i/o paths
data_root = '/data/Example_raw'
sta_dir = 'output/eg_stations'
fsta = 'output/station_eg.csv'
# down params
providers = ['NCEDC', 'IRIS', 'SCEDC', 'USGS']
chn_codes = [['HH*','EH*','BH*','HN*'],['HH*','EH*','BH*']][1]
loc_codes = [["", "00", "01"],["*"]][1]
num_workers = 3
start_date, end_date = UTCDateTime('20200101'), UTCDateTime('20250101')
lat_rng = [34.15,36.8]
lon_rng = [-121.4,-117.5]
num_day = int((end_date - start_date) / 86400) 
print('data range:')
print('latitude range: %s'%(lat_rng))
print('longitude range: %s'%(lon_rng))
print('time range: %s'%[start_date, end_date])

f=open(fsta); lines=f.readlines(); f.close()
sta_list = [line.split(',')[0] for line in lines]
stations_str = ','.join(np.unique([net_sta.split('.')[1] for net_sta in sta_list]))
networks_str = ','.join(np.unique([net_sta.split('.')[0] for net_sta in sta_list]))

domain = RectangularDomain(minlatitude=lat_rng[0], maxlatitude=lat_rng[1],
                           minlongitude=lon_rng[0], maxlongitude=lon_rng[1])
mdl = MassDownloader(providers=providers)

for day_idx in range(num_day):
    t0 = start_date + 86400*day_idx
    t1 = start_date + 86400*(day_idx+1)
    print('downloading %s'%t0)
    # 1. set domain & restrict
    restrict = Restrictions(
        starttime=t0, endtime=t1,
        network=networks_str, station=stations_str, 
        reject_channels_with_gaps=False,
        minimum_length=0.0,
        minimum_interstation_distance_in_m=10,
        channel_priorities=chn_codes,
        location_priorities=loc_codes)

    # 2. set storage
    out_dir = os.path.join(data_root, ''.join(str(t0.date).split('-')))
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    # 3. start download
    #mdl = MassDownloader(providers=providers)
    try:
        mdl.download(domain, restrict,
          threads_per_client=num_workers, mseed_storage=out_dir,
          stationxml_storage=sta_dir)
    except:
        continue

