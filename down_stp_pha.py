""" Download phase file with STP https://scedc.caltech.edu/research-tools/stp/
"""
from obspy import UTCDateTime
import subprocess

# i/o files
time_range = '20190704-20190725'
fpha = 'output/rc_scsn_%s.dat'%time_range

# download params
lat_range = [35.4, 36.1]
lon_range = [-117.9, -117.2]
start_time, end_time = [UTCDateTime(time) for time in time_range.split('-')]
num_days = (end_time.date - start_time.date).days
t0 = '/'.join(str(start_time.date).split('-')) + ',00:00:00'
max_num = 100000

# start download
p = subprocess.Popen(['stp'], stdin=subprocess.PIPE)
s = "SET NEVNTMAX %s \n"%max_num
s+= "PHASE -t0 %s +%sd -lon %s %s -lat %s %s -f %s \n"%(t0, num_days, lon_range[0], lon_range[1], lat_range[0], lat_range[1], fpha)
s+= "quit \n"
p.communicate(s.encode())

