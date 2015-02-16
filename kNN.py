# Brett (Berty) Fischler and Hunter (Kenneth) Wapman
# October 2014
# kNN Implementation for Senior Design Project

from collections import Counter
import sets
import math
import sys
import os
from scripts.db.db import Database
from math import isinf

# Minimum normalized RSSI value detected; used as "not detected" value
MIN_DETECTED = 0

password = os.environ.get('SIRIUS_PASSWORD')
if password is None:
    raise Exception('No database password available')

db = Database(password)

cur = db.get_cur()

# Access Point class
class AccessPoint(object):
    def __init__(self, ap):
        self.mac = ap[0]
        self.strength_dbm = float(ap[1])
        self.strength = 10 ** (float(ap[1]) / 10)
        self.std = 10 ** (float(ap[2]) / 10)
        self.datetime = ap[3]
        #self.sample_size = ap[4]

# Location Class
# TODO: Look into storing previous distance calculations
class Location(object):
    def __init__(self, loc):
        self.x = loc[0]
        self.y = loc[1]
        self.direction = loc[2]
        self.floor_id = loc[3]
        self.init_aps(loc[4])

    def printLoc(self):
        sys.stdout.write("Location: (x, y) = (" + str(self.x) + ", " + str(self.y) + ")\n")

    # Stores Access Points in a {mac_id : AccessPoint} dictionary
    def init_aps(self, aps):
        self.aps = {}
        for ap in aps:
            self.aps[ap[0]] = AccessPoint(ap)

    #Calculates distance between this Location and the given dictionary of
    #AccessPoints (currently calls function to calculate Euclidean distance)
    def get_distance1(self, aps):
        distances = []
        keys = sets.Set()
        for mac_id in aps.keys():
            keys.add(mac_id)
        for mac_id in self.aps.keys():
            keys.add(mac_id)
        euc_dist = euclidean(keys, self.aps, aps)
        percent_shared = float(len([ap for ap in aps.keys() if ap in self.aps.keys()])) / len(keys)
        if percent_shared == 0:
            return float("INF")
        return 1 / percent_shared + 1.5 * euc_dist

    def get_distance2(self, aps):
        num_similar = 0
        for mac_id in aps.keys():
            if mac_id in self.aps.keys():
                num_similar += 1
        return num_similar


    #def get_distance(self, aps):
    #    coeffA = 1
    #    coeffB = 1
    #   coeffC = 1
    #   keys1 = self.aps.keys()
    #   keys2 = aps.keys()
    #   intersection = [key for key in keys1 if key in keys2]
    #   if len(intersection) == 0:
    #       return sys.maxint
    #   size_shared = len(intersection)
    #   size_diff = len(keys1) + len(keys2) - 2 * size_shared
    #   probability = 0
    #   for key in intersection:
    #       probability += similarity(self.aps[key], aps[key])
    #   probability = float(probability) / len(intersection)
    #   return coeffA * size_shared + coeffB * size_diff + coeffC * probability"""

def similarity(ap1, ap2):
    from scipy.stats import ttest_ind,norm
    return 1 - ttest_ind(
	    norm.rvs(loc=ap1.strength,scale=ap1.std,size=ap1.sample_size),
	    norm.rvs(loc=ap2.strength,scale=ap2.std,size=ap2.sample_size),
	    equal_var = False)[1]

# Given a set of mac_ids and two dictionaries of AccessPoints, calculates the
# Euclidean distance between the two dictionaries
def euclidean(keys, aps1, aps2):
    rVal = 0
    for key in keys:
        strength1 = MIN_DETECTED
        if key in aps1:
            strength1 = aps1[key].strength
        strength1 = 10 ** (strength1 / 10)
        strength2 = MIN_DETECTED
        if key in aps2:
            strength2 = aps2[key].strength
        strength2 = 10 ** (strength2 / 10)
        rVal = rVal + (strength1 - strength2) ** 2
    return math.sqrt(rVal)


        # Given a list of tuples where t[0] is the value and t[1] is the distance,
# returns a weighted average of the values
def weighted_avg(tuples, inverse):
    ### If we want the unweighted average:
    #return sum([t[0] for t in tuples]) / len(tuples)
    s = 0
    for t in tuples:
        if t[1] == 0:
            return t[0]
    if inverse:
        weight_sum = sum([1 / t[1] for t in tuples])
    else:
        weight_sum = sum([t[1] for t in tuples])
    for t in tuples:
        if isinf(t[1]) or weight_sum == 0:
            print t[0]
            return t[0]
        if inverse:
            s += t[0] * (1 / t[1]) / weight_sum
        else:
            s += t[0] * t[1] / weight_sum
    return s


# Uses k - Nearest Neighbor technique to get the coordinates associated with
# the given AccessPoint dictionary
def apply_kNN(data, aps, k = 3):
    k = min(k, len(data))
    #data = sorted(data, key=lambda x: x.get_distance1(aps))
    for d in data:
        d.distance = d.get_distance1(aps)
    data = sorted(data, key=lambda x: x.distance)
    #TODO: Reconsider avg vs. mode
    d = Counter([loc.floor_id for loc in data[:(k * 2 - 1)]])
    floor = d.most_common(1)[0][0]
    data = [d for d in data if d.floor_id == floor]
    x = weighted_avg([(loc.x, loc.distance) for loc in data[:k]], True)
    y = weighted_avg([(loc.y, loc.distance) for loc in data[:k]], True)
    return (x, y, floor)


def apply_kNN_func(data, aps, func , k = 3):
    #function must take in two dictionaries from MAC : strength and return a strength
    k = min(k, len(data))
    #data = sorted(data, key=lambda x: x.get_distance1(aps))
    for d in data:
        d.distance =  func(aps, d.aps)
    data = sorted(data, key=lambda x: x.distance)
    #TODO: Reconsider avg vs. mode
    d = Counter([loc.floor_id for loc in data[:(k * 2 - 1)]])
    floor = d.most_common(1)[0][0]
    data = [d for d in data if d.floor_id == floor]
    x = weighted_avg([(loc.x, loc.distance) for loc in data[:k]], True)
    y = weighted_avg([(loc.y, loc.distance) for loc in data[:k]], True)
    return (x, y, floor)


# Returns the standard deviation of the given list
def get_sd(l):
    mean = get_mean(l)
    rVal = 0
    for elem in l:
        rVal += (elem - mean) ** 2
    return (rVal / (len(l) - 1)) ** .5

# Returns the mean of the given list
def get_mean(l):
    return sum(l) / len(l)

# Normalizes the signal strengths of all AccessPoints in the given array of
# Locations and the given AccessPoint dictionary
def normalize(data, aps):
    global MIN_DETECTED
    strengths = []
    for loc in data:
        for ap in loc.aps.values():
            strengths.append(ap.strength)
    for ap in aps.values():
        strengths.append(ap.strength)
    mean = get_mean(strengths)
    st_dev = get_sd(strengths)
    for loc in data:
        for ap in loc.aps.values():
            ap.strength = (ap.strength - mean) / st_dev
            if ap.strength < MIN_DETECTED:
                MIN_DETECTED = ap.strength
    for ap in aps.values():
        ap.strength = (ap.strength - mean) / st_dev
        if ap.strength < MIN_DETECTED:
            MIN_DETECTED = ap.strength



# Returns a list of Locations and an AccessPoint dictionary
def get_locations():
    data = getData()
    locations = []
    #sys.stderr.write("LENGTH: " + str(len(data)) + "\n")
    for d in data:
        cur_macs = d["macs"]
        cur_rss = d["rss"]
        cur_aps = []
        for i in range(len(cur_macs)):
            cur_aps.append((cur_macs[i], cur_rss[i], 0, 0))
        locations.append((d["x"], d["y"], d["direction"], d["floor_id"], cur_aps))
    return [Location(i) for i in locations]

def get_data_locations(data):
    locations = []
    for d in data:
        cur_macs = d["macs"]
        cur_rss = d["rss"]
        cur_aps = []
        for i in range(len(cur_macs)):
            cur_aps.append((cur_macs[i], cur_rss[i], 0, 0))
        locations.append((d["x"], d["y"], d["direction"], d["floor_id"], cur_aps))
        # TODO: Maybe take away list comprehension thing
    return [Location(i) for i in locations]

def get_data2():
    # Change this
    data = [(1,1,3,0,[(1,-66,1,1), (2, -60, 2, 2)]),
            (2,2,3,0,[(1,-55,1,1), (3, -45, 2, 2), (4, -55, 2, 2)]),
            (3,3,3,0,[(1,-80,1,1), (4, -70, 2, 2)]),
            (4,4,3,0,[(1,-55,1,1), (2, -85, 2, 2), (4, -55, 2, 2)]),
            (5,5,3,0,[(2,-80,1,1), (4, -70, 2, 2)]),
            (6,6,3,0,[(2,-55,1,1), (3, -55, 2, 2), (4, -55, 2, 2)]),
            (7,7,3,0,[(3,-60,1,1), (4, -70, 2, 2)]),
            (8,8,5,0,[(4,-50,3,3)])]

    new_aps = [(1,-66,2,2), (2,-64,4,1)]

    formatted_data = [Location(i) for i in data]
    formatted_aps = {}
    for ap in new_aps:
        formatted_aps[ap[0]] = AccessPoint(ap)
    return (formatted_data, formatted_aps)

def getData():
	cur.execute("""SET SESSION group_concat_max_len = 1000000""")
	cur.execute("""SELECT floor_id,accesspoint.location_id,x,y,direction, GROUP_CONCAT(MAC) as MAC_list,GROUP_CONCAT(strength) as strength_list from accesspoint
	 join location on location.id=accesspoint.location_id
	  group by accesspoint.location_id,x,y,direction""")
	access_points = cur.fetchall()
	res = []
	for f in access_points:
	    msg = {
	        'floor_id': f[0],
	        'location_id': f[1],
	        'x': f[2],
	        'y': f[3],
	        'direction': f[4],
	        'macs': f[5].split(','),
	        'rss': map(float, f[6].split(','))
	    }
	    res.append(msg)
	return res

def kNN(aps):
    data = get_locations()
    normalize(data, aps)
    (x, y, floor) = apply_kNN(data, aps)
    return (x, y, floor)

def getMinMax():
    dataa = get_locations()
    normalize(dataa[:-1], dataa[-1].aps)
    minx = 100000
    maxx = 0
    miny = 100000
    maxy = 0
    for data in dataa:
        if data.x < minx:
            minx = data.x
        if data.x > maxx:
            maxx = data.x
        if data.y < miny:
            miny = data.y
        if data.y > maxy:
            maxy = data.y
    return (minx, maxx, miny, maxy)

def error(element, x, y, floor):
    if element.floor_id != floor:
        return -1
    else:
        dist = math.sqrt(pow(element.x - x, 2) + pow(element.y - y, 2))
        return dist

def LOOCV():
    import subprocess as sp
    tmp = sp.call('clear', shell=True)
    print "RUNNING LOOCV TESTS"
    print ""
    data = get_locations()
    normalize(data[:-1], data[-1].aps) # Hacky way to normalize all data
    wrong_floor_count = 0
    error_total = 0
    distances = [0] * 10 # [0-1 meter, 1-2, 2-3, etc]
    for i in range(len(data)):
        element = data[i]
        data.remove(element)
        aps = element.aps
        (x, y, floor)  = apply_kNN(data, aps)
        cur_error = error(element, x, y, floor)
        if cur_error == -1:
            wrong_floor_count += 1
        else:
            #For Halligan_2.png, 14.764px ~= 1 meter
            #For Halligan_1.png 9.555px ~= 1 meter
            if floor == 1: #id NOT FLOOR NUMBER!!
                error_total += cur_error / 14.764
                distances[min(int(cur_error / 14.764), 9)] += 1
            else:
                error_total += cur_error / 9.555
                distances[min(int(cur_error / 9.555), 9)] += 1
        data.insert(i, element)
    print "FOR " + str(len(data)) + " POINTS:"
    print "Incorrect Floor Count:", wrong_floor_count
    print "Avg error: " + str(float(error_total) / (len(data) - wrong_floor_count)) + "m"
    print "Distances:", distances
    print ""


def LOOCV_func(data, distance_func ):
    wrong_floor_count = 0
    error_total = 0
    distances = [0] * 10 # [0-1 meter, 1-2, 2-3, etc]
    for i in range(len(data)):
        element = data[i]
        data.remove(element)
        aps = element.aps
        (x, y, floor)  = apply_kNN_func(data, aps,distance_func)
        cur_error = error(element, x, y, floor)
        if cur_error == -1:
            wrong_floor_count += 1
        else:
            #For Halligan_2.png, 14.764px ~= 1 meter
            #For Halligan_1.png 9.555px ~= 1 meter
            if floor == 1: #id NOT FLOOR NUMBER!!
                error_total += cur_error / 14.764
                distances[min(int(cur_error / 14.764), 9)] += 1
            else:
                error_total += cur_error / 9.555
                distances[min(int(cur_error / 9.555), 9)] += 1
        data.insert(i, element)
    #Returns wrong floor count, average error
    return wrong_floor_count, float(error_total) / (len(data) - wrong_floor_count)

def percent_same(L1, L2):
    fullList = L1 + L2
    unique = len(set(fullList))
    total = len(fullList)
    if total == 0:
        return 1
    return float(unique) / total

def overlap_distance(aps1,aps2):
    rVal = 0
    for mac,ap1 in aps1.iteritems():
        if mac in aps2:
            strength1 = 10 ** (ap1.strength / 10)
            strength2 = 10 ** (aps2[mac].strength / 10)
            rVal = rVal + (strength1 - strength2) ** 2
    return math.sqrt(rVal)


def make_dist_func(alpha,beta,delta):
    return lambda APS_1, APS_2:  (alpha - beta) * percent_same(APS_1.keys(),APS_2.keys()) + alpha + delta * overlap_distance(APS_1,APS_2)


def error_rate(missed_floors, average_error):
    return average_error

def wrapper():
    minError = sys.maxint
    minAlpha = sys.maxint
    minBeta = sys.maxint
    minDleta = sys.maxint
    data = get_locations()
    normalize(data[:-1], data[-1].aps) # Hacky way to normalize all data
    wrapper_data = {}
    wrapper_data["alpha"] = []
    wrapper_data["beta"] = []
    wrapper_data["delta"] = []
    wrapper_data["avgError"] = []
    wrapper_data["missed_floors"] = []
    for i in range(10):
        for j in range(10):
            for k in range(10):
                print "{} - {} - {}".format(i,j,k)
                alpha = i / 1.0 - 5
                beta = j / 1.0 - 5
                delta = k / 1.0 - 5
                dist_func = make_dist_func(alpha,beta,delta)
                (missed_floors, avgError) =LOOCV_func(data, dist_func)
                wrapper_data["alpha"].append(alpha)
                wrapper_data["beta"].append(beta)
                wrapper_data["delta"].append(delta)
                wrapper_data["avgError"].append(avgError)
                wrapper_data["missed_floors"].append(missed_floors)
    fp = open("wrapper_data.json","w+")
    import json
    fp.write( json.dumps(wrapper_data,indent=4) )
    fp.close()

if __name__ == "__main__":
    wrapper()
