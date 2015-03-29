# Brett (Berty) Fischler and Hunter (Kenneth) Wapman
# October 2014
# kNN Implementation for Senior Design Project

from collections import Counter
import sets
import math
import sys
import os
from math import isinf

# Minimum normalized RSSI value detected; used as "not detected" value
MIN_DETECTED = 0
COEFF_JACCARD = 3
COEFF_EUCLIDEAN = 1
COEFF_DENSITY = .112

MAC_COUNTS = {}

#########################
### CLASS DEFINITIONS ###
#########################

# Access Point class
class AccessPoint(object):
    def __init__(self, ap, from_django=False):

        if not from_django:
            self.mac = ap[0]
            self.strength_dbm = float(ap[1])
            self.strength = self.strength_dbm
            #self.strength = 10 ** (float(ap[1]) / 10)
            self.std = 10 ** (float(ap[2]) / 10)
            self.datetime = ap[3]

        else:
            self.mac = ap['mac_address']
            self.strength_dbm = ap['signal_strength']
            self.strength = self.strength_dbm
            #self.strength = 10 ** (self.strength_dbm / 10)
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

    def printLoc(self):
        sys.stdout.write("Location: (x, y) = (" + str(self.x) + ", " + str(self.y) + \
                "), Floor = " + str(self.floor_id) + "\n")

    # Stores Access Points in a {mac_id : AccessPoint} dictionary
    def init_aps(self, aps):
        self.aps = {}
        for ap in aps:
            self.aps[ap[0]] = AccessPoint(ap)


##########################
### DISTANCE FUNCTIONS ###
##########################

# Returns a set of shared keys between the two given AP dictionaries
def getSharedKeys(aps1, aps2):
    keys = sets.Set()
    for mac_id in aps1.keys():
        keys.add(mac_id)
    for mac_id in aps2.keys():
        keys.add(mac_id)
    return keys

#Calculates distance between this Location and the given dictionary of
#AccessPoints (currently calls function to calculate Euclidean distance)
def kNNDistance(aps1, aps2, density = 0):
    distances = []
    euc_dist = euclidean(aps1, aps2)
    jaccard = jaccardDistance(aps1, aps2)
    if jaccard == 0:
        return float("INF")
    #return 1 / percent_shared + 1.5 * euc_dist
    return (COEFF_JACCARD / jaccard) + (COEFF_EUCLIDEAN * euc_dist)  + (COEFF_DENSITY * density)

# Given two dictionaries of AccessPoints, calculates the
# Euclidean distance between the two dictionaries
def euclidean(aps1, aps2):
    global MIN_DETECTED
    keys = getSharedKeys(aps1, aps2)
    rVal = 0
    for key in keys:
        strength1 = MIN_DETECTED
        if key in aps1:
            strength1 = aps1[key].strength
        strength2 = MIN_DETECTED
        if key in aps2:
            strength2 = aps2[key].strength
        rVal = rVal + ((strength1 - strength2) ** 2)
    return math.sqrt(rVal)

def jaccardDistance(aps1, aps2):
    count = 0
    for ap in aps2.values():
        if ap.mac in aps1.keys():
            count += 1
    intersection = count
    union = len(aps1.keys()) + len(aps2.keys()) - count
    return float(intersection) / union


def realDistance(d1, d2):
    if d1 is None or d2 is None:
        return 0
    return math.sqrt(pow(d1.x - d2.x, 2) + pow(d1.y - d2.y, 2))


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
            #print t[0]
            return t[0]
        if inverse:
            s += t[0] * (1 / t[1]) / weight_sum
        else:
            s += t[0] * t[1] / weight_sum
    return s



# Uses k - Nearest Neighbor technique to get the coordinates associated with
# the given AccessPoint dictionary
def apply_kNN(data, aps, k = 4, element = None):
    k = min(k, len(data))
    floor = getFloor(data, aps)
    for d in data:
        if d.floor_id == floor:
            d.distance = kNNDistance(d.aps, aps, density=d.density)
            #d.distance = euclidean(d.aps, aps)
            #d.distance = 1 / jaccardDistance(d.aps, aps)
        else:
            d.distance = float("INF")
    data = sorted(data, key=lambda x: x.distance)
    #data = sorted(data, key=lambda x: realDistance(element, x))
    #for d in data:
    #   print jaccardDistance(aps, d.aps), "->", euclidean(aps, d.aps), "->", kNNDistance(aps, d.aps, density=d.density), "->", d.density, "->", realDistance(d, element)
    x = weighted_avg([(loc.x, loc.distance) for loc in data[:k]], True)
    y = weighted_avg([(loc.y, loc.distance) for loc in data[:k]], True)
    return (x, y, floor, data[:k])

def getFloor(data, aps, k = 5):
    k = min(k, len(data))
    data = sorted(data, key=lambda d: jaccardDistance(d.aps, aps), reverse=True)
    d = Counter([loc.floor_id for loc in data[:k]])
    floor = d.most_common(1)[0][0]
    return floor

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

##########################
### GET DATA FUNCTIONS ###
##########################

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


###############################
### NORMALIZATION FUNCTIONS ###
###############################

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

# BRETT NORMALIZE FUNCTION
def normalize_all_data(data, testdata):
    global MIN_DETECTED
    global MAC_COUNTS
    strengths = []
    for loc in data:
        for ap in loc.aps.values():
            strengths.append(ap.strength)
            if ap.mac not in MAC_COUNTS.keys():
                MAC_COUNTS[ap.mac] = 0
            MAC_COUNTS[ap.mac] += 1
    mean = get_mean(strengths)
    st_dev = get_sd(strengths)
    for loc in data:
        for ap in loc.aps.values():
            ap.strength = (ap.strength - mean) / st_dev
            if ap.strength < MIN_DETECTED:
                MIN_DETECTED = ap.strength
    for loc in testdata:
        for ap in loc.aps.values():
            ap.strength = (ap.strength - mean) / st_dev
            if ap.mac not in MAC_COUNTS.keys():
                MAC_COUNTS[ap.mac] = 0
            MAC_COUNTS[ap.mac] += 1

def normalize_all_data2(data, testdata):
    global MIN_DETECTED
    global MAC_COUNTS

    minstrength = sys.maxint
    maxstrength = -1 * sys.maxint - 1
    strengths = []
    for loc in data:
        for ap in loc.aps.values():
            strengths.append(ap.strength)
            if ap.strength < minstrength:
                minstrength = ap.strength
            if ap.strength > maxstrength:
                maxstrength = ap.strength
            if ap.mac not in MAC_COUNTS.keys():
                MAC_COUNTS[ap.mac] = 0
            MAC_COUNTS[ap.mac] += 1
    for loc in data:
        for ap in loc.aps.values():
            ap.strength = (ap.strength - minstrength) / (maxstrength - minstrength)
            if MIN_DETECTED > ap.strength:
                MIN_DETECTED = ap.strength
    for loc in testdata:
        for ap in loc.aps.values():
            ap.strength = (ap.strength - minstrength) / (maxstrength - minstrength)


##########################
### ANALYSIS FUNCTIONS ###
##########################

def error(element, x, y, floor):
    if element.floor_id == 6 and floor != 2:
        return -1
    elif element.floor_id == 15 and floor != 1:
        return -1
    elif element.floor_id < 3 and element.floor_id != floor:
        return -1
    else:
        dist = math.sqrt(pow(element.x - x, 2) + pow(element.y - y, 2))
    return dist

def addDensities(data):
    for i in range(len(data)):
        count = 1
        loc1 = data[i]
        for j in range(len(data)):
            loc2 = data[j]
            if i == j or loc1.floor_id != loc2.floor_id:
                continue
            if loc1.floor_id == 1:
                den_threshold = 9.555 * 10
            else:
                den_threshold = 14.764 * 10
            if realDistance(loc1,loc2) < den_threshold:
                count += 1
        loc1.density = count

def testAccuracy(data, testdata):
    wrong_floor_count = 0
    error_total = 0
    distances = [0] * 10 # [0-1 meter, 1-2, 2-3, etc]
    # 7, 8, 12, 16
    #our_points = [2, 4, 6, 7, 13, 17]
    our_points = range(19)
    testdata = [d for (i, d) in enumerate(testdata) if i in our_points]
    for i in range(len(testdata)):
        element = testdata[i]
        aps = element.aps
        (x, y, floor, neighbors)  = apply_kNN(data, aps, element = element)
        cur_error = error(element, x, y, floor)
        if cur_error == -1:
            print "Wrong floor"
            wrong_floor_count += 1
        else:
            print element.x, element.y, x, y
            for n in neighbors:
                print n.x, n.y, n.density
            #For Halligan_2.png, 14.764px ~= 1 meter
            #For Halligan_1.png 9.555px ~= 1 meter
            if floor == 1: #id NOT FLOOR NUMBER!!
                print i, cur_error / 14.764
                error_total += cur_error / 14.764
                distances[min(int(cur_error / 14.764), 9)] += 1
            else:
            #    if cur_error / 9.555 > 9:
            #        print i, cur_error / 9.555
                error_total += cur_error / 9.555
                distances[min(int(cur_error / 9.555), 9)] += 1
    print "FOR " + str(len(testdata)) + " POINTS:"
    print "Incorrect Floor Count:", wrong_floor_count
    print "Avg error: " + str(float(error_total) / (len(testdata) - wrong_floor_count)) + "m"
    print "Distances:", distances
    print ""
    return float(error_total) / len(testdata)

if __name__ == "__main__":
    sql_data = getData()
    all_data = get_locations(sql_data)
    data = [d for d in all_data if d.floor_id < 3]
    testdata = [d for d in all_data if d.floor_id == 7]
    addDensities(data)
    normalize_all_data(data, testdata)
    testAccuracy(data, testdata)
    sys.exit(1)
    global COEFF_DENSITY
    global COEFF_JACCARD
    COEFF_DENSITY = 0
    COEFF_JACCARD = 3
    best_density = 0
    best_jaccard =0
    best_val = 100
    for i in range(1):
        COEFF_DENSITY = .1
        for j in range(10):
            cur_error = testAccuracy(data, testdata)
            if cur_error < best_val:
                best_density = COEFF_DENSITY
                best_jaccard = COEFF_JACCARD
                best_val = cur_error
            COEFF_DENSITY += .004
        COEFF_JACCARD += .2
    print "BEST ERROR:", best_val
    print "BEST COEFFS:", best_jaccard, best_density
