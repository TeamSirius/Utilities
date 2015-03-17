# Brett (Berty) Fischler and Hunter (Kenneth) Wapman
# October 2014
# kNN Implementation for Senior Design Project

from collections import Counter
import sets
import math
import sys
import os
from math import isinf


#-------------
# CONSTANTS
#-------------

COEFF_JACCARD = 3
COEFF_EUCLIDEAN = 1
COEFF_DENSITY = .112

# Minimum normalized RSSI value detected; used as "not detected" value
MIN_DETECTED = 0

MAXINT = sys.maxint
MININT = (MAXINT * -1) - 1

# TODO: Either incorporate this or get rid of it
MAC_COUNTS = {}

#---------------------
# CLASS DEFINITIONS 
#---------------------

class AccessPoint(object):
    """ AccessPoint Object """
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

class Location(object):
    """ Location Object """
    def __init__(self, loc):
        self.x = loc[0]
        self.y = loc[1]
        self.direction = loc[2]
        self.floor_id = loc[3]
        self.init_aps(loc[4])

    # Stores Access Points in a {mac_id : AccessPoint} dictionary
    def init_aps(self, aps):
        """ Stores the AccessPoint list in a {mac_id : AccessPoint } dict """
        self.aps = {}
        for ap in aps:
            self.aps[ap[0]] = AccessPoint(ap)


#-------------------
# DEBUGGING TOOLS
#-------------------

def printToFile():
    return



#----------------------
# DISTANCE FUNCTIONS
#----------------------

def getSharedKeys(aps1, aps2):
    """ Returns a set of shared keys between the two given AP dictionaries """
    keys = sets.Set()
    for mac_id in aps1.keys():
        keys.add(mac_id)
    for mac_id in aps2.keys():
        keys.add(mac_id)
    return keys

def kNNDistance(aps1, aps2, density = 0):
    """ Returns distance between the given AccessPoint dicts.
    Takes Jaccard coefficient, Euclidean distance, and density into account.
    """
    distances = []
    euc_dist = euclidean(aps1, aps2)
    jaccard_dist = jaccard(aps1, aps2)
    if jaccard_dist == 0:
        return float("INF")
    return (COEFF_JACCARD / jaccard_dist) + (COEFF_EUCLIDEAN * euc_dist) +\
            (COEFF_DENSITY * density)

def euclidean(aps1, aps2):
    """ Returns the Euclidean distance between the given AccessPoint dicts """
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

def jaccard(aps1, aps2):
    """ Returns the Jaccard coeff between the given AccessPoint dicts """
    count = 0
    for ap in aps2.values():
        if ap.mac in aps1.keys():
            count += 1
    intersection = count
    union = len(aps1.keys()) + len(aps2.keys()) - count
    return float(intersection) / union


def realDistance(d1, d2):
    """ Returns the real distance between the two given Location objects """
    if d1 is None or d2 is None:
        return 0
    return math.sqrt(pow(d1.x - d2.x, 2) + pow(d1.y - d2.y, 2))


#-----------------
# kNN FUNCTIONS
#-----------------

def weighted_avg(tuples, inverse):
    """ Given a list of tuples (t[0] is the value and t[1] is the distance),
    returns a weighted average of the values. If inverse == True, we use the
    inverse of the given weights.
    """
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

def applykNN(data, aps, k = 4, element = None):
    """ Uses kNN technique to locate the given AccessPoint dict """
    k = min(k, len(data))
    floor = getFloor(data, aps)
    for d in data:
        if d.floor_id == floor:
            d.distance = kNNDistance(d.aps, aps, density=d.density)
        else:
            d.distance = float("INF")
    data = sorted(data, key=lambda x: x.distance)
    #data = sorted(data, key=lambda x: realDistance(element, x))
    #for d in data:
    #   print jaccard(aps, d.aps), "->", euclidean(aps, d.aps), "->", kNNDistance(aps, d.aps, density=d.density), "->", d.density, "->", realDistance(d, element)
    x = weighted_avg([(loc.x, loc.distance) for loc in data[:k]], True)
    y = weighted_avg([(loc.y, loc.distance) for loc in data[:k]], True)
    return (x, y, floor, data[:k])

def getFloor(data, aps, k = 5):
    """ Uses kNN technique to find the floor of the given AccessPoint dict """
    k = min(k, len(data))
    data = sorted(data, key=lambda d: jaccard(d.aps, aps), reverse=True)
    d = Counter([loc.floor_id for loc in data[:k]])
    floor = d.most_common(1)[0][0]
    return floor


#----------------------
# GET DATA FUNCTIONS
#----------------------

def getLocations(data):
    """ Returns an array of Location objects corresponding to the given data"""
    locations = []
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


#---------------------------
# NORMALIZATION FUNCTIONS
#---------------------------

def get_sd(l):
    """ Returns the standard deviation of the given list """
    mean = get_mean(l)
    rVal = 0
    for elem in l:
        rVal += (elem - mean) ** 2
    return (rVal / (len(l) - 1)) ** .5

def get_mean(l):
    """ Returns the mean of the given list """
    return sum(l) / len(l)

def normalize(data):
    """ Normalizes the given data and returns the mean and standard dev """
    global MIN_DETECTED
    global MAC_COUNTS # TODO: Get rid of this if we don't incorporate it
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
    return (mean, st_dev)

def normalizeAPs(aps, mean, st_dev):
    """ Normalizes the given AccessPoint dict """
    for ap in aps.values():
        ap.strength = (ap.strength - mean) / st_dev


#----------------------
# ANALYSIS FUNCTIONS
#----------------------

def error(element, x, y, floor):
    """ Returns the error between the given element and our x and y vals """
    if element.floor_id == 7 and floor != 2:
        return -1
    elif element.floor_id == 15 and floor != 1:
        return -1
    elif element.floor_id < 3 and element.floor_id != floor:
        return -1
    else:
        dist = math.sqrt(pow(element.x - x, 2) + pow(element.y - y, 2))
    return dist

def addDensities(data):
    """ Adds the density of points around each Location as a Location member """
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

def testAccuracy():
    """ Pulls data from the database, runs kNN on each test point, and prints
    results to various files
    """
    sql_data = getData()
    all_data = getLocations(sql_data)
    data = []
    testdata = []
    for d in all_data:
        if d.floor_id < 3:
            data.append(d)
        else:
            testdata.append(d)
    addDensities(data)
    (mean, st_dev) = normalize(data)
    wrong_floor_count = 0
    error_total = 0
    distances = [0] * 10 # [0-1 meter, 1-2, 2-3, etc]
    for i in range(len(testdata)):
        element = testdata[i]
        aps = element.aps
        normalizeAPs(aps, mean, st_dev)
        (x, y, floor, neighbors)  = applykNN(data, aps, element = element)
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
    testAccuracy()
