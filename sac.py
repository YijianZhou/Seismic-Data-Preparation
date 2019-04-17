import os
import subprocess
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

""" Data Process
get data
cut sac trace
merge traces
"""

def cut(fpath, b, e, out_path):
    """ set [t0, t1] --> cut stream
    faster in long continuous records
    b, e: second relative to hdeader b
    """
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "cuterr fillz \n"
    s += "cut %s %s \n" %(b, e)
    s += "r %s \n" %(fpath)
    s += "ch allt (0-&1,b&) iztype IB \n"
    s += "w %s \n" %(out_path)
    s += "q \n"
    p.communicate(s.encode())


def merge(fpaths, out_path):
    """ merge sac files
    """
    if len(fpaths)==1: os.rename(fpaths[0], out_path); return
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    print('merge sac files {}'.format(fpaths))
    for i,fpath in enumerate(fpaths):
        if i==0: s += "r %s \n" %(fpath)
        else:    s += "r more %s \n" %(fpath)
    s += "merge g z o a \n"
    s += "w %s \n" %(out_path)
    s += "q \n"
    p.communicate(s.encode())



""" Change Header
station header
event header
"""

def ch_sta(fpath, knetwk, kstnm, stlo, stla, stel):
    """ change station header by SAC
    """
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    print('change station header for {}: {},{},{},{},{}'.\
        format(fpath, knetwk, kstnm, stlo, stla, stel))
    s += "rh %s \n" %(fpath)
    s += "ch stlo %s stla %s \n" %(stlo, stla)
    s += "ch stel %s \n" %(stel)
    s += "ch kstnm %s \n" %(kstnm)
    s += "ch knetwk %s \n" %(knetwk)
    s += "wh \n"
    s += "q \n"
    p.communicate(s.encode())


def ch_event(fpath, evlo, evla, evdp, mag, tp=-1, ts=-1):
    """ change event header by SAC
    """
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "rh %s \n" %(fpath)
    s += "ch evlo %s evla %s \n" %(evlo, evla)
    s += "ch evdp %s \n" %(evdp)
    s += "ch mag %s \n" %(mag)
    if tp>0: s += "ch t0 %s \n" %(tp)
    if ts>0: s += "ch t1 %s \n" %(ts)
    s += "wh \n"
    s += "q \n"
    p.communicate(s.encode())



""" Format Changing
seed to sac
miniseed/ mseed to sac
with IRIS tool: mseed2sac & rdseed
"""

def seed2sac(fpath):
    subprocess.call(['rdseed', '-df', fpath])

def mseed2sac(fpath):
    subprocess.call(['mseed2sac', fpath])

