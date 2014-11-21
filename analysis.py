from scipy.stats import ttest_ind,norm
import scipy
from db import cur
import numpy as np
import matplotlib.pyplot as plt



names = {
	"100": "2 Pulls",
	"101": "10 Pulls",
	"102": "30 Pulls",
	"103": "60 Pulls",
	"104": "100 Pulls"
}


titles = [["2 Pulls", "10 Pulls", "30 Pulls", "60 Pulls", "100 Pulls"],["T1", "T2", "T3", "T4","T5"]]

#IDS must be parallel with the corresponding titles array
#	LISTS MUST BE OF LENTH 5

ids = [[100,101,102,103,104],[6,7,8,9,10]]



def flatten(L):
	return [item for sublist in L for item in sublist]


def mean(L):
	if len(L) == 0:
		return 0
	return float(sum(L)) / len(L)

def intersection(listas):
	return list(intersection_r(listas))

def intersection_r(listas):
	return set(listas[0]).intersection(*listas[1:]) 

def main():
	sum_data = [[0 for i in range(5)] for j in range(5)]
	for ts_id, id_list in enumerate(ids):
		for t_id,ID in enumerate(id_list):
			names[str(ID)] = titles[ts_id][t_id]
		data = {}
		if len(id_list) != 5:
			pass
		cur.execute("""SET SESSION group_concat_max_len = 1000000""")
		cur.execute("""SELECT accesspoint.location_id, GROUP_CONCAT(MAC) as MAC_list,
			GROUP_CONCAT(strength) as strength_list,
			GROUP_CONCAT(std_dev) as std_list from accesspoint
	 		join location on location.id=accesspoint.location_id
	 		where location.id in (%s,%s,%s,%s,%s) 
	 		group by accesspoint.location_id,x,y,direction""", id_list )
		all_macs = []
		for row in cur.fetchall():
			data[str(row[0])] = {"mac": row[1].split(","),
			 "strengths": [float(r) for r in row[2].split(",")]}#,
			# "stds": [float(r) for r in row[3].split(",")]}
			all_macs.append( row[1].split(",") )
		unique = len(set(flatten(all_macs)))
		intermacs = intersection(all_macs)
		stds = []
		print "Comparing {} common mac addresses of {} unique".format(len(intermacs),unique)
		for imac in intermacs:
			L = {}
			for k in data.keys():
				L[k] = []
			for k,vals in sorted(data.iteritems()):
				L[k].append( vals["strengths"][vals["mac"].index(imac)] )

		ks = [" " * 10]
		for k in sorted(L.keys(),key=lambda x: names[x]):
			ks.append(names[str(k)].rjust(10))
		print ' '.join(ks)
		sorted_items = sorted(L.iteritems(),key=lambda x: names[x[0]])
		for i,(k,v) in enumerate(sorted_items):
			d = [names[str(k)].ljust(10)]
			for j,(key,val) in enumerate(sorted_items):
				diff = difference(val,v) 
				sum_data[i][j] += diff
				d.append(str( round(diff ,2) ).rjust(10) )
			print ' '.join(d)
		print
	print
	print "Average Table:"
	for i in sum_data:
		print ' '.join([str( round(x / float(len(ids)), 2) ).rjust(10) for x in i])

def difference(L1,L2):
	s = 0
	if len(L1) != len(L2):
		return 0
	for i in range(len(L1)):
		s += (L1[i] - L2[i]) ** 2
	return s ** 0.5

def hist(name,L):
	plt.title(name)
	plt.hist(L,bins = 500)#,range=(-100,-50))
	plt.grid(True)
	#plt.ylim([0,15])
	plt.show()

def same(ap1, ap2):
	return 1 - ttest_ind(
		norm.rvs(loc=ap1.strength,scale=ap1.std,size=ap1.sample_size),
		norm.rvs(loc=ap2.strength,scale=ap2.std,size=ap2.sample_size),
		equal_var = False)[1]


if __name__ == "__main__":
	main()