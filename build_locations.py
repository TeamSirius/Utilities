#Usage: python build_locations filename
#   This script will open the image then allow a user to click on a location
#   and name the location both shorthand and verbosely. This will then be
#   posted to a remote database

#When working logged points are in red, unlogged points are in blue

import Tkinter
from PIL import Image, ImageTk
from sys import argv

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

    def save(self):
        print "({},{}): in {}. {} or {}\n ".format(self.x,self.y, self.file_name, self.name, self.verbose)

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
        self.id = w.create_rectangle(x1, y1, x2, y2, fill="blue")
        self.canvas = w
    def pop(self):
        self.canvas.delete(self.cid2)
        self.canvas.delete(self.id)
        return (self.x1, self.y1, self.cid1)
    def delete(self):
        # deletes the rectangle from the canvas
        self.canvas.delete(self.id)

corners = []
rectangles = []        

def main(argv):
    window = Tkinter.Tk(className="Location Selector")
    locations = []
    if len(argv) != 2:
        print "Usage: python build_locations filename"
        exit(1)        
    image = Image.open(argv[1])
    pixels = image.load()
    canvas = Tkinter.Canvas(window, width=image.size[0], height=image.size[1])
    canvas.pack()
    image_tk = ImageTk.PhotoImage(image)
    oncanvas = canvas.create_image(image.size[0]//2, image.size[1]//2, image=image_tk)

    def add_corner(event):
        global corners
        global rectangles
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
    for loc in locations:
        loc.save()



if __name__ == '__main__':
    main(argv)
