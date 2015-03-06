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

class Point(object):
    """ Point Object """

    def __init__(self, x, y):
        self.x = x
        self.y = y

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

    APP['canvas'] = Tkinter.Canvas(APP['frame'], width=width, height=height)
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
    buttons = {'ready_btn': Tkinter.Button(APP['frame'], text="Ready!", command=ready)}
    return buttons

def draw_point(p, color):
    """ draws a point at the coordinates with the specified color """
    global APP

    radius = 5  # point radius
    new_canvas = APP['canvas'].create_oval(
        p.x - radius, p.y - radius, p.x + radius, p.y + radius, fill=color)

    APP['points'].append(p)
    APP['canvas_list'].append(new_canvas)

def draw_line(line, color):
    """ draws the given line with the specified color """
    global APP
    new_canvas = APP['canvas'].create_line(
            line.p1.x, line.p1.y, line.p2.x, line.p2.y, fill=color,
            width=line.length / 25, arrow=Tkinter.FIRST)
    APP['lines'].append(line)
    APP['canvas_list'].append(new_canvas)

def ready():
    """ Displays connections between test points and predictions """
    APP['buttons']['ready_btn'].pack_forget()

    (real_points, guess_points) = readPoints()
    for i in range(len(real_points)):
        draw_point(real_points[i], 'green')
        draw_point(guess_points[i], 'red')
        draw_line(Line(real_points[i], guess_points[i]), 'blue')

def readPoints():
    """ Reads points from input file """
    real_points = []
    guess_points = []
    points_list = sys.stdin.readlines()
    for line in points_list:
        points = [float(p) for p in line.rstrip().split()]
        real_points.append(Point(points[0], points[1]))
        guess_points.append(Point(points[2], points[3]))
    return (real_points, guess_points)

def main(argv):
    if len(argv) != 3:
        print "Usage: python testresults.py image_path point_coords"
        exit(1)

    image_path = argv[1]
    sys.stdin = open(argv[2])
    initializeApp(image_path)

if __name__ == '__main__':
    main(argv)
