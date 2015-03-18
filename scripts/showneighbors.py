# Usage:
#   - python this_script path_to_image input_file
#
# Purpose:  This script displays arrows between test points and their kNN estimates.
#
#           We use this utility to visualize the accuracy of our kNN algorithm.
#           have mapped.

from sys import argv, stderr, exit
from PIL import Image, ImageTk
import Tkinter
import json
import os
import math
import sys

APP = {}  # contains global information needed by tkinter functions

REAL_POINTS = []
GUESS_POINTS = []
NEIGHBORS = []
NUM_NEIGHBORS = 4
INDEX = 0

class Point(object):
    """ Point Object """

    def __init__(self, x, y, density=""):
        self.x = x
        self.y = y
        self.density=density

class Line(object):
    """ Line Object """

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.length = distance(p1, p2)

#--------------------------------
# Misc Utility Functions Below
#--------------------------------

def distance(a, b):
    """ Returns the distance between the given two Points """
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy)

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

    APP['canvas'] = Tkinter.Canvas(APP['frame'], width=width, height=height-50)
    APP['canvas'].create_image(width // 2, height // 2, image=image_tk)

    APP['dims'] = {'w': width, 'h': width}
    APP['buttons'] = getButtons()
    APP['points'] = []
    APP['lines'] = []
    APP['canvas_list'] = []

    APP['frame'].pack()
    APP['canvas'].pack()
    APP['buttons']['ready_btn'].pack(side='right')
    APP['window'].mainloop()


def getButtons():
    """ Returns dict of buttons; will be added to app object"""
    buttons = {'ready_btn': Tkinter.Button(APP['frame'], text="Begin", command=ready)}
    return buttons

def draw_point(p, color, text=""):
    """ draws a point at the coordinates with the specified color """
    global APP

    radius = 5  # point radius
    new_canvas = APP['canvas'].create_oval(
        p.x - radius, p.y - radius, p.x + radius, p.y + radius, fill=color)
    if text != "":
        APP['canvas_list'].append(new_canvas)
        new_canvas = APP['canvas'].create_text(
            p.x, p.y-15, text=str(text))

    APP['points'].append(p)
    APP['canvas_list'].append(new_canvas)

def draw_line(line, color):
    """ draws the given line with the specified color """
    global APP
    new_canvas = APP['canvas'].create_line(
            line.p1.x, line.p1.y, line.p2.x, line.p2.y, fill=color,
            width=1, arrow=Tkinter.FIRST)
    APP['lines'].append(line)
    APP['canvas_list'].append(new_canvas)

def ready():
    """ Displays connections between test points and predictions """

    global REAL_POINTS, GUESS_POINTS, NEIGHBORS, INDEX
    if INDEX == 0:
        global APP
        readPoints()
        APP['buttons']['ready_btn']["text"] = "Next point"
    elif INDEX == len(REAL_POINTS): 
        sys.exit(0)
    else:
        global APP
        for canvas in APP['canvas_list']:
            APP['canvas'].delete(canvas)
            APP['points'] = []
            APP['canvas_list'] = []

    draw_point(REAL_POINTS[INDEX], 'green', "P" + str(INDEX))
    draw_point(GUESS_POINTS[INDEX], 'red')
    draw_line(Line(REAL_POINTS[INDEX], GUESS_POINTS[INDEX]), 'blue')
    for j in range(INDEX * NUM_NEIGHBORS, INDEX * NUM_NEIGHBORS + NUM_NEIGHBORS):
        draw_point(NEIGHBORS[j], 'purple', str(j - INDEX * NUM_NEIGHBORS + 1))
        draw_line(Line(REAL_POINTS[INDEX], NEIGHBORS[j]), 'black')
    INDEX = INDEX + 1

def readPoints():
    global REAL_POINTS, GUESS_POINTS, NEIGHBORS
    """ Reads points from input file """
    REAL_POINTS = []
    GUESS_POINTS = []
    NEIGHBORS = []
    points_list = sys.stdin.readlines()
    for (index, line) in enumerate(points_list):
        points = [float(p) for p in line.rstrip().split()]
        if len(points) == 4:
            REAL_POINTS.append(Point(points[0], points[1]))
            GUESS_POINTS.append(Point(points[2], points[3]))
        else:
            NEIGHBORS.append(Point(points[0], points[1]))

def main(argv):
    if len(argv) != 4:
        print "Usage: python testresults.py k image_path point_coords"
        exit(1)
    global NUM_NEIGHBORS
    NUM_NEIGHBORS = int(argv[1])
    image_path = argv[2]
    sys.stdin = open(argv[3])
    initializeApp(image_path)

if __name__ == '__main__':
    main(argv)
