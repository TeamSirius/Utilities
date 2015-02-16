from sys import argv,stderr,exit
from PIL import Image, ImageTk
import math
from random import random
import Tkinter, requests, json
# from db.db import cur,SERVER_URL,DEBUG

NUM_TEST_POINTS = 20 # Number of test points we want
NUM_CANDIDATES = 200 # Number of attempts per test point chosen

# Location Object
class Location(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    # Saves location to server
    def save(self, name, verbose, floor_id):
        payload = {}
        payload['x'] = self.x
        payload['y'] = self.y
        payload['name'] = ''
        payload['verbose'] = ''
        payload['floor_id'] = floor_id
        payload['d'] = 0

        r = requests.post(SERVER_URL + "location", data=json.dumps(payload))

# Rectangle Object
class Rectangle(object):
    def __init__(self, point_list):
        x1, y1 = point_list[0]
        x2, y2 = point_list[1]

        XL = min(x1,x2)
        XR = max(x1,x2)
        YT = min(y1,y2)
        YB = max(y1,y2)

        self.XL = min(x1,x2)
        self.XR = max(x1,x2)
        self.YT = min(y1,y2)
        self.YB = max(y1,y2)

        self.locs = [Location(XL, YT), Location(XR, YT), 
                    Location(XR, YB), Location(XL, YB)]

    # Checks whether the given rectangle contains the given location
    def contains(self, location):
        if ((self.XL <= location.x <= self.XR) and 
            (self.YT <= location.y <= self.YB)):
            return True
        else: 
            return False

# Returns a random number between minimum and maximum
def rand(minimum, maximum):
    return random() * (maximum - minimum) + minimum

# Given a set of Locations, a point, and the width and height of the image,
#   returns the closest location to the point
def findClosest(test_points, point, width, height):
    min_distance = math.sqrt(width * width + height * height)
    closest = None
    for test_point in test_points:
        cur_distance = distance(point, test_point)
        if cur_distance < min_distance:
            closest = test_point
            min_distance = cur_distance
    return closest

# Returns a random location in the image within at least one of the rectangles
def getRandomLocation(rectangles, width, height):
    loc = Location(rand(0, width), rand(0, height))
    if rectangles == []: return loc
    num_tries = 0  # Caps total number of tries allowed
    while(num_tries < 1000000):
        for rectangle in rectangles:
            if rectangle.contains(loc):
                return loc
        loc = Location(rand(0, width), rand(0, height))
        num_tries += 1
    stderr.write("rectangle space too small to find point\n")
    exit()

# Returns the distance between the given two Locations
def distance(a, b):
    dx = a.x - b.x
    dy = a.y - b.y
    return math.sqrt(dx * dx + dy * dy) 

# Runs Mitchell's Best-Candidate II Algorithm to find a random Location
def getTestPoint(test_points, rectangles, width, height):
    if len(test_points) == 0:
        return getRandomLocation(rectangles, width, height)
    bestDistance = 0
    for i in range(NUM_CANDIDATES):
        c = getRandomLocation(rectangles, width, height)
        d = distance(findClosest(test_points, c, width, height), c)
        if d > bestDistance:
            bestCandidate = c
    return bestCandidate

# Gets and returns a list of random Locations
def getTestPointList(rectangles, width, height):
    test_points = []
    while len(test_points) < NUM_TEST_POINTS:
        test_points.append(getTestPoint(test_points, rectangles, width, height))
    return test_points

num_vertices = 2
builder_function = Rectangle

rectangles = [] # list of things to post at end
points = []
delete_list = []

def main(argv, debug):
    if len(argv) != 2:
        print "Usage: python build_locations filename"
        exit(1)
    image = Image.open(argv[1])

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

        radius = 5 #point radius
        new_canvas = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color)
        points.append( (x,y) )
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

    def done():
        done_btn.pack_forget()
        log_btn.pack_forget()
        canvas.unbind("<Button-1>")

        width = image.size[0] 
        height = image.size[1]
        test_points = getTestPointList(rectangles, width, height)

        for test_point in test_points:
            draw_point(test_point.x, test_point.y, 'green')

    def exit():
        window.destroy()
        exit()

    def reset():
        global points
        global delete_list
        global builder_function
        for cid in delete_list:
            canvas.delete(cid)
        points = []
        delete_list = []

    def log():
        global rectangles
        global points
        global delete_list

        canvas.unbind("<Button-1>")

        rectangle = builder_function(points)
        possible_locs = rectangle.locs
        reset()

        for i, point in enumerate(possible_locs):
            draw_point(point.x, point.y, 'red')

        # command = raw_input("Confirm Points? [Y/N]")
        command = 'Y'
        if command.upper() == 'Y':
            rectangles.append(rectangle)
            points = []
            delete_list = []
        else:
            reset()
        log_btn.pack_forget()
        canvas.bind("<Button-1>", add_point)

    log_btn = Tkinter.Button(frame, text="Log",command=log)
    done_btn = Tkinter.Button(frame, text="Done",command=done)
    exit_btn = Tkinter.Button(frame, text="Exit",command=exit)
    exit_btn.pack(side='right')
    done_btn.pack(side='right')
    canvas.bind("<Button-1>", add_point)

    window.mainloop()

if __name__ == '__main__':
    debug = False
    main(argv, debug)
