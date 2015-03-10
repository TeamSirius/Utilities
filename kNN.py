# Brett (Berty) Fischler and Hunter (Kenneth) Wapman
# October 2014
# kNN Implementation for Senior Design Project

from collections import Counter
from scipy.stats import ttest_ind,norm
import sets
import math
import sys
import os
from math import isinf

# Minimum normalized RSSI value detected; used as "not detected" value
MIN_DETECTED = 0


# Access Point class
class AccessPoint(object):
    def __init__(self, ap, from_django=False):
        if not from_django:
            self.mac = ap[0]
            self.strength_dbm = float(ap[1])
            self.strength = 10 ** (float(ap[1]) / 10)
            self.std = 10 ** (float(ap[2]) / 10)
            self.datetime = ap[3]
        else:
            self.mac = ap['mac_address']
            self.strength_dbm = ap['signal_strength']
            self.strength = 10 ** (self.strength_dbm / 10)
            self.std = 10 ** (ap['standard_deviation'] / 10)
            self.datetime = ap['recorded']

# Location Class
# TODO: Look into storing previous distance calculations
class Location(object):
    def __init__(self, loc):
        self.x = loc[0]
        self.y = loc[1]
        self.direction = loc[2]
        self.floor_id = loc[3]
        self.init_aps(loc[4])

    def __repr__(self):
        return "Location: (x, y) = ({}. {}), Floor = {}\n".format(self.x,self.y,self.floor_id)

    # Stores Access Points in a {mac_id : AccessPoint} dictionary
    def init_aps(self, aps):
        self.aps = {}
        for ap in aps:
            self.aps[ap[0]] = AccessPoint(ap)

    #Calculates distance between this Location and the given dictionary of
    #AccessPoints (currently calls function to calculate Euclidean distance)
    def get_distance(self, aps,gamma = 0.005 ):
        distances = []
        keys = sets.Set()
#        keys = set( aps.keys() ).intersection( set(self.aps.keys()) )
        keys = set( aps.keys() + self.aps.keys() )
        euc_dist = euclidean(keys, self.aps, aps)
        percent_shared = jaccardDistance(self.aps.keys(),aps.keys())
        if percent_shared == 0:
            return float("INF")
        return (1 / percent_shared) + (1.5 * euc_dist)  + (gamma * self.density)

# Given a set of mac_ids and two dictionaries of AccessPoints, calculates the
# Euclidean distance between the two dictionaries
def euclidean(keys, aps1, aps2):
    rVal = 0
    for key in keys:
        strength1 = MIN_DETECTED
        strength2 = MIN_DETECTED
        if key in aps1:
            strength1 = aps1[key].strength
        strength1 = 10 ** (strength1 / 10)
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
            return t[0]
        if inverse:
            s += t[0] * (1 / t[1]) / weight_sum
        else:
            s += t[0] * t[1] / weight_sum
    return s


def jaccardDistance(aps1, aps2):
    set1 = set(aps1)
    set2 = set(aps2)
    return float(len(set1.intersection(set2))) / len(set1.union(set2))


def realDistance(d1, d2):
    if d1 is None or d2 is None:
        return 0
    return math.sqrt(pow(d1.x - d2.x, 2) + pow(d1.y - d2.y, 2))

# Uses k - Nearest Neighbor technique to get the coordinates associated with
# the given AccessPoint dictionary
def apply_kNN(data, aps, k = 3):
    k = min(k, len(data))
    for d in data:
        d.distance = d.get_distance(aps)
    data = sorted(data, key=lambda x: x.distance)
    #TODO: Reconsider avg vs. mode
    d = Counter([loc.floor_id for loc in data[:(k * 2 - 1)]])
    floor = d.most_common(1)[0][0]
    data = filter(lambda d: d.floor_id == floor, data)
    # data = [d for d in data if d.floor_id == floor]
    x = weighted_avg([(loc.x, loc.distance) for loc in data[:k]], True)
    y = weighted_avg([(loc.y, loc.distance) for loc in data[:k]], True)
    return (x, y, floor)

# Returns the standard deviation of the given list
def get_sd(l,mean=None):
    if not mean:
        mean = get_mean(l)
    rVal = 0
    for elem in l:
        rVal += (elem - mean) ** 2
    return (rVal / (len(l) - 1)) ** .5

# Returns the mean of the given list
def get_mean(l):
    return sum(l) / len(l)


# Returns a list of Locations and an AccessPoint dictionary
def get_locations(data):
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

def getData(db_cursor=None):
    if db_cursor is None:
        from scripts.db.db import Database
        password = os.environ.get('SIRIUS_PASSWORD')
        if password is None:
            raise Exception('No database password available')

        db = Database(password)

        cur = db.get_cur()
    else:
        cur = db_cursor
    cur.execute("""SELECT floor_id,marauder_accesspoint.location_id, x_coordinate, y_coordinate, direction,
         array_to_string(array_agg(mac_address),',') as MAC_list,
         array_to_string(array_agg(signal_strength),',') as strength_list 
         from marauder_accesspoint 
         join marauder_location 
            on marauder_location.id=marauder_accesspoint.location_id
         group by floor_id,marauder_accesspoint.location_id,x_coordinate,y_coordinate,direction""")
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

def kNN(test_aps, db_cursor=None):
    test_aps = {ap['mac_address'] : AccessPoint(ap, from_django=True) for ap in test_aps}
    trained_data = getData(db_cursor=db_cursor)
    locations = get_locations(trained_data)
    normalize(trained_data, test_aps)
    return apply_kNN(trained_data, test_aps)

# NORMALIZE FUNCTION
def normalize_all_data(data, testdata):
    global MIN_DETECTED
    strengths = []
    for loc in data:
        for ap in loc.aps.values():
            strengths.append(ap.strength)
    mean = get_mean(strengths)
    st_dev = get_sd(strengths,mean)
    for loc in data:
        for ap in loc.aps.values():
            ap.strength = (ap.strength - mean) / st_dev
            if ap.strength < MIN_DETECTED:
                MIN_DETECTED = ap.strength
    for loc in testdata:
        for ap in loc.aps.values():
            ap.strength = (ap.strength - mean) / st_dev
            if ap.strength < MIN_DETECTED:
                MIN_DETECTED = ap.strength

# TEST STUFF
def testAccuracy():
    sql_data = getData()
    all_data = get_locations(sql_data)

    DEN_THRESHOLD = 9.555 * 20 # Number of points within 20m

    # dens = []
    for i in range(len(all_data)):
        count = 1
        loc1 = all_data[i]
        for j in range(len(all_data)):
            if i == j:
                continue
            loc2 = all_data[j]
            if realDistance(loc1,loc2) < DEN_THRESHOLD:
                count += 1
        loc1.density = count
    #     dens.append(count)
    # dens_mean = float(get_mean(dens))
    # dens_sd = float(get_sd(dens,dens_mean))
    # n_dens = [ (x - dens_mean) / dens_sd  for x in dens ]
    # for i in range(len(n_dens)):
    #     n = n_dens[i]
    #     if n <= -.5 and all_data[i].floor_id == 2:
    #         print all_data[i].x,all_data[i].y
    data = []
    testdata = []
    for d in all_data:
        if d.floor_id == 3:
            testdata.append(d)
        else:
            data.append(d)
    normalize_all_data(data, testdata)
    wrong_floor_count = 0
    error_total = 0
    distances = {}
    for i in range(len(testdata)):
        element = testdata[i]
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
                distances[int(cur_error / 14.764)] = distances.get(int(cur_error / 14.764),0) + 1
            else:
                error_total += cur_error / 9.555
                distances[int(cur_error / 9.555)] = distances.get(int(cur_error / 9.555),0) + 1
    if wrong_floor_count == len(testdata):
        print "All floors wrong"
        exit(0)
    print "Total points: {}".format(len(testdata))
    print "Error Histogram"
    sorted_keys = sorted(distances.keys())
    max_key = int(sorted_keys[-1])
    max_val = max(distances.values())
    for i in range(max_key):
        if i not in distances:
            distances[i] = 0
    for k in range(max_key + 1):
        i = int(k)
        start = str(i).rjust(2)
        end = str(i + 1).rjust(2)
        row = "#" * distances[k]
        row = row.ljust(max_val)
        print "{} to {}m: {} {}".format(start,end,row,distances[k])
    print "Incorrect Floor Count: {}".format(wrong_floor_count)
    print "Average Error: {}m".format(round(float(error_total) / (len(testdata) - wrong_floor_count),2))

def error(element, x, y, floor):
    if element.floor_id == 3 and floor != 2:
        return -1
    elif element.floor_id != 3 and element.floor_id != floor:
        return -1
    else:
        dist = math.sqrt(pow(element.x - x, 2) + pow(element.y - y, 2))
    return dist


if __name__ == "__main__":
    testAccuracy()
