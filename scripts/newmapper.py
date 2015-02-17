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

# Changing Modes before logging deletes unlogged points

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

class Location(object):
    def __init__(self, x, y, name, verbose):
        self.x = x
        self.y = y
        self.name = name
        self.verbose = verbose

    def save(self, floor_identifier):
        global server_interface
        payload = {
            'verbose_name': self.verbose,
            'short_name': self.name,
            'x_coordinate': self.x,
            'y_coordinate': self.y,
            'floor': floor_identifier
        }

        for i in xrange(4):
            payload['direction'] = i * 90
            server_interface.post(ServerInterface.LOCATION,
                                  payload)


class Point(object):
    def __init__(self, point_list, name, verbose):
        x, y = point_list[0]
        self.locs = []
        self.locs.append(Location(x, y, name, verbose))


class Line(object):
    def __init__(self, point_list, name, verbose):
        x1, y1 = point_list[0]
        x2, y2 = point_list[1]
        num_points = int(raw_input('Number of points in line: '))

        XL = min(x1, x2)
        XR = max(x1, x2)
        YT = min(y1, y2)
        YB = max(y1, y2)

        width = XR - XL
        height = YB - YT  # inverted because of pixel map structure
        x_step = width // (num_points - 1)
        y_step = height // (num_points - 1)

        if width > height:
            YT = (YT + YB) // 2
            YB = YT
        else:
            XL = (XL + XR) // 2
            XR = XL

        self.locs = []
        for i in range(num_points):
            if width > height:
                self.locs.append(Location(XL + (i * x_step), YB,
                    name + str(unichr(ord('A') + i)), verbose))
            else:
                self.locs.append(Location(XL, YT + (i * y_step),
                    name + str(unichr(ord('A') + i)), verbose))


class Rectangle(object):
    def __init__(self, point_list, name, verbose):
        x1, y1 = point_list[0]
        x2, y2 = point_list[1]

        XL = min(x1, x2)
        XR = max(x1, x2)
        YT = min(y1, y2)
        YB = max(y1, y2)
        XCT = (XL + XR) // 2
        YCT = (YB + YT) // 2

        self.locs = []
        self.locs.append(Location(XL, YT, name + "_TL", verbose + " Top Left"))
        self.locs.append(Location(XR, YT, name + "_TR", verbose + " Top Right"))
        self.locs.append(Location(XR, YB, name + "_BR", verbose + " Bottom Right"))
        self.locs.append(Location(XL, YB, name + "_BL", verbose + " Bottom Left"))
        self.locs.append(Location(XCT, YCT, name + "_CT", verbose + " Center"))


class Grid(object):
    def __init__(self, point_list, name, verbose):
        x1, y1 = point_list[0]
        x2, y2 = point_list[1]

        XL = min(x1, x2)
        XR = max(x1, x2)
        YT = min(y1, y2)
        YB = max(y1, y2)

        width = XR - XL  # inverted because of pixel map structure
        height = YB - YT
        num_across = max(1, int(math.ceil(width // density)))
        num_high = max(1, int(math.ceil(height // density)))
        x_justification = ((width - (density * (num_across - 1))) / 2) + XL
        y_justification = ((height - (density * (num_high - 1))) / 2) + YT

        self.locs = []
        for x in range(num_across):
            for y in range(num_high):
                addage = '_' + str(x) + '-' + str(unichr(ord('A') + y))
                x_coord = x_justification + (density * x)
                y_coord = y_justification + (density * y)
                self.locs.append(Location(x_coord, y_coord, name + addage, verbose + addage))

density = 30
num_vertices = 1
builder_function = Point

points = []
delete_list = []
locations = [] # list of things to post at end

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


def begin_mapping(image_file, debug, username='', password=''):
    global server_interface
    server_interface = ServerInterface(username, password)
    image = Image.open(image_file)

    # if not debug:
    #     payload = {'path': file_name(image_file)}
    #     try:
    #         r = requests.get(SERVER_URL + "floor", params=payload)
    #         found_fid = False
    #         fid = 1
    #         if DEBUG:
    #             print r.text
    #         if r:
    #             json_r = r.json()
    #             if 'error' not in json_r:
    #                 found_fid = True
    #                 fid = int(json_r['floor_id'])
    #         if not found_fid:
    #             payload['building'] = building_name
    #             payload['floor_number'] = floor_number
    #             r = requests.post(SERVER_URL + "floor", data=json.dumps(payload))
    #             json_r = r.json()
    #             if 'error' in json_r:
    #                 raise "Server Error"
    #             fid = int(json_r['floor_id'])
    #     except:
    #         exit("Error finding floor id")
    if not debug:
        floor_identifier = get_floor_identifier(image_file)
        # print floor_identifier

    window = Tkinter.Tk()
    frame = Tkinter.Frame(window)
    frame.pack()

    canvas = Tkinter.Canvas(frame, width=image.size[0], height=image.size[1])
    canvas.pack()

    image_tk = ImageTk.PhotoImage(image)
    oncanvas = canvas.create_image(image.size[0]//2, image.size[1]//2, image=image_tk)

    def draw_point(x, y, color):
        global points
        global delete_list

        radius = 2 #point radius
        new_canvas = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color)
        points.append( (x, y) )
        delete_list.append(new_canvas)

    def add_point(event):
        draw_point(event.x, event.y, 'blue')

        if len(points) == num_vertices:
            log_btn.pack(side='left')
        elif len(points) > num_vertices:
            reset()
            draw_point(event.x, event.y, 'blue')
            log_btn.pack_forget()
        else:
            log_btn.pack_forget()

    def reset():
        global points
        global delete_list
        global builder_function
        for cid in delete_list:
            canvas.delete(cid)
        points = []
        delete_list = []

    def point_mode():
        global num_vertices
        global builder_function
        num_vertices = 1
        builder_function = Point
        reset()

    def line_mode():
        global num_vertices
        global builder_function
        num_vertices = 2
        builder_function = Line
        reset()

    def rectangle_mode():
        global num_vertices
        global builder_function
        num_vertices = 2
        builder_function = Rectangle
        reset()

    def grid_mode():
        global num_vertices
        global builder_function
        global density
        num_vertices = 2
        builder_function = Grid
        if density == 0:
            density = raw_input("Density: ")
        reset()

    def log():
        global locations
        global points
        global delete_list

        canvas.unbind("<Button-1>")
        name = raw_input("Short name: ")
        verbose = raw_input("Verbose name: ")

        mode_points = builder_function(points, name, verbose)
        possible_locs = mode_points.locs
        reset()

        for i, point in enumerate(possible_locs):
            print 'Point', i + 1, ':'
            print '     Name: ', point.name, 'Verbose: ', point.verbose
            draw_point(point.x, point.y, 'red')

        command = raw_input("Confirm Points? [Y/N]")
        if command == 'Y':
            locations = locations + possible_locs
            points = []
            delete_list = []
        else:
            reset()
        log_btn.pack_forget()
        canvas.bind("<Button-1>", add_point)


    point_btn = Tkinter.Button(frame, text="Point", command=point_mode)
    line_btn = Tkinter.Button(frame, text="Line", command=line_mode)
    rectangle_btn = Tkinter.Button(frame, text="Rectangle", command=rectangle_mode)
    grid_btn = Tkinter.Button(frame, text="Grid", command=grid_mode)
    log_btn = Tkinter.Button(frame, text="Log", command=log)

    point_btn.pack(side='left')
    line_btn.pack(side='left')
    rectangle_btn.pack(side='left')
    grid_btn.pack(side="left")

    canvas.bind("<Button-1>", add_point)

    window.mainloop()
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
    begin_mapping(args.image_file, args.debug, args.username, args.password)
