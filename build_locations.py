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

    # - Hunter: currently testing function to automatically create 4 points in a rectangle
    #           when given two clicks. 
    def draw_rectangle():
        verbose = raw_input("Verbose name: ") # Will make a 4 new names based on this
        short = raw_input("Short Name: ") 

        corners = []
        def record_click(event):
            canvas.create_oval(event.x-r, event.y-r, event.x + r, event.y +r, fill="blue")
            print "clicked at: ", event.x, event.y
            corners.append( (event.x, event.y) )

        print "Click the Top-Left Corner of the Rectangle"
        canvas.bind("<Button-1>", record_click)
        t_l = corners.pop() # top-left

        print "Click the Bottom-Right Corner of the Rectangle"
        canvas.bind("<Button-1>", record_click)
        b_r = corners.pop() # bottom-right

        # To make list accessing more readable (for coordinates)
        X = 0
        Y = 1
        t_r = (b_r[X], t_l[Y])  # top-right
        b_l = (t_l[X], b_r[Y])  # bottom-left

        # Draws the point in red on the canvas and saves the location to 'locations'
        def draw_and_save(point, location):
            r = 2 # also the point radius
            verbose_name = verbose + '_' + location[0]
            short_name = short + '_' + location[1]

            print "Point created: [x: ", str(point[X]), ', y: ', str(point[Y]), ', short: ', short_name, ', verbose: ', verbose_name, ']'
            locations.append( Location( point[X], point[Y], argv[1], short_name, verbose_name) )
            canvas.create_oval(point[X]-r, point[Y]-r, point[X]+r, point[Y]+r, fill="red")
        
        corner_coords = (t_l, t_r, b_l, b_r)
        corner_names = [['Top-Left', 'TL'], ['Top-Right', 'TR'], ['Bottom-Left', 'BL'], ['Bottom-Right', 'BR']]
        for i in range(4):
            draw_and_save(corner_coords[i], corner_names[i])

    rectangle = raw_input("Press '1' for a rectange.")
    if int(rectange):
        draw_rectangle
    else:
        canvas.bind("<Button-1>", callback)

    Tkinter.mainloop()
    for loc in locations:
        loc.save()



if __name__ == '__main__':
    main(argv)
