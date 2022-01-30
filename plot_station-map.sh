#!/bin/sh
R="-118.9/-116.2/34.6/36.8"
J="M14c"
output="output/RC_sta.ps"
grd="/home/public/GMT_data/earth_relief_15s.grd"
fault="input/rc_faults.dat"
org_cpt="topo"
cpt="input/rc.cpt"
inp="input"

# start gmt
gmt psxy -R$R -J$J -T -K > $output
gmt makecpt -C$org_cpt -T-11000/9000/1 > $cpt
gmt psbasemap -R -J -B0.5 -K -O >> $output
gmt grdimage $grd -R -J -C$cpt -I -K -O >> $output
gmt psxy -R -J -W0.6p,black $fault -K -O >> $output

# plot event
awk '{print $1,$2,(1+$3)*0.05}' $inp/event_loc | gmt psxy -R -J -Sc -Gdarkred -K -O  >> $output

# plot stations
gmt psxy $inp/sta_loc  -R -J -St0.5c -Gblue -K -O >> $output
#gmt pstext $inp/sta_name -R -J -F+f14p,1,black+jTL -K -O >> $output

#end gmt
gmt psxy -R$R -J$J -T -O >>$output
rm gmt*
