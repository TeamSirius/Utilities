from scipy.stats import ttest_ind,norm
from db import cur

"""
id  => n
100 => 2
101 => 10
102 => 30
103 => 60
104 => 100
"""


def main():
	cur.execute("""SELECT floor_id,accesspoint.location_id,x,y,direction, GROUP_CONCAT(MAC) as MAC_list,GROUP_CONCAT(strength) as strength_list from accesspoint
 		join location on location.id=accesspoint.location_id
 		where location.id in (100,101,102,103,104) 
 		group by accesspoint.location_id,x,y,direction""")


def same(ap1, ap2):
	return 1 - ttest_ind(
		norm.rvs(loc=ap1.strength,scale=ap1.std,size=ap1.sample_size),
		norm.rvs(loc=ap2.strength,scale=ap2.std,size=ap2.sample_size),
		equal_var = False)[1]


if __name__ = "__main__":
	main()