""" Plot and report raw data continuity against station operation periods.

For each net.sta, expected days are calculated from the operation periods in
output/station_full_pal.csv. Downloaded days are counted from raw MiniSEED files
only when the raw net.sta.loc.chn matches a selected station-file entry active
on that day.
"""
import os, glob, csv, sys
from collections import defaultdict
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


# i/o paths
raw_root = '/nas/zhouyj/Campi_Flegeri_raw'
raw_list_file = 'output/cf_raw_mseed_paths.txt'
fsta = 'output/station_full_pal.csv'
fout = 'output/cf_data-continuity.jpg'
freport = 'output/cf_data-continuity_report.csv'
flow = 'output/cf_data-continuity_low40.csv'
title = 'Campi Flegrei Raw Data Continuity'
# continuity params
low_ratio = 0.40
# fig config
fig_size = (36,24)
fsize_label = 14
fsize_title = 18
marker_size = 70
alpha_expected = 0.18
alpha_data = 0.85



def read_raw_paths(raw_root, raw_list_file):
    if os.path.exists(raw_list_file):
        f = open(raw_list_file, 'r', encoding='utf-8')
        raw_paths = [line.strip() for line in f if line.strip()]
        f.close()
        print('read %s raw paths from %s'%(len(raw_paths),raw_list_file))
        return raw_paths
    raw_paths = sorted(glob.glob(os.path.join(raw_root, '*', '*.mseed')))
    out_dir = os.path.dirname(raw_list_file)
    if out_dir and not os.path.exists(out_dir): os.makedirs(out_dir)
    f = open(raw_list_file, 'w', encoding='utf-8')
    for raw_path in raw_paths:
        f.write('%s\n'%raw_path)
    f.close()
    print('wrote %s raw paths to %s'%(len(raw_paths),raw_list_file))
    return raw_paths

def parse_time(text):
    text = text.strip()
    if len(text)==8 and text.isdigit():
        return datetime.strptime(text, '%Y%m%d')
    if text.endswith('Z'): text = text[:-1]
    return datetime.fromisoformat(text)


def day0(t):
    return datetime(t.year, t.month, t.day)


def date_str(t):
    return t.strftime('%Y%m%d')


def parse_station_id(sta_id):
    parts = sta_id.strip().split('.')
    if len(parts)<4: return None
    net, sta, chn = parts[0:3]
    loc = '.'.join(parts[3:])
    return net, sta, chn, loc


def parse_raw_name(raw_path):
    fname = os.path.basename(raw_path)
    name = fname.split('__')[0]
    parts = name.split('.')
    if len(parts)<4: return None
    net, sta, loc, chn = parts[0:4]
    return net, sta, loc, chn[0:3]


def iter_overlap_days(t0, t1):
    cur = day0(t0)
    while cur < t1:
        nxt = cur + timedelta(days=1)
        if nxt > t0 and cur < t1:
            yield cur
        cur = nxt


def read_station_file(fsta):
    if not os.path.exists(fsta):
        sys.exit('missing station file: %s'%fsta)
    sta_periods = defaultdict(list)
    active_keys = defaultdict(set)
    expected_days = defaultdict(set)
    f = open(fsta, 'r', newline='', encoding='utf-8-sig')
    reader = csv.reader(f)
    for row in reader:
        if len(row)<9: continue
        parsed = parse_station_id(row[0])
        if parsed is None: continue
        net, sta, chn, loc = parsed
        t0, t1 = parse_time(row[7]), parse_time(row[8])
        net_sta = '%s.%s'%(net,sta)
        sta_periods[net_sta].append([t0,t1,row[0]])
        for day in iter_overlap_days(t0,t1):
            expected_days[net_sta].add(day)
            active_keys[date_str(day)].add((net,sta,loc,chn))
    f.close()
    return sta_periods, active_keys, expected_days


def count_raw_days(raw_paths, active_keys):
    data_days = defaultdict(set)
    for raw_path in raw_paths:
        raw_dir = os.path.dirname(raw_path)
        date = os.path.basename(raw_dir)
        if date not in active_keys: continue
        parsed = parse_raw_name(raw_path)
        if parsed is None: continue
        net, sta, loc, chn = parsed
        if (net,sta,loc,chn[0:2]) not in active_keys[date]: continue
        data_days['%s.%s'%(net,sta)].add(datetime.strptime(date, '%Y%m%d'))
    return data_days


def write_report(sta_keys, sta_periods, expected_days, data_days):
    out_dir = os.path.dirname(freport)
    if out_dir and not os.path.exists(out_dir): os.makedirs(out_dir)
    rows = []
    for sta_key in sta_keys:
        n_expected = len(expected_days[sta_key])
        n_data = len(data_days[sta_key] & expected_days[sta_key])
        ratio = n_data / n_expected if n_expected>0 else 0.0
        periods = ['%s-%s:%s'%(date_str(t0),date_str(t1),sta_id) for t0,t1,sta_id in sta_periods[sta_key]]
        rows.append({
            'station': sta_key,
            'expected_days': n_expected,
            'downloaded_days': n_data,
            'continuity_ratio': '%.4f'%ratio,
            'operation_periods': ';'.join(periods)})

    f = open(freport, 'w', newline='', encoding='utf-8')
    fieldnames = ['station','expected_days','downloaded_days','continuity_ratio','operation_periods']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    f.close()

    low_rows = [row for row in rows if float(row['continuity_ratio'])<low_ratio]
    f = open(flow, 'w', newline='', encoding='utf-8')
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(low_rows)
    f.close()
    print('%s %s stations'%(freport,len(rows)))
    print('%s %s stations below %.0f%%'%(flow,len(low_rows),low_ratio*100))
    return rows, low_rows


def plot_continuity(sta_keys, sta_periods, expected_days, data_days):
    out_dir = os.path.dirname(fout)
    if out_dir and not os.path.exists(out_dir): os.makedirs(out_dir)
    plt.figure(figsize=fig_size)
    ax = plt.gca()
    for i, sta_key in enumerate(sta_keys):
        # expected operational days behind downloaded days
        x_expected = sorted(expected_days[sta_key])
        if len(x_expected)>0:
            plt.vlines(x_expected, i-0.35, i+0.35, color='k', linewidth=0.25,
                alpha=alpha_expected, zorder=1)
        # operation-period boundaries from fullfed-derived station file
        for t0, t1, _ in sta_periods[sta_key]:
            plt.vlines([t0,t1], i-0.45, i+0.45, color='k', linewidth=0.8, zorder=2)
        x_data = sorted(data_days[sta_key] & expected_days[sta_key])
        plt.scatter(x_data, [i]*len(x_data), marker='+', s=marker_size,
            alpha=alpha_data, zorder=3)

    plt.setp(ax.xaxis.get_majorticklabels(), fontsize=fsize_label, rotation=30, ha='right')
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))
    plt.yticks(list(range(len(sta_keys))), sta_keys, fontsize=fsize_label)
    plt.title(title, fontsize=fsize_title)
    plt.ylim(-1, len(sta_keys))
    plt.grid(True, axis='x')
    plt.tight_layout()
    plt.savefig(fout, dpi=600)
    print('wrote %s'%fout)


sta_periods, active_keys, expected_days = read_station_file(fsta)
sta_keys = sorted(sta_periods.keys())
raw_paths = read_raw_paths(raw_root, raw_list_file)
data_days = count_raw_days(raw_paths, active_keys)
rows, low_rows = write_report(sta_keys, sta_periods, expected_days, data_days)
plot_continuity(sta_keys, sta_periods, expected_days, data_days)