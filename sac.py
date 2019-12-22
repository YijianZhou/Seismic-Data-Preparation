import os
import subprocess
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

""" Data Process
get data
cut sac trace
merge traces
"""

def cut(fpath, b, e, outpath, fillz=False):
    """ set [t0, t1] --> cut stream
    faster in long continuous records
    b, e: second relative to header b
    """
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    if fillz: s += "cuterr fillz \n"
    s += "cut %s %s \n" %(b, e)
    s += "r %s \n" %(fpath)
    s += "ch allt (0-&1,b&) iztype IB \n"
    s += "w %s \n" %(outpath)
    s += "q \n"
    p.communicate(s.encode())


def merge(fpaths, out_path):
    """ merge sac files
    """
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


""" Change Header
station header
event header
"""

def ch_sta(fpath, knetwk=None, kstnm=None, kcmpnm=None, stlo=0, stla=0, stel=0):
    """ change station header by SAC
    """
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


def ch_event(fpath, evla, evlo, evdp, mag, tn=[]):
    """ change event header by SAC
    """
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "rh %s \n" %(fpath)
    s += "ch evlo %s evla %s \n" %(evlo, evla)
    s += "ch evdp %s \n" %(evdp)
    s += "ch mag %s \n" %(mag)
    for i,ti in enumerate(tn):
        s += "ch t%s %s \n" %(i,ti)
    s += "wh \n"
    s += "q \n"
    p.communicate(s.encode())


"""
seed to sac
miniseed/ mseed to sac
with IRIS tool: mseed2sac & rdseed
"""

def seed2sac(fpath, out_dir=None):
    if out_dir: subprocess.call(['rdseed', '-dfq', fpath, out_dir])
    else: subprocess.call(['rdseed', '-df', fpath])

def mseed2sac(fpath):
    subprocess.call(['mseed2sac', '-O', fpath])

