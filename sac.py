import os
from obspy import read, UTCDateTime
import subprocess
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

def cut(fpath, b, e, outpath, fillz=False):
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    if fillz: s += "cuterr fillz \n"
    s += "cut %s %s \n" %(b, e)
    s += "r %s \n" %(fpath)
    s += "ch allt (0-&1,b&) iztype IB \n"
    s += "w %s \n" %(outpath)
    s += "q \n"
    p.communicate(s.encode())


def obspy_trim(stream, t0, t1, zfill=False):
    if not zfill: st = stream.copy().trim(t0, t1)
    if zfill: st = stream.copy().trim(t0, t1, pad=True, fill_value=0)
    for tr in st:
        tr.stats.sac.nzyear = t0.year
        tr.stats.sac.nzjday = t0.julday
        tr.stats.sac.nzhour = t0.hour
        tr.stats.sac.nzmin = t0.minute
        tr.stats.sac.nzsec = t0.day
        tr.stats.sac.nzmsec = t0.microsecond / 1e3
    return st


def obspy_slice(stream, t0, t1):
    st = stream.slice(t0, t1)
    for tr in st:
        tr.stats.sac.nzyear = t0.year
        tr.stats.sac.nzjday = t0.julday
        tr.stats.sac.nzhour = t0.hour
        tr.stats.sac.nzmin = t0.minute
        tr.stats.sac.nzsec = t0.day
        tr.stats.sac.nzmsec = t0.microsecond / 1e3
    return st


def merge(fpaths, out_path):
    num_files = len(fpaths)
    if num_files==0: return
    if num_files==1: os.rename(fpaths[0], out_path); return
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    print('merge sac files to {}'.format(out_path))
    if num_files<1000:
      for i,fpath in enumerate(fpaths):
        if i==0: s += "r %s \n" %(fpath)
        else:    s += "r more %s \n" %(fpath)
      s += "merge g z o a \n"
      s += "w %s \n" %(out_path)
    else:
      os.rename(fpaths[0], 'tmp.sac')
      num_batch = 1 + (num_files-2)//999
      for idx in range(num_batch):
        # read one batch (1000 files)
        s += "r tmp.sac \n"
        for fpath in fpaths[1+idx*999:1+(idx+1)*999]:
            s += "r more %s \n" %(fpath)
        # merge batch to tmp sac
        s += "merge g z o a \n"
        s += "w tmp.sac \n"
      os.rename('tmp.sac', out_path)
    s += "q \n"
    p.communicate(s.encode())


def ch_sta(fpath, knetwk=None, kstnm=None, kcmpnm=None, stlo=0, stla=0, stel=0):
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    print('change station header for {}: {},{},{},{},{},{}'\
        .format(fpath, knetwk, kstnm, kcmpnm, stlo, stla, stel))
    s += "rh %s \n" %(fpath)
    s += "ch stlo %s stla %s \n" %(stlo, stla)
    s += "ch stel %s \n" %(stel)
    if knetwk: s += "ch knetwk %s \n" %(knetwk)
    if kstnm:  s += "ch kstnm %s \n" %(kstnm)
    if kcmpnm: s += "ch kcmpnm %s \n" %(kcmpnm)
    s += "wh \n"
    s += "q \n"
    p.communicate(s.encode())


def ch_event(fpath, evla=None, evlo=None, evdp=None, mag=None, tn={}):
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "rh %s \n" %(fpath)
    if evlo: s += "ch evlo %s \n" %evlo
    if evla: s += "ch evla %s \n" %evla
    if evdp: s += "ch evdp %s \n" %(evdp)
    if mag: s += "ch mag %s \n" %(mag)
    for ti_code,ti in tn.items():
        s += "ch %s %s \n" %(ti_code,ti)
    s += "wh \n"
    s += "q \n"
    p.communicate(s.encode())


def seed2sac(fpath, out_dir=None):
    if out_dir: subprocess.call(['rdseed', '-dfq', fpath, out_dir])
    else: subprocess.call(['rdseed', '-df', fpath])


def mseed2sac(fpath):
    subprocess.call(['mseed2sac', '-O', fpath])
