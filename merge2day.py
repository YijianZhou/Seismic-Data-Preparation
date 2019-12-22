import os
import glob
os.putenv("SAC_DISPLAY_COPYRIGHT", '0')
import subprocess
import obspy
import numpy as np
from obspy.core import *
from datetime import datetime, timedelta
import shutil
# Tool


def jday2YYYYMMDD(year, jday):
    dt = datetime.strptime(str(year) + str(jday), '%Y%j').date()
    month = str(dt.month)
    day = str(dt.day)
    YYYYMMDD = str(year) + month.zfill(2) + day.zfill(2)

    return YYYYMMDD


def cal_days_for_1year(year):
    dt = datetime.strptime(str(year) + '1231', '%Y%m%d').date()
    jday = int(dt.strftime('%j'))
    return jday



def merge(tar_file_list, out_sacfile):
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "r %s\n" % tar_file_list[0]
    print(tar_file_list)
    if len(tar_file_list) > 1:
        for tar_file in tar_file_list[1:]:
            s += "r more %s\n" % tar_file  # SAC v101.6 or later
    s += "merge g z o a \n"
    s += "w %s \n" % out_sacfile
    s += "q \n"
    p.communicate(s.encode())

    return None


def slice_stream_sac(out_sacfile_stage1, tar_ts, tar_te, out_sacfile_stage2):
    str_day = out_sacfile_stage1.split('/')[-2]
    day_date = UTCDateTime(str_day)
    p = subprocess.Popen(['sac'], stdin=subprocess.PIPE)
    s = "wild echo off \n"
    s += "cuterr fillz \n"
    s += "cut b %s %s \n" % (tar_ts, tar_te)
    s += "r %s \n" % out_sacfile_stage1
    s += "ch b 0 \n" # Necessary!
    s += "ch nzhour %s nzmin %s nzsec %s nzmsec %s \n" % (0,0,0,0) # Necessary!
    s += "ch nzyear %s nzjday %s \n" % (day_date.year, day_date.julday) # Necessary!
    s += "w %s \n" % out_sacfile_stage2
    s += "q \n"
    p.communicate(s.encode())
    print (out_sacfile_stage2)


def slice_getOneday(out_sacfile_stage1, out_sacfile_stage2):
    str_day = out_sacfile_stage1.split('/')[-2]
    day_date = UTCDateTime(str_day)

    st = read(out_sacfile_stage1)
    ts = st[0].stats.starttime
    # te = st[0].stats.endtime
    tar_ts = day_date - ts
    tar_te = tar_ts + 86400

    slice_stream_sac(out_sacfile_stage1, tar_ts, tar_te, out_sacfile_stage2)

    return None

def merge_and_slice2oneday(
        origin_sacfilepath,
        tar_file_list,
        out_sacfile_stage1,
        out_sacfile_stage2):
    # os.chdir(origin_sacfilepath)
    merge(tar_file_list, out_sacfile_stage1)
    slice_getOneday(out_sacfile_stage1, out_sacfile_stage2)
    os.remove(out_sacfile_stage1)

    return None

def merge_and_slice2oneday_obspy(
        tar_file_list,
        out_sacfile_stage2,log_file):
    print (out_sacfile_stage2)
    st=obspy.read(tar_file_list[0],dtype='float64')
    if len(tar_file_list) > 1:
        for tar_file in tar_file_list[1:]:
            st=st+obspy.read(tar_file,dtype='float64')

    print (st)
    for t in range(len(st)):
        sr=st[t].stats.sampling_rate
        print (sr)
        if sr != 100:
            shutil.move(tar_file_list[t], '/home/data/Changning/s6data')
    st=st.select(sampling_rate=100)
    print (st)

    st_merge=st.merge(fill_value=0)
    if len(st_merge) != 1:
        raise ValueError('The merge and slice result is wrong!')
    sampling_rate = round(st_merge[0].stats.sampling_rate)

    str_day = out_sacfile_stage2.split('/')[-2]
    day_date = UTCDateTime(str_day)
    tar_ts = day_date
    tar_te = tar_ts + 86400 -1/sampling_rate

    st_final=st_merge.slice(tar_ts,tar_te)
    if len(st_final) == 0:
        print ('There is no data for %s' % (out_sacfile_stage2.split('/')[-2:]))
        with open(log_file,'a') as f:
            f.writelines('There is no data for %s' % (out_sacfile_stage2.split('/')[-2:]))
    else:
        tr=st_final[0]

        start_time=tr.stats.starttime
        end_time = tr.stats.endtime

        before_points=round((start_time-tar_ts)*round(sampling_rate))
        stats_before=tr.stats.copy()
        stats_before.starttime = tar_ts
        stats_before.npts = before_points
        tr_before=trace.Trace(data=np.array([float(0)]*before_points),header=stats_before)

        after_points=round((tar_te-end_time)*round(sampling_rate))
        stats_after=tr.stats.copy()
        stats_after.starttime = end_time+1/sampling_rate
        stats_after.npts = after_points
        tr_after = trace.Trace(data=np.array([float(0)] * after_points), header=stats_after)

        tr_final=tr_before+tr+tr_after
        tr_final.stats.sac['delta'] = 1/sampling_rate
        tr_final.stats.sac['b']=0
        tr_final.stats.sac['e'] = tr_final.stats.endtime-tr_final.stats.starttime
        tr_final.stats.sac['npts'] = tr_final.stats.npts
        tr_final.stats.sac['nzyear']=tr_final.stats.starttime.year
        tr_final.stats.sac['nzjday'] = tr_final.stats.starttime.julday
        tr_final.stats.sac['nzhour'] = tr_final.stats.starttime.hour
        tr_final.stats.sac['nzmin'] = tr_final.stats.starttime.minute
        tr_final.stats.sac['nzsec'] = tr_final.stats.starttime.second
        tr_final.stats.sac['nzmsec'] = tr_final.stats.starttime.microsecond
        tr_final.write(out_sacfile_stage2,format='SAC') # LPSPOL is wrong in the head.

    return None



def get_tar_day_list(origin_sacfilepath, year, day, sta, chn, firstdate):

    def get_last_sacfile(origin_sacfilepath, year, day, sta, chn):
        last_sacfiles = []
        for i in range(20):
            today = datetime.strptime(str(year) + str(day), '%Y%j').date()
            tar_date = today - timedelta(days=i + 1)
            tar_day = tar_date.strftime('%j')
            tar_year = tar_date.strftime('%Y')
            # tar_day_files = glob.glob(
            #     os.path.join(
            #         origin_sacfilepath,
            #         tar_year +
            #         '.' +
            #         str(tar_day).zfill(3) +
            #         '.*.' +
            #         sta +
            #         '.*.' +
            #         chn +
            #         '.*'))
            tar_day_files = glob.glob(
                os.path.join(
                    origin_sacfilepath,
                    sta +
                    '.*.' +
                    chn +
                    '.*.' +
                    tar_year +
                    '.' +
                    str(tar_day).zfill(3) +
                    '.*'))
            if tar_day_files != []:
                last_sacfiles = last_sacfiles + tar_day_files
                break
        return last_sacfiles

    # Only need to find the last day
    tar_file_list = []
    # today_files = glob.glob(
    #     os.path.join(
    #         origin_sacfilepath,
    #         year +
    #         '.' +
    #         str(day).zfill(3) +
    #         '.*.' +
    #         sta +
    #         '.*.' +
    #         chn +
    #         '.*'))

    today_files = glob.glob(
        os.path.join(
            origin_sacfilepath,
            sta +
            '.*.' +
            chn +
            '.*.' +
            year +
            '.' +
            str(day).zfill(3) +
            '.*'))

    tar_file_list = tar_file_list + today_files

    if datetime.strptime(str(year) + str(day), '%Y%j').date() != firstdate:
        tar_file_list = tar_file_list + \
            get_last_sacfile(origin_sacfilepath, year, day, sta, chn)

    return tar_file_list


def run_merge(
        origin_sacfilepath,
        outpath,
        year_list,
        sta_list,
        chn_dic,
        b_jday_list,
        e_jday_list,
        first_flag_list):

    for y in range(len(year_list)):
        # Determine if it is the first day.
        year = year_list[y]
        log_file='merge_HWS.log'
        if os.path.exists(log_file):
            os.remove(log_file)

        b_jday = b_jday_list[y]
        e_jday = e_jday_list[y]
        first_flag = first_flag_list[y]
        if first_flag:
            firstdate = datetime.strptime(
                str(year) + str(b_jday), '%Y%j').date()
        else:
            firstdate = ''
        # print(firstdate)

        # Set the output path.
        out_sacfilepath = os.path.join(outpath, str(year))
        # if os.path.exists(out_sacfilepath):
        #     shutil.rmtree(out_sacfilepath)
        # os.makedirs(out_sacfilepath)


        #
        for day in range(int(b_jday), int(e_jday) + 1):
            # day=4
            print('Merge %s %s...' % (str(year), str(day)))
            # os.makedirs(
            #     os.path.join(
            #         out_sacfilepath,
            #         jday2YYYYMMDD(
            #             str(year),
            #             str(day).zfill(3))))

            for sta in sta_list:
                # sta='GZ.BJT'
                for chn in chn_dic[sta]:
                    # chn='BHZ'
                    tar_file_list = get_tar_day_list(
                        origin_sacfilepath, year, day, sta, chn, firstdate)
                    out_sacfile_stage1 = os.path.join(out_sacfilepath, jday2YYYYMMDD(
                        str(year), str(day).zfill(3)), '.'.join([sta, chn, 'pre']))
                    out_sacfile_stage2 = os.path.join(out_sacfilepath, jday2YYYYMMDD(
                        str(year), str(day).zfill(3)), '.'.join([sta, chn]))

                    if tar_file_list != []:
                        # merge_and_slice2oneday(
                        #     origin_sacfilepath,
                        #     tar_file_list,
                        #     out_sacfile_stage1,
                        #     out_sacfile_stage2)
                        merge_and_slice2oneday_obspy(
                            tar_file_list,
                            out_sacfile_stage2,log_file)
                    else:
                        print('There is no data for %s' % (out_sacfile_stage2.split('/')[-2:]))
                        with open(log_file, 'a') as f:
                            f.writelines('There is no data for %s' % (out_sacfile_stage2.split('/')[-2:]))



if __name__ == "__main__":
    origin_sacfilepath = '/home/data/Changning/s6data/sac_part1'
    outpath = '/home/data/Changning/s6data/sac'
    # origin_sacfilepath = '/home/yunnd/Workspace/Dynamic_triggering/Changning/data/s6data/sac_part1'
    # outpath = '/home/yunnd/Workspace/Dynamic_triggering/Changning/data/s6data/sac'
    year_list = ['2013','2014','2015','2016','2017','2018','2019']
    sta_list = ['SC.HWS']
    chn_dic = {'SC.HWS': ['BHZ', 'BHE', 'BHN']}

    b_jday_list = [1,1,1,1,1,1,1]
    e_jday_list = [365,365,365,366,365,365,198]
    first_flag_list = [True,False,False,False,False,False,False]
    run_merge(
        origin_sacfilepath,
        outpath,
        year_list,
        sta_list,
        chn_dic,
        b_jday_list,
        e_jday_list,
        first_flag_list)

    print('finish')
