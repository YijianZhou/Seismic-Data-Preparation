# Preprocess-Raw-Seismic-Data
scripts for preprocessing raw data

Seismic data are usually transmitted in miniseed format, but not all programs can process miniseed files. Also, data need to have a uniform archiving for easy access.

In consideration of these needs, we implemented a set of python scripts for the following functions:

1. mseed2sac & seed2sac

2. merge

3. change header

4. slice into days

5. archive (mkdir + mv)

sac.py utilize python subprocess to call sac & mseed2sac & rdseed

prep_* is my scripts for preprocessing different data

plot_continuity.py can visualize the data continuity
