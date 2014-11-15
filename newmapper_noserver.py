import Tkinter
from PIL import Image, ImageTk
# from sys import argv,exit
# from db import cur,SERVER_URL,DEBUG
import os, math
# import requests, json

halligan_two = os.path.join(os.getcwd(), 'Halligan_2.png')

class Location(object):
    def __init__(self, x, y, name, verbose):
        self.x = x
        self.y = y
        self.name = name
        self.verbose = verbose

    def save(self):
        payload = {}
        payload['x'] = self.x
        payload['y'] = self.y
        payload['name'] = self.name
        payload['verbose'] = self.verbose
        # payload['floor_id'] = floor_id
        # for i in range(4):
            # payload['d'] = i * 90
            # r = requests.post(SERVER_URL + "location", data=json.dumps(payload))

class Line(object):
    def __init__(self, coords, name, verbose):
        x1, y1 = coords[0]
        x2, y2 = coords[1]

        self.locs = []
        self.locs.append(Location(x1,y1,name + '_A',verbose + '_A'))
        self.locs.append(Location(x2,y2,name + '_B',verbose + '_B'))

class Rectangle(object):
    def __init__(self, coords, name, verbose):
        x1, y1 = coords[0]
        x2, y2 = coords[1]

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
    def __init__(self, coords, name, verbose):
        x1, y1 = coords[0]
        x2, y2 = coords[1]

        XL = min(x1,x2)
        XR = max(x1,x2)
        YT = min(y1,y2)
        YB = max(y1,y2)

        width = XR - XL
        height = YB - YT # inverted because of pixel map structure
        num_across = max(1, int(math.ceil(width // scale)))
        num_high = max(1, int(math.ceil(height // scale)))
        x_justification = ((width - (scale * (num_across - 1))) / 2) + XL
        y_justification = ((height - (scale * (num_high - 1))) / 2) + YT

        self.locs = []
        for x in range(num_across):
            for y in range(num_high):
                addage = '_' + str(x) + '-' + str(unichr(ord('A') + y))
                x_coord = x_justification + (scale * x)
                y_coord = y_justification + (scale * y)

                self.locs.append(Location(x_coord, y_coord, name + addage, verbose + addage))

# Valid Modes:
#   - Point
#   - Line
#   - Rectangle
#   - Grid
mode = 'Point'
scale = 40

# Current Behavior: modes are kept separate; if you change modes before you 'complete'
#                   a log then you delete that log
num_vertices = {'Point':1, 'Line':2,'Rectangle':2,'Grid':2}
builder_function = {'Point':Location, 'Line':Line,'Rectangle':Rectangle,'Grid':Grid}

points = [] # for all modes; erased when changing modes
delete_list = []
locations = [] # list of things to post at end

def main():
    window = Tkinter.Tk()
    frame = Tkinter.Frame(window)
    frame.pack()

    image = Image.open(halligan_two) # later should load from file
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

        if num_vertices[mode] == len(points):
            name = raw_input("Short name: ")
            verbose = raw_input("Verbose name: ")

            possible_locs = []
            possible_color = []
            possible_names = []
            if mode == 'Point':
                x, y = points[0]
                point = Location(x, y, name, verbose)
                possible_locs.append(point)
            else:
                mode_points = builder_function[mode](points, name, verbose)
                possible_locs = mode_points.locs

            for i, point in enumerate(possible_locs):
                print 'Point', i + 1, ':'
                print '     Name: ', point.name, 'Verbose: ', point.verbose
                draw_point(point.x, point.y, 'red')

            command = raw_input("Confirm Points? [Y/N]: ")
            if command == 'Y':
                locations = locations + possible_locs
                points = []
                delete_list = []
            else:
                reset()

    def reset():
        global points
        global delete_list
        for cid in delete_list:
            canvas.delete(cid)
        points = []
        delete_list = []

    def delete_point():
        global points
        global delete_list
        if len(points) >= 0 and len(delete_list) >= 0:
            points.pop()
            cid = delete_list.pop()
            canvas.delete(cid)

    def point_mode():
        global mode
        mode = 'Point'
        reset()

    def line_mode():
        print "Click Two Points; Enter One Name; First Point will be 'Name + A', Second will be 'Name + B'"
        global mode
        mode = 'Line'     
        reset()  

    def rectangle_mode():
        global mode
        mode = 'Rectangle'
        reset()

    def grid_mode():
        global mode
        global scale
        mode = 'Grid'
        if scale == 0:
            scale = raw_input("Scale: ")
        reset()

    point_btn = Tkinter.Button(frame, text="Point",command=point_mode)
    line_btn = Tkinter.Button(frame, text="Line",command=line_mode)
    rectangle_btn = Tkinter.Button(frame, text="Rectangle",command=rectangle_mode)
    grid_btn = Tkinter.Button(frame, text="Grid",command=grid_mode)
    delete_btn = Tkinter.Button(frame, text="Delete",command=delete_point)

    point_btn.pack(side='left')
    line_btn.pack(side='left')
    rectangle_btn.pack(side='left')
    grid_btn.pack(side="left")
    delete_btn.pack(side="left")

    canvas.bind("<Button-1>", add_point)
    # canvas.bind("<Button-3>", delete_point)

    window.mainloop()
    for loc in locations:
        loc.save()

if __name__ == '__main__':
    main()