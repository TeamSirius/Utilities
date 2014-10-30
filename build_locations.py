#Usage: python build_locations filename
#   This script will open the image then allow a user to click on a location
#   and name the location both shorthand and verbosely. This will then be
#   posted to a remote database

#When working logged points are in red, unlogged points are in blue

import Tkinter
from PIL import Image, ImageTk
from sys import argv,exit
from db import cur,SERVER_URL
import requests
import json


class Location(object):
    """A location corresponds to a pixel location on a map, the file name,
        a short name and a verbose name. It allows the functionality of
        'saving' which will post to a server to store in a remote database.
        Each save will post 4 times, one for each cardinal direction"""

    def __init__(self, x, y, file_name, name, verbose):
        self.x = x
        self.y = y
        self.file_name = file_name
        self.name = name
        self.verbose = verbose

    def save(self,floor_id):
        payload = {}
        payload['x'] = self.x
        payload['y'] = self.x
        payload['name'] = self.name
        payload['verbose'] = self.verbose
        payload['floor_id'] = floor_id
        for i in range(4):
            payload['d'] = i * 90
            r = requests.post(SERVER_URL + "location", params=payload)

class Rectangle(object):
    def __init__(self,name, verbose, x1, y1, x2, y2, cid1,cid2, w):
        #x1, y1 is the top left corner
        #x2, y2 is the bottom right corner
        #w is the Tkinter canvas 
        self.name = name
        self.verbose = verbose
        self.cid1 = cid1
        self.cid2 = cid2
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        XL = self.x1 if self.x1 < self.x2 else self.x2
        XR = self.x2 if self.x1 < self.x2 else self.x1
        YT = self.y1 if self.y1 < self.y2 else self.y2
        YB = self.y2 if self.y1 < self.y2 else self.y1
        self.id = w.create_rectangle(XL, YT, XR, YB, fill="blue")
        self.canvas = w
    def build_locations(self,locs):
        XL = self.x1 if self.x1 < self.x2 else self.x2
        XR = self.x2 if self.x1 < self.x2 else self.x1
        YT = self.y1 if self.y1 < self.y2 else self.y2
        YB = self.y2 if self.y1 < self.y2 else self.y1
        fn = argv[1]
        loc1 = Location(XL,YT,fn, self.name +" TL", self.verbose + " Top Left")
        loc2 = Location(XR,YT,fn, self.name +" TR", self.verbose + " Top Right")
        loc3 = Location(XR,YB,fn, self.name +" BR", self.verbose + " Bottom Right")
        loc4 = Location(XL,YB,fn, self.name +" BL", self.verbose + " Bottom Left")
        loc5 = Location( (XL + XR) // 2, (YB + YT) // 2,fn, self.name +" CT", self.verbose + " Center")
        locs.append(loc1)
        locs.append(loc2)
        locs.append(loc3)
        locs.append(loc4)
        locs.append(loc5)

    def pop(self):
        self.canvas.delete(self.cid2)
        self.canvas.delete(self.id)
        return (self.x1, self.y1, self.cid1)
    def delete(self):
        # deletes the rectangle from the canvas
        self.canvas.delete(self.cid2)
        self.canvas.delete(self.cid1)
        self.canvas.delete(self.id)

corners = []
rectangles = []        
locations = []

def main(argv):
    window = Tkinter.Tk(className="Location Selector")
    if len(argv) != 2:
        print "Usage: python build_locations filename"
        exit(1)        
    image = Image.open(argv[1])
    payload = {'path': argv[1]}
    try:
        r = requests.get(SERVER_URL + "floor", params=payload)
        found_fid = False
        fid = 1
        if r: 
            json_r = r.json()
            if 'error' not in json_r:
                found_fid = True
                fid = int(json_r['floor_id'])
        if not found_fid:
            payload['building'] = raw_input("Building: ")
            payload['floor_number'] = int(raw_input("floor_number: "))
            r = requests.post(SERVER_URL + "floor", params=payload)
            json_r = r.json()
            if 'error' in json_r:
                raise "Server Error"
            fid = int(json_r['floor_id'])
    except:
        exit("Error finding floor id")

    pixels = image.load()
    canvas = Tkinter.Canvas(window, width=image.size[0], height=image.size[1])
    canvas.pack()
    image_tk = ImageTk.PhotoImage(image)
    oncanvas = canvas.create_image(image.size[0]//2, image.size[1]//2, image=image_tk)

    def add_corner(event):
        global corners
        global rectangles
        global locations
        radius = 2 #point radius
        cid = canvas.create_oval(event.x-radius, event.y-radius,
             event.x + radius, event.y +radius, fill="blue")
        corners.append( (event.x, event.y, cid) )
        if len(corners) == 2:
            name = raw_input("Short name: ")
            verbose = raw_input("Verbose name: ")
            rectangles.append( Rectangle(name,verbose,corners[0][0],corners[0][1],corners[1][0],corners[1][1],
                corners[0][2], corners[1][2],
                canvas)  )
            corners = []

    def pop_corner(event):
        global corners
        global rectangles
        global locations
        if len(corners) != 1:
            if len(rectangles) == 0:
                return
            else:
                r = rectangles.pop(len(rectangles) - 1)
                corners.append( r.pop() )
        else:
            c = corners[0]
            canvas.delete(c[2])
            corners = []
    

    canvas.bind("<Button-1>", add_corner)
    canvas.bind("<Button-2>", pop_corner)

    Tkinter.mainloop()
    for rect in rectangles:
        rect.build_locations(locations)
    for loc in locations:
        loc.save(fid)



if __name__ == '__main__':
    main(argv)
