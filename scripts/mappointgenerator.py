# This Script:
#   - supports building mapping by mode
# Valid Modes:
#   - Point
#   - Line (horizontal or vertical)
#       - asks for the number of points in the line
#       - Naming Schema:
#           - Vertical Lines:
#               - Top-Bottom = A-Z
#           - Horizontal Lines:
#               - Left-Right = A-Z
#   - Rectangle
#   - Grid
#       - Name Schema:
#           - Columns: 0-N
#           - Rows: A-Z

#################### TODO ###################
# name points before they get sent to the database

import Tkinter
import math
import requests
import json
from PIL import Image, ImageTk
from sys import exit
from db.db import SERVER_URL, DEBUG
import ntpath
import argparse
import sys
from server_interface import ServerInterface

server_interface = None
APP = {}  # will hold global information for TKinter app
DENSITY = 30 # default density of grids

def file_name(file_path):
    head, tail = ntpath.split(file_path)
    return tail or ntpath.basename(head)

def get_floor_information():
    """ Get the name of the building and floor information from the user
        If a non-integer floor number is entered, keep asking"""

    building_name = raw_input("Building: ")
    floor_number = -1
    while True:
        try:
            floor_number = int(raw_input("Floor Number: "))
            break
        except ValueError:
            print >> sys.stderr, "Not a number. Try again"

    return building_name, floor_number


def get_floor_identifier(image_file):
    """ retrieves floor identifier from server """
    global server_interface
    building_name, floor_number = get_floor_information()
    get_payload = {
        'building_name__iexact': building_name.lower(),
        'floor_number': floor_number
    }

    worked, data = server_interface.get_single_item(ServerInterface.FLOOR,
                                                    get_payload)

    if not worked:
        with open(image_file, 'rb') as image:
            post_payload = {
                'floor_number': floor_number,
                'building_name': building_name
            }

            files = {
                'image': image
            }

            data = server_interface.post_with_files(ServerInterface.FLOOR,
                                                    post_payload,
                                                    files)
    return data['resource_uri']

#--------------------------------
# Object code here
#--------------------------------

class Location(object):
    """ used for posting to the server """

    def __init__(self, point, name, verbose):
        self.point = point
        self.name = name
        self.verbose = verbose

    def save(self, floor_identifier):
        global server_interface
        payload = {
            'verbose_name': self.verbose,
            'short_name': self.name,
            'x_coordinate': self.point.x,
            'y_coordinate': self.point.y,
            'floor': floor_identifier
        }

        for i in xrange(4):
            payload['direction'] = i * 90
            server_interface.post(ServerInterface.LOCATION, payload)

class PlainPoint(object):
    """ PlainPoint Object, for simple (x,y) """
    def __init__(self, x, y):
        self.x = x
        self.y = y

#--------------------------------
# Object code for TKinter drawing
#--------------------------------

class Point(object):
    """ wrapper for Points when drawing"""
    def __init__(self, point):
        self.point = point

    def points(self):
        """ Returns the point to be drawn for a point """
        return self.point

class Line(object):
    def __init__(self, point_list):
        p1 = point_list[0]
        p2 = point_list[1]
        self.num_points = int(raw_input('Number of points in line: '))

        self.XL = min(p1.x, p2.x)
        self.XR = max(p1.x, p2.x)
        self.YT = min(p1.y, p2.y)
        self.YB = max(p1.y, p2.y)

    def points(self):
        """ Returns the points to be drawn for a line """
        width = self.XR - self.XL
        height = self.YB - self.YT 

        if width > height: 
            # horizontal line
            x = self.XL
            y = (self.YT + self.YB) // 2
            x_step = width // (self.num_points - 1)
            y_step = 0
        else: 
            # vertical line
            x = (self.XL + self.XR) // 2
            y = self.YT
            x_step = 0
            y_step = height // (self.num_points - 1)

        points = []
        for i in range(self.num_points):
            points.append(PlainPoint(x + (i * x_step), y + (i * y_step)))

        return points

class Rectangle(object):

    def __init__(self, point_list):
        p1 = point_list[0]
        p2 = point_list[1]

        self.XL = min(p1.x, p2.x)
        self.XR = max(p1.x, p2.x)
        self.YT = min(p1.y, p2.y)
        self.YB = max(p1.y, p2.y)

    def points(self):
        """ Returns the points to be drawn for a rectangle """
        return [PlainPoint(self.XL, self.YT),
                PlainPoint(self.XR, self.YT),
                PlainPoint(self.XR, self.YB),
                PlainPoint(self.XL, self.YB),
                PlainPoint((self.XL + self.XR) // 2, (self.YB + self.YT) // 2)]

class Grid(object):
    def __init__(self, point_list):
        p1 = point_list[0]
        p2 = point_list[1]

        self.XL = min(p1.x, p2.x)
        self.XR = max(p1.x, p2.x)
        self.YT = min(p1.y, p2.y)
        self.YB = max(p1.y, p2.y)

    def points(self):
        """ Returns the points to be drawn for a grid """
        width = self.XR - self.XL
        height = self.YB - self.YT 

        num_across = max(1, int(math.ceil(width // DENSITY)))
        num_high = max(1, int(math.ceil(height // DENSITY)))
        x_justification = ((width - (DENSITY * (num_across - 1))) / 2) + self.XL
        y_justification = ((height - (DENSITY * (num_high - 1))) / 2) + self.YT

        points = []
        for x in range(num_across):
            for y in range(num_high):
                x_coord = x_justification + (DENSITY * x)
                y_coord = y_justification + (DENSITY * y)
                points.append(PlainPoint(x_coord, y_coord))
        return points

#--------------------------------
# TKinter Application Code Below
#--------------------------------


def initializeAPP(image_path):
    """ Initializes data for app and binds tkinter buttons """
    global APP

    image = Image.open(image_path)
    width, height = image.size[0], image.size[1]

    APP['window'] = Tkinter.Tk()
    APP['frame'] = Tkinter.Frame(APP['window'])
    image_tk = ImageTk.PhotoImage(image)

    APP['canvas'] = Tkinter.Canvas(APP['frame'], width=width, height=height)
    APP['canvas'].create_image(width // 2, height // 2, image=image_tk)

    APP['dims'] = {'w': width, 'h': height}
    APP['buttons'] = getButtons()
    APP['locations'] = []
    APP['points'] = []
    APP['canvas_list'] = []
    APP['mode'] = {'draw': Rectangle, 'vertices': 2}
    packAndRunApp()

def getButtons():
    """ Returns dict of buttons; will be added to APP object """
    global APP
    buttons = {'point_btn': Tkinter.Button(APP['frame'], text="Point", command=point_mode),
               'line_btn': Tkinter.Button(APP['frame'], text="Line", command=line_mode),
               'rectangle_btn': Tkinter.Button(APP['frame'], text="Rectangle", command=rectangle_mode),
               'grid_btn': Tkinter.Button(APP['frame'], text="Grid", command=grid_mode),
               'log_btn': Tkinter.Button(APP['frame'], text="Log", command=log)}
    return buttons

def packAndRunApp():
    """ packs tkinter interface at startup of app """
    global APP
    APP['frame'].pack()
    APP['canvas'].pack()
    APP['buttons']['point_btn'].pack(side='left')
    APP['buttons']['line_btn'].pack(side='left')
    APP['buttons']['rectangle_btn'].pack(side='left')
    APP['buttons']['grid_btn'].pack(side="left")

    APP['canvas'].bind("<Button-1>", handle_click)
    APP['window'].mainloop()

def draw_point(p, color):
    """ draws a point at the coordinates with the specified color """
    global APP

    radius = 5  # point radius
    new_canvas = APP['canvas'].create_oval(
        p.x - radius, p.y - radius, p.x + radius, p.y + radius, fill=color)

    APP['points'].append(p)
    APP['canvas_list'].append(new_canvas)

def handle_click(click):
    """ Adds a point to the canvas; if there are enough points, allows logging """
    global APP
    point = PlainPoint(click.x, click.y)

    num_points = len(APP['points']) + 1

    if num_points > APP['mode']['vertices']:
        reset()
        APP['buttons']['log_btn'].pack_forget()
    elif num_points == APP['mode']['vertices']:
        APP['buttons']['log_btn'].pack(side='left')

    draw_point(point, 'blue')

def log():
    """ generates the rest of the shape for drawing; asks for confirmation if input
        is correct.  """
    global APP

    APP['canvas'].unbind("<Button-1>")

    # name = raw_input("Short name: ")
    # verbose = raw_input("Verbose name: ")

    shape = APP['mode']['draw'](APP['points'])
    reset()

    for p in shape.points():
        draw_point(p, 'red')

    # command = raw_input("Confirm Points? [Y/N]")
    command = 'Y'
    if command.upper() == 'Y':
        APP['locations'] += shape.points()
        APP['points'] = []
        APP['canvas_list'] = []
    else:
        reset()

    APP['buttons']['log_btn'].pack_forget()
    APP['canvas'].bind("<Button-1>", handle_click)

def reset():
    """ removes unlogged points from screen """
    global APP

    for cid in APP['canvas_list']:
        APP['canvas'].delete(cid)

    APP['points'] = []
    APP['canvas_list'] = []

def point_mode():
    """ resets points; sets APP's draw function to point mode""" 
    global APP
    APP['mode'] = {'draw': Point, 'vertices': 1}
    reset()

def line_mode():
    """ resets points; sets APP's draw function to line mode""" 
    global APP

    APP['mode'] = {'draw': Line, 'vertices': 2}
    reset()

def rectangle_mode():
    """ resets points; sets APP's draw function to rectangle mode""" 
    global APP
    APP['mode'] = {'draw': Rectangle, 'vertices': 2}
    reset()

def grid_mode():
    """ resets points; sets APP's draw function to grid mode""" 
    global APP
    global DENSITY 

    APP['mode'] = {'draw': Grid, 'vertices': 2}
    if DENSITY == 0:
        DENSITY = raw_input("Density: ")
    reset()

#################################

def main(image_file, debug, username='', password=''):
    """ opens up server interface; finds floor id; initializes and runs app"""
    global server_interface

    if not debug:
        server_interface = ServerInterface(username, password)
        floor_identifier = get_floor_identifier(image_file)

    initializeAPP(image_file)

    if not debug:
        command = raw_input("Save Points? [Y/N] ")
        if command == 'Y':
            for loc in locations:
                loc.save(floor_identifier)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('image_file', help='The image to work with')
    parser.add_argument('username', help='Your username for the server')
    parser.add_argument('password', help='Your password for the server')
    parser.add_argument('-d', '--debug', action='store_true', help='Debug')

    args = parser.parse_args()
    main(args.image_file, args.debug, args.username, args.password)
