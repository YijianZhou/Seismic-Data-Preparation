import numpy as np

# i/o paths
fsta = 'input/xls_all.sta'
fout = open('output/xls_neighbor_stations.txt','w')
# params
max_dist = 5 #km

f=open(fsta); lines=f.readlines(); f.close()
line_list, loc_list = lines, []
num_sta = len(lines)
for line in lines:
    net, sta, lon, lat, ele = line.split('\t')
    loc_list.append([float(lon), float(lat)])
loc_list = np.array(loc_list)
cos_lat = np.cos(np.mean(loc_list[:,1]) * np.pi/180)

# corr clust sta
def calc_dist(loc0, loc1):
    dx = cos_lat*(loc0[0] - loc1[0])
    dy = loc0[1] - loc1[1]
    return 111*(np.sqrt(dx**2 + dy**2))

corr_mat = np.zeros([num_sta, num_sta])
for i in range(num_sta-1):
  for j in range(i+1, num_sta):
    if calc_dist(loc_list[i],loc_list[j])<max_dist: corr_mat[i,j]=1

print('clustering')
clusters = []
# find isolated events
for i in range(num_sta-1):
    nbrs  = list(np.where(corr_mat[i]==1)[0])
    nbrs += list(np.where(corr_mat[:,i]==1)[0])
    if len(nbrs)==0: clusters.append([i]) # save the idx

for i in range(num_sta-1):
    nbrs  = list(np.where(corr_mat[i]==1)[0])
    nbrs += list(np.where(corr_mat[:,i]==1)[0])
    corr_mat[i, corr_mat[i]==1] = 0
    corr_mat[corr_mat[:,i]==1, i] = 0
    if len(nbrs)>0: clusters.append(nbrs+[i]) # save the idx
    while len(nbrs)>0:
        new_nbrs = []
        for nbr in nbrs:
            new_nbrs += list(np.where(corr_mat[nbr]==1)[0])
            new_nbrs += list(np.where(corr_mat[:,nbr]==1)[0])
            corr_mat[nbr, corr_mat[nbr]==1] = 0
            corr_mat[corr_mat[:,nbr]==1, nbr] = 0
        clusters[-1] += new_nbrs
        nbrs = new_nbrs
clusters = [np.unique(cluster) for cluster in clusters]
print('%s clusters found'%len(clusters))

# write sta clusts
for i,cluster in enumerate(clusters):
    fout.write('# %sth station location \n'%(i+1))
    for line_idx in cluster: fout.write(line_list[line_idx])
fout.close()
