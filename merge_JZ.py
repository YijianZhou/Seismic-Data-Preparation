"""
msd2sac + merge 
for JZ data in /data2/JZ (on ZSY workstation, 162.105.91.211)
by Yijian Zhou 2017-11-17
python merge_JZ.py
"""
import os, glob, subprocess, fileinput, math
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')
paths = glob.glob('/data2/JZ/00*/*/1710')
for path in paths:
        # cd to dir of one day's data
        os.chdir(path)
        msd_files = glob.glob('E00*')
        for i in range(len(msd_files)):
                if msd_files[i].split('.')[-1] != 'LOG':
                        subprocess.call(['mseed2sac', msd_files[i]])

        sets = {}
        for fname in glob.glob("*.SAC"):
                net, sta, sub_net, chn, _, yr, day, time,_ = fname.split('.')
                key = '.'.join([sta, chn])
                print(key)
                if key not in sets:
                        sets[key] = 1
                else:
                        sets[key] += 1

        todel=glob.glob("*.SAC")
        p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
        s = "wild echo off \n"

        for key, value in sets.items():
                print("merge %s: %d traces" % (key, value))
                sta, chn = key.split('.')
                s += "r *%s*%s*.SAC \n" % (sta, chn) # SAC v101.6 or later
                s += "merge  g z o a\n"
                s += "w PJ%s.%s.%s.SAC\n" %(sta[1:3], sta[3:5], chn) # rename
        s += "q \n"
        p.communicate(s.encode())

        for file in todel:
                os.unlink(file)
                                                       
