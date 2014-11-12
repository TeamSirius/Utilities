# Brett (Berty) Fischler and Hunter (Kenneth) Wapman
# October 2014
# kNN Implementation for Senior Design Project

from collections import Counter
import sets
import math
import json
from pprint import pprint
import sys

# Minimum normalized RSSI value detected; used as "not detected" value
MIN_DETECTED = 0

# Access Point class
class AccessPoint(object):
    def __init__(self, ap):
        self.mac = ap[0]
        self.strength = ap[1]
        self.std = ap[2]
        self.datetime = ap[3]

# Location Class
class Location(object):
    def __init__(self, loc):
        self.x = loc[0]
        self.y = loc[1]
        self.durrrr = loc[2]
        self.floor_id = loc[3]
        self.init_aps(loc[4])

    def printLoc(self):
        sys.stdout.write("Location: (x, y) = (" + str(self.x) + ", " + str(self.y) + ")\n")

    # Stores Access Points in a {mac_id : AccessPoint} dictionary
    def init_aps(self, aps):
        self.aps = {}
        for ap in aps:
            self.aps[ap[0]] = AccessPoint(ap)

    # Calculates distance between this Location and the given dictionary of
    # AccessPoints (currently calls function to calculate Euclidean distance)
    def get_distance(self, aps):
        distances = []
        keys = sets.Set()
        for mac_id in aps.keys():
            keys.add(mac_id)
        for mac_id in self.aps.keys():
            keys.add(mac_id)
        return euclidean(keys, self.aps, aps)

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
    rVal = math.sqrt(rVal)
    return rVal

# Given a list of tuples where t[0] is the value and t[1] is the distance,
# returns a weighted average of the values
def weighted_avg(tuples):
    ### If we want the unweighted average:
    #return sum([t[0] for t in tuples]) / len(tuples)
    s = 0
    if tuples[0][1] == 0:
            return tuples[0][0]
    weight_sum = sum([1 / t[1] for t in tuples])
    for t in tuples:
        s += t[0] * (1 / t[1]) / weight_sum
    return s


# Uses k - Nearest Neighbor technique to get the coordinates associated with
# the given AccessPoint dictionary
def kNN(data, aps, k = 7):
    k = min(k, len(data))
    data = sorted(data, key=lambda x: x.get_distance(aps))
    d = Counter([loc.floor_id for loc in data[:k]])
    floor = d.most_common(1)[0][0]
    x = weighted_avg([(loc.x, loc.get_distance(aps)) for loc in data[:k]])
    y = weighted_avg([(loc.y, loc.get_distance(aps)) for loc in data[:k]])
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
def get_locations(filename):
    json_data = open(filename)
    data = json.load(json_data)
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
    return [Location(i) for i in locations]


# Returns a list of Locations and an AccessPoint dictionary
# Note: Right now, the data is hard-coded. It shouldn't be.
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

    new_aps = [(3,-55,2,2), (4,-75,4,1)]

    formatted_data = [Location(i) for i in data]
    formatted_aps = {}
    for ap in new_aps:
        formatted_aps[ap[0]] = AccessPoint(ap)
    return (formatted_data, formatted_aps)

# Gets and normalizes training Location data and current AccessPoint strengths
# Runs kNN algorithm to predict current location and floor
def demo(cur_data):
    data = get_locations("access_points.json")
    cur_loc = get_data_locations(cur_data)
    cur_aps = cur_loc[0].aps
    normalize(data, cur_aps)
    (x, y, floor) = kNN(data, cur_aps)
    return (x,y)

if __name__ == '__main__':
    main()
