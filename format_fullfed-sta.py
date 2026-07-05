""" Format station file in Fullfed format, e.g. http://www.fdsn.org/networks/detail/7D_2011/
"""
import os
from collections import defaultdict
from obspy import UTCDateTime


# i/o paths
nets = ['iv','ix','zm','2i']
fsta_template = 'input/station_%s.fullfed'
fout_template = 'output/station_%s_r1.csv'
fsummary_template = 'output/station_%s_r1_overlap_summary.csv'
# channel priority, selected independently for each net.sta.loc time period
chn_codes = ['HH','BH','EH']
lat_min, lat_max = 40.39, 41.22
lon_min, lon_max = 13.48, 14.78
t_min, t_max = UTCDateTime('20150101'), UTCDateTime('20270101')


def comp_key(chn):
    comp = chn[-1].upper()
    if comp == 'E' or comp == '1': return 'E'
    if comp == 'N' or comp == '2': return 'N'
    if comp == 'Z' or comp == '3': return 'Z'
    return comp


def time_str(t):
    return t.strftime('%Y%m%d')


def read_fullfed(fsta):
    sta_dict = defaultdict(list)
    f = open(fsta, 'r', encoding='utf-8')
    lines = f.readlines()
    f.close()
    for line in lines[3:]:
        codes = line.strip().split('|')
        if len(codes)<17: continue
        net, sta, loc, chn = codes[0:4]
        chn0 = chn[0:2]
        if chn0 not in chn_codes: continue
        lat, lon, ele = [float(code) for code in codes[4:7]]
        if not (lat_min<lat<lat_max and lon_min<lon<lon_max): continue
        t0, t1 = [UTCDateTime(code) for code in codes[-2:]]
        if t1<=t_min or t0>=t_max: continue
        t0, t1 = max(t0,t_min), min(t1,t_max)
        sta_dict[(net,sta,loc)].append({
            'net': net, 'sta': sta, 'loc': loc, 'chn': chn, 'chn0': chn0,
            'comp': comp_key(chn), 'lat': lat, 'lon': lon, 'ele': ele,
            'gain': float(codes[11]), 't0': t0, 't1': t1})
    return sta_dict


def gain_code(recs):
    comp_gains = {}
    for rec in sorted(recs, key=lambda x: x['chn']):
        if rec['comp'] not in comp_gains:
            comp_gains[rec['comp']] = rec['gain']
    if len(comp_gains)==1:
        gain = list(comp_gains.values())[0]
        return '%s,%s,%s'%(gain,gain,gain), 'single_component_copied'
    gains = [comp_gains.get(comp,'') for comp in ['E','N','Z']]
    note = '' if all(gain!='' for gain in gains) else 'missing_component'
    return '%s,%s,%s'%(gains[0],gains[1],gains[2]), note


def period_active_records(recs, t0, t1):
    return [rec for rec in recs if rec['t0']<=t0 and rec['t1']>=t1]


def choose_channel(active_recs):
    active_chns = sorted(set([rec['chn0'] for rec in active_recs]))
    for chn0 in chn_codes:
        if chn0 in active_chns:
            return chn0, active_chns
    return None, active_chns


def format_station(sta_dict):
    out_lines, summary_lines = [], []
    for (net,sta,loc), recs in sorted(sta_dict.items()):
        edge_dict = {}
        for rec in recs:
            edge_dict[float(rec['t0'])] = rec['t0']
            edge_dict[float(rec['t1'])] = rec['t1']
        edges = [edge_dict[key] for key in sorted(edge_dict)]
        for idx in range(len(edges)-1):
            t0, t1 = edges[idx], edges[idx+1]
            if t0>=t1: continue
            active_recs = period_active_records(recs, t0, t1)
            if len(active_recs)==0: continue
            chn0, active_chns = choose_channel(active_recs)
            if chn0 is None: continue
            sel_recs = [rec for rec in active_recs if rec['chn0']==chn0]
            gain_str, gain_note = gain_code(sel_recs)
            lat = sum([rec['lat'] for rec in sel_recs]) / len(sel_recs)
            lon = sum([rec['lon'] for rec in sel_recs]) / len(sel_recs)
            ele = sum([rec['ele'] for rec in sel_recs]) / len(sel_recs)
            net_sta_chn_loc = '%s.%s.%s.%s'%(net,sta,chn0,loc)
            out_lines.append('{},{:.6f},{:.6f},{:.1f},{},{},{}\n'.format(
                net_sta_chn_loc, lat, lon, ele, gain_str, time_str(t0), time_str(t1)))

            comp_counts = defaultdict(int)
            for rec in sel_recs:
                comp_counts[rec['comp']] += 1
            dup_comps = sorted([comp for comp,count in comp_counts.items() if count>1])
            if len(active_chns)>1 or gain_note or len(dup_comps)>0:
                summary_lines.append('{},{},{},{},{},{},{},{},{}\n'.format(
                    net, sta, loc, time_str(t0), time_str(t1),
                    ';'.join(active_chns), chn0,
                    gain_note, ';'.join(dup_comps)))
    return out_lines, summary_lines


def write_lines(fout, lines, header=None):
    out_dir = os.path.dirname(fout)
    if out_dir and not os.path.exists(out_dir): os.makedirs(out_dir)
    f = open(fout, 'w', encoding='utf-8')
    if header: f.write(header)
    for line in lines:
        f.write(line)
    f.close()


for net in nets:
    fsta = fsta_template%net
    if not os.path.exists(fsta): continue
    sta_dict = read_fullfed(fsta)
    out_lines, summary_lines = format_station(sta_dict)
    fout = fout_template%net
    fsummary = fsummary_template%net
    write_lines(fout, out_lines)
    write_lines(fsummary, summary_lines,
        header='net,sta,loc,t0,t1,active_chns,selected_chn,gain_note,duplicate_components\n')
    print('%s %s stations/periods'%(fout,len(out_lines)))
    print('%s %s summary rows'%(fsummary,len(summary_lines)))



