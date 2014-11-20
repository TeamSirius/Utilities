from scipy.stats import ttest_ind,norm
from db import cur
import numpy as np
import matplotlib.pyplot as plt
"""
id  => n
100 => 2
101 => 10
102 => 30
103 => 60
104 => 100
"""

"""select location_id, count(*) from accesspoint where location_id in (100,101,102,103,104) group by location_id"""

names = {
	"100": "2 Pulls",
	"101": "10 Pulls",
	"102": "30 Pulls",
	"103": "60 Pulls",
	"104": "100 Pulls"
}

def mean(L):
	if len(L) == 0:
		return 0
	return float(sum(L)) / len(L)

def intersection(listas):
	return list(intersection_r(listas))

def intersection_r(listas):
	return set(listas[0]).intersection(*listas[1:]) 

def main():
	data = {}
	cur.execute("""SET SESSION group_concat_max_len = 1000000""")
	cur.execute("""SELECT accesspoint.location_id, GROUP_CONCAT(MAC) as MAC_list,
		GROUP_CONCAT(strength) as strength_list,
		GROUP_CONCAT(std_dev) as std_list from accesspoint
 		join location on location.id=accesspoint.location_id
 		where location.id in (100,101,102,103,104) 
 		group by accesspoint.location_id,x,y,direction""")
	all_macs = []
	for row in cur.fetchall():
		data[str(row[0])] = {"mac": row[1].split(","),
		 "strengths": [float(r) for r in row[2].split(",")],
		 "stds": [float(r) for r in row[3].split(",")]}
		# print "mac: {}".format(len(row[1].split(",")))
		# #print row[1]
		# print "strenght: {}".format(len(row[2].split(",")))
		# #print row[2]
		# print "std: {}".format(len(row[3].split(",")))
		# #print row[3]
		# print "+" * 10
		all_macs.append( row[1].split(",") )
#		hist(names[str(row[0])],data[row[0]]['strengths'])
	intermacs = intersection(all_macs)
	imac = intermacs[0]
	for k,vals in sorted(data.iteritems()):
		print "{}: {}".format(names[k],vals["strengths"][vals["mac"].index(imac)])

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