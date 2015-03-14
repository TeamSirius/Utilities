# Usage:
#   - python this_script path_to_image
#
# Purpose:  This script generates random test points using Mitchel's Best Candidate-II
#           algorithm. These points are displayed on the input image.
#
#           The user can also designate rectangles for those random points to be
#           generated within.
#
#           We use this utility to create random points within areas of a building we
#           have mapped.

import sys
from sys import argv, stderr, exit
from PIL import Image, ImageTk
from random import random
import Tkinter
import requests
from requests.exceptions import HTTPError
import json
import os
import math
from server_interface import ServerInterface

APP = {}  # contains global information needed by tkinter functions
NUM_POINTS = 2  # number of vertices in a rectangle
NUM_TEST_POINTS = 20  # Number of test points we want
NUM_CANDIDATES = 500  # Number of attempts per test point chosen
SERVER_URL = "http://mapbuilder.herokuapp.com/"
FID = -1 # Floor ID

SERVER = None
FLOOR_NAME = None

class Point(object):

    """ Point Object """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def save(self, fid, c):
        """Given a floor id and counter will create a point in the database"""
        n = c()
        name = '{} TEST: {}'.format(FLOOR_NAME, n)

        data = {
            'x_coordinate': self.x,
            'y_coordinate': self.y,
            'short_name': n,
            'verbose_name': name,
            'direction': 0,
            'floor': FID
        }

        try:
            SERVER.post(ServerInterface.LOCATION, data)
            print('Saved {} at ({},{})'.format(name, self.x, self.y))
        except HTTPError, e:
            print >> sys.stderr, e
            print >> sys.stderr, 'Unable to save {}'.format(name)


class Rectangle(object):

    """ Rectangle Object """

    def __init__(self, corners):
        if len(corners) != 2:
            stderr.write("not enough corners.\n")
            exit()

        p1 = corners[0]
        p2 = corners[1]

        self.XL = min(p1.x, p2.x)
        self.XR = max(p1.x, p2.x)
        self.YT = min(p1.y, p2.y)
        self.YB = max(p1.y, p2.y)

    def corners(self):
        return [Point(self.XL, self.YT),
                Point(self.XR, self.YT),
                Point(self.XR, self.YB),
                Point(self.XL, self.YB)]

    def contains(self, point):
        """ Checks whether the given rectangle contains the given point """
        if ((self.XL <= point.x <= self.XR) and
                (self.YT <= point.y <= self.YB)):
            return True
        else:
            return False


def getRandomPoints():
    """ Gets and returns a list of random Points """
    test_points = []
    while len(test_points) < NUM_TEST_POINTS:
        new_point = bestCandidate(test_points)
        test_points.append(new_point)
    return test_points


def bestCandidate(test_points):
    """ Runs Mitchell's Best-Candidate II Algorithm to generate a dispersed random Point """
    if len(test_points) == 0:
        return getCandidatePoint()
    bestDistance = 0
    for i in range(NUM_CANDIDATES):
        c = getCandidatePoint()
        d = distance(findClosest(test_points, c), c)
        if d > bestDistance:
            best = c
    return best


def getCandidatePoint():
    """ Returns a random Point in the image within at least one of the rectangles """
    global APP
    if APP['rectangles'] == []:
        return RandomPoint()

    attempts = 0  # Caps total number of tries allowed
    while(attempts < 1000000):
        point = RandomPoint()
        for rectangle in APP['rectangles']:
            if rectangle.contains(point):
                return point
        attempts += 1
    stderr.write("rectangle space too small to find point\n")
    exit()


def findClosest(test_points, point):
    """ Given a set of Points, and a point returns the closest Point to the point """
    min_distance = math.sqrt(APP['dims']['w'] ** 2 + APP['dims']['h'] ** 2)
    closest = None
    for test_point in test_points:
        cur_distance = distance(point, test_point)
        if cur_distance < min_distance:
            closest = test_point
            min_distance = cur_distance
    return closest

#--------------------------------
# Misc Utility Functions Below
#--------------------------------


def distance(a, b):
    """ Returns the distance between the given two Points """
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)


def rand(minimum, maximum):
    """ Returns a random number between minimum and maximum """
    return random() * (maximum - minimum) + minimum


def counter():
    """Creates a counter instance"""
    x = [0]

    def c():
        x[0] += 1
        return x[0]
    return c

def RandomPoint():
    """ generates a Point object within the image space """
    global APP
    return Point(rand(0, APP['dims']['w']), rand(0, APP['dims']['h']))


def get_floor_info(imageName):
    """Requests a building name and floor number from the user
    If a floor with the supplied name and number exists, get the resource ID for it
    If it does not exists, create a new one and return its resource ID.
    Args: 
        imageName: A string with the location of an image for a floor
    Returns:
        The Resource ID for the floor and the name to use when posting new points
    """

    global SERVER
    try:
        building_name = raw_input("Building: ")
        floor_number = raw_input("Floor Number: ")
        building_name.replace(' ', '_')
        combined_name = "{} {}".format(building_name, floor_number)
        lookup_params = {
            'building_name__iexact': building_name, # iexact to account for capitalization
            'floor_number': floor_number
        }

        found, floor_info = SERVER.get_single_item(ServerInterface.FLOOR,
                                                   lookup_params)

        if found:
            return floor_info['resource_uri'], combined_name
        else:
            with open(imageName, 'rb') as image:
                post_payload = {
                    'building_name': building_name,
                    'floor_number': floor_number,
                }

                files = {
                    'image': image
                }

                floor_info = SERVER.post_with_files(ServerInterface.FLOOR,
                                                    post_payload,
                                                    files)
                return floor_info['resource_uri'], combined_name
    except HTTPError, e:
        print >> sys.stderr, e
        exit("Error finding floor id")

#--------------------------------
# TKinter Application Code Below
#--------------------------------


def initializeApp(image_path):
    """ Initializes data for app Binds tkinter buttons """
    global APP

    image = Image.open(image_path)
    width, height = image.size[0], image.size[1]

    APP['window'] = Tkinter.Tk()
    APP['frame'] = Tkinter.Frame(APP['window'])
    image_tk = ImageTk.PhotoImage(image)

    APP['canvas'] = Tkinter.Canvas(APP['frame'], width=width, height=height)
    APP['canvas'].create_image(width // 2, height // 2, image=image_tk)

    APP['dims'] = {'w': width, 'h': width}
    APP['buttons'] = getButtons()
    APP['rectangles'] = []
    APP['points'] = []
    APP['canvas_list'] = []

    APP['frame'].pack()
    APP['canvas'].pack()
    APP['buttons']['reset_btn'].pack(side='right')
    APP['canvas'].bind("<Button-1>", handle_click)
    APP['window'].mainloop()


def getButtons():
    """ Returns dict of buttons; will be added to app object"""
    buttons = {'log_btn': Tkinter.Button(APP['frame'], text="Log", command=log),
               'done_btn': Tkinter.Button(APP['frame'], text="Done", command=done),
               'reset_btn': Tkinter.Button(APP['frame'], text="Reset", command=reset)}
    return buttons


def draw_point(p, color):
    """ draws a point at the coordinates with the specified color """
    global APP

    radius = 5  # point radius
    new_canvas = APP['canvas'].create_oval(
        p.x - radius, p.y - radius, p.x + radius, p.y + radius, fill=color)

    APP['points'].append(p)
    APP['canvas_list'].append(new_canvas)

def draw_rectangle(rectangle, outline_color):
    """ draws a rectangle at the coordinates with the specified color """
    global APP

    corners = rectangle.corners()
    p1 = corners[0]
    p2 = corners[2]

    new_canvas = APP['canvas'].create_rectangle(
        p1.x, p1.y, p2.x, p2.y, outline=outline_color, width=2)

    APP['rectangles'].append(rectangle)
    APP['canvas_list'].append(new_canvas)


def handle_click(click):
    """ Adds a point to the canvas; if there are enough points, allows logging """
    global APP
    point = Point(click.x, click.y)

    num_points = len(APP['points']) + 1
    if num_points > NUM_POINTS:
        reset()
        APP['buttons']['log_btn'].pack_forget()
    elif num_points == NUM_POINTS:
        APP['buttons']['log_btn'].pack(side='left')

    draw_point(point, 'blue')


def log():
    """ generates the rest of the rectangle for drawing; asks for confirmation if input
        is correct.  """
    global APP
    APP['canvas'].unbind("<Button-1>")

    rectangle = Rectangle(APP['points'])
    reset()

    # command = raw_input("Confirm Points? [Y/N]")
    command = 'Y'
    if command.upper() == 'Y':
        draw_rectangle(rectangle, 'red')
        APP['buttons']['done_btn'].pack(side='right')
        APP['points'] = []
        APP['canvas_list'] = []
    else:
        reset()

    APP['buttons']['log_btn'].pack_forget()
    APP['canvas'].bind("<Button-1>", handle_click)


def done():
    """ activates the algorithm with the current set of rectangles. Generates random points
        within those rectangles. """
    APP['buttons']['done_btn'].pack_forget()
    APP['buttons']['log_btn'].pack_forget()
    APP['canvas'].unbind("<Button-1>")

    test_points = getRandomPoints()

    c = counter()
    for point in test_points:
        draw_point(point, 'green')
        APP['buttons']['reset_btn'].pack_forget()
        if not debug:
            global FID
            point.save(FID, c)


def reset():
    """ deletes unlogged points from the canvas """
    global APP
    for canvas in APP['canvas_list']:
        APP['canvas'].delete(canvas)

    APP['points'] = []
    APP['canvas_list'] = []


def main(argv, debug):
    if len(argv) != 4:
        print "Usage: python build_locations filename username password"
        exit(1)

    filename = argv[1]
    username = argv[2]
    password = argv[3]
    
    if not debug:
        global FID
        global FLOOR_NAME
        global SERVER
        SERVER = ServerInterface(username, password)
        FID, FLOOR_NAME = get_floor_info(filename)

    image_path = argv[1]
    initializeApp(image_path)

if __name__ == '__main__':
    debug = False
    main(argv, debug)
