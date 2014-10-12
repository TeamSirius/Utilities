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

    def callback(event):
        r = 2 #point radius
        canvas.create_oval(event.x-r, event.y-r, event.x + r, event.y +r, fill="blue")
        print "clicked at: ", event.x, event.y
        name = raw_input("Short name: ")
        verbose = raw_input("Verbose name: ")
        print "Point created"
        locations.append( Location( event.x, event.y, argv[1], name, verbose) )
        
        canvas.create_oval(event.x-r, event.y-r, event.x + r, event.y +r, fill="red")


    canvas.bind("<Button-1>", callback)
    Tkinter.mainloop()
    for loc in locations:
        loc.save()



if __name__ == '__main__':
    main(argv)
