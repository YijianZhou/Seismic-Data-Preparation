import os, glob
import tarfile
import multiprocessing as mp

# i/o paths
event_dirs = glob.glob('/data1/XC_events/evtloc/20160513.134.*')
out_root = 'output'
# params
num_workers = 10

def tar_event(event_dir):
    print('tar %s'%event_dir)
    event_name = os.path.basename(event_dir)
    out_path = os.path.join(out_root, event_name)
    with tarfile.open(out_path, "w") as tar:
        tar.add(event_dir, arcname=event_name)

def untar_event(tar_path):
    print('untar %s'%tar_path)
    event_name = os.path.basename(tar_path)
    out_dir = os.path.join(out_root, 'output')
    t = tarfile.open(tar_path)
    t.extractall(path = out_dir)

"""
# tar
for event_dir in event_dirs: tar_event(event_dir)
# untar
event_tars = [os.path.join(out_root, os.path.basename(event_dir)) for event_dir in event_dirs]
for event_tar in event_tars: untar_event(event_tar)
"""

pool = mp.Pool(num_workers)
pool.map_async(tar_event, event_dirs)
pool.close()
pool.join()

