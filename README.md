# Preprocess-Raw-Seismic-Data
scripts for making an easy access data base from raw data

Seismic data are transmitted in miniseed, but not all tools can process miniseed files. Also, data for a single project need to have a uniform way of archiving for an easy access.

In consideration of these needs, we implemented a set of python scripts for the following functions:

1. mseed2sac

2. merge

3. change head files

4. slice into days

5. archive (mkdir + mv)
