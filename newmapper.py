import Tkinter
from PIL import Image, ImageTk
from sys import argv,exit
from db import cur,SERVER_URL,DEBUG
import os, math
import requests, json

# halligan_two = os.path.join(os.getcwd(), 'Halligan_2.png')

class Location(object):
    def __init__(self, x, y, name, verbose):
        self.x = x
        self.y = y
        self.name = name
        self.verbose = verbose

    def save(self, floor_id):
        payload = {}
        payload['x'] = self.x
        payload['y'] = self.y
        payload['name'] = self.name
        payload['verbose'] = self.verbose
        payload['floor_id'] = floor_id
        for i in range(4):
            payload['d'] = i * 90
            r = requests.post(SERVER_URL + "location", data=json.dumps(payload))

class Line(object):
    def __init__(self, points, name, verbose):
        x1, y1 = points[0]
        x2, y2 = points[1]
        num_points = int(raw_input('Number of points in line: '))

        XL = min(x1,x2)
        XR = max(x1,x2)
        YT = min(y1,y2)
        YB = max(y1,y2)

        width = XR - XL
        height = YB - YT # inverted because of pixel map structure
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
                    name + str(unichr(ord('A') + i)),verbose))
            else:
                self.locs.append(Location(XL, YT + (i * y_step),
                    name + str(unichr(ord('A') + i)), verbose))

class Rectangle(object):
    def __init__(self, points, name, verbose):
        x1, y1 = points[0]
        x2, y2 = points[1]

        XL = min(x1,x2)
        XR = max(x1,x2)
        YT = min(y1,y2)
        YB = max(y1,y2)
        XCT = (XL + XR) // 2
        YCT = (YB + YT) // 2

        self.locs = []
        self.locs.append(Location(XL, YT, name + "_TL", verbose + " Top Left"))
        self.locs.append(Location(XR, YT, name + "_TR", verbose + " Top Right"))
        self.locs.append(Location(XR, YB, name + "_BR", verbose + " Bottom Right"))
        self.locs.append(Location(XL, YB, name + "_BL", verbose + " Bottom Left"))
        self.locs.append(Location(XCT, YCT, name + "_CT", verbose + " Center"))

class Grid(object):
    def __init__(self, points, name, verbose):
        x1, y1 = points[0]
        x2, y2 = points[1]

        XL = min(x1,x2)
        XR = max(x1,x2)
        YT = min(y1,y2)
        YB = max(y1,y2)

        width = XR - XL # inverted because of pixel map structure
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

# Valid Modes:
#   - Point
#   - Line
#   - Rectangle
#   - Grid
density = 30

# Current Behavior: modes are kept separate; if you change modes before you 'complete'
#                   a log then you delete that log
num_vertices = 1 #{'Point':1, 'Line':2,'Rectangle':2,'Grid':2}
builder_function = Location #{'Point':Location, 'Line':Line,'Rectangle':Rectangle,'Grid':Grid}

points = [] # for all modes; erased when changing modes
delete_list = []
locations = [] # list of things to post at end

def main(argv, debug):
    if len(argv) != 2:
        print "Usage: python build_locations filename"
        exit(1)
    image = Image.open(argv[1])

    if not debug:
        payload = {'path': argv[1]}
        try:
            r = requests.get(SERVER_URL + "floor", params=payload)
            found_fid = False
            fid = 1
            if DEBUG:
                print r.text
            if r:
                json_r = r.json()
                if 'error' not in json_r:
                    found_fid = True
                    fid = int(json_r['floor_id'])
            if not found_fid:
                payload['building'] = raw_input("Building: ")
                payload['floor_number'] = int(raw_input("floor_number: "))
                r = requests.post(SERVER_URL + "floor", data=json.dumps(payload))
                json_r = r.json()
                if 'error' in json_r:
                    raise "Server Error"
                fid = int(json_r['floor_id'])
        except:
            exit("Error finding floor id")

    window = Tkinter.Tk()
    frame = Tkinter.Frame(window)
    frame.pack()

    canvas = Tkinter.Canvas(frame, width=image.size[0], height=image.size[1])
    canvas.pack()
    
    image_tk = ImageTk.PhotoImage(image)
    oncanvas = canvas.create_image(image.size[0]//2, image.size[1]//2, image=image_tk)

    modes = []
    def add_point(event):
        global points
        global locations
        global delete_list
        
        def draw_point(x, y, color):
            radius = 2 #point radius  
            new_canvas = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color)
            points.append( (x,y) )
            delete_list.append(new_canvas)

        draw_point(event.x, event.y, 'blue')

        if len(points) == num_vertices:
            name = raw_input("Short name: ")
            verbose = raw_input("Verbose name: ")

            possible_locs = []
            if num_vertices == 1:
                x, y = points[0]
                point = Location(x, y, name, verbose)
                possible_locs.append(point)
            else:
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
        elif len(points) > num_vertices:
            reset()
            draw_point(event.x, event.y, 'blue')

    def reset():
        global points
        global delete_list
        global builder_function
        for cid in delete_list:
            canvas.delete(cid)
        points = []
        delete_list = []

    def point_mode():
        global mode
        global num_vertices
        global builder_function
        num_vertices = 1
        builder_function = Location
        reset()

    def line_mode():
        global mode
        global num_vertices
        global builder_function
        num_vertices = 2
        builder_function = Line
        reset()  

    def rectangle_mode():
        global mode
        global num_vertices
        global builder_function
        num_vertices = 2
        builder_function = Rectangle
        reset()

    def grid_mode():
        global mode
        global num_vertices
        global builder_function
        global density
        num_vertices = 2
        builder_function = Grid
        if density == 0:
            density = raw_input("Density: ")
        reset()

    point_btn = Tkinter.Button(frame, text="Point",command=point_mode)
    line_btn = Tkinter.Button(frame, text="Line",command=line_mode)
    rectangle_btn = Tkinter.Button(frame, text="Rectangle",command=rectangle_mode)
    grid_btn = Tkinter.Button(frame, text="Grid",command=grid_mode)
    # delete_btn = Tkinter.Button(frame, text="Delete",command=delete_point)

    point_btn.pack(side='left')
    line_btn.pack(side='left')
    rectangle_btn.pack(side='left')
    grid_btn.pack(side="left")
    # delete_btn.pack(side="left")

    canvas.bind("<Button-1>", add_point)
    # canvas.bind("<Button-3>", delete_point)

    window.mainloop()
    command = raw_input("Save Points? [Y/N] ")
    if command == 'Y':
        for loc in locations:
            loc.save(fid)

if __name__ == '__main__':
    debug = False
    main(argv, debug)