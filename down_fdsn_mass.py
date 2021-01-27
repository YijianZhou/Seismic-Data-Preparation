import os
import obspy
from obspy import UTCDateTime
from obspy.clients.fdsn.mass_downloader import RectangularDomain, Restrictions, MassDownloader
import time

# i/o paths
fsta = 'input/station_nepal.fullfed'
f=open(fsta); lines=f.readlines(); f.close()
data_root = '/data1/Gorkha_raw'
sta_dir = 'output/gorkha_stations'
# down params
providers = ["IRIS"]
chn_codes = ['HH*']
loc_codes = ["", "00", "01"]
num_workers = 10

# get data range
net_codes = []
lat, lon = [], []
start_date, end_date = [], []
for line in lines:
    codes = line.split('|')
    if codes[0] not in net_codes: net_codes.append(codes[0])
    lat.append(float(codes[4]))
    lon.append(float(codes[5]))
    start_date.append(UTCDateTime(UTCDateTime(codes[-2]).date))
    end_date.append(UTCDateTime(UTCDateTime(codes[-1]).date))

lat_rng = [min(lat)-0.5, max(lat)+0.5]
lon_rng = [min(lon)-0.5, max(lon)+0.5]
start_date = min(start_date)
end_date = max(end_date)
num_day = int((end_date - start_date) / 86400) + 1
print('data range:')
print('latitude range: %s'%(lat_rng))
print('longitude range: %s'%(lon_rng))
print('time range: %s'%[start_date, end_date])

domain = RectangularDomain(minlatitude=lat_rng[0], maxlatitude=lat_rng[1],
                           minlongitude=lon_rng[0], maxlongitude=lon_rng[1])
for day_idx in range(num_day):
  for net_code in net_codes:
    t0 = start_date + 86400*day_idx
    t1 = start_date + 86400*(day_idx+1)
    print('downloading %s network: %s'%(net_code, t0))
    # 1. set domain & restrict
    restrict = Restrictions(
        starttime=t0, endtime=t1,
        network=net_code, station="*", 
#        location="", channel="HH*",
#        chunklength_in_sec=86400,
        reject_channels_with_gaps=False,
        minimum_length=0.0,
        minimum_interstation_distance_in_m=10,
        channel_priorities=chn_codes,
        location_priorities=loc_codes)

    # 2. set storage
    out_dir = os.path.join(data_root, ''.join(str(t0.date).split('-')))
    if not os.path.exists(out_dir): os.makedirs(out_dir)

    # 3. start download
    mdl = MassDownloader(providers=providers)
    mdl.download(domain, restrict, 
        threads_per_client=num_workers, mseed_storage=out_dir,
        stationxml_storage=sta_dir)

