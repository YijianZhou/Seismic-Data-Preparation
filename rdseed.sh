#!/bin/bash
ls -d /data3/XJ_SAC/YN/2017/* > dirs
for dir in $(cat dirs)
do
    cd $dir
    ls -d *.seed > tmp
    for file in $(cat tmp)
    do
      rdseed -df $file
    done
    rm *.seed tmp
done
rm dirs
