from db.db import Database
from sys import argv, exit
import os
from PIL import Image

"""

MODIFY THIS COMMAND TO RUN and generate contour map
matlab -nodisplay -r "ContourMap('~/Desktop/test.csv','~/Desktop/test.png')" 


"""


SHOW = False # Determines if images are shown or merely saved

password = os.environ.get('SIRIUS_PASSWORD')

radius = 5 # point radius


if password is None:
    raise Exception('No password available')

db = Database(password)
cur = db.get_cur()

path_offset = "../Static_Files/" # Path offset from cwd to image directory
    
def make_csv(data,height):
    """Takes the given data and builds the csv string. 
    This function DOES NOT save the file. The expected input data
    should be a list in the format [(x,y,z),...]. The y data will be
    flipped such that the generated file from matlab will match the
    image orientation."""
    xs = sorted(set([item[0] for item in data]))
    ys = sorted(set([height - item[1] for item in data]))
    #Flips ys
    num_X = len(xs)
    num_Y = len(ys)
    zs = [[0 for j in range(num_X)] for i in range(num_Y)]
        #indexed row column
    lines = []
    lines.append("{},{}".format(num_Y,num_X))
    x_pos = {} # dictionary from x value to x index
    y_pos = {} # dictionary from y value to y index
    for i,y in enumerate(ys):
        y_pos[height - y] = i #initial y value, not flipped
        lines.append(str(y))
    for i,x in enumerate(xs):
        x_pos[x] = i
        lines.append(str(x))
    for (x,y,z) in data:
        zs[ y_pos[y] ][ x_pos[x] ] = z
    for line in zs:
        lines.append( ','.join( map(str,line) ) )
    return '\n'.join(lines)







def main():
    """Generates a csv map that ContourMap.m can parse to create a contour map
    There are 4 generaged csv files for the given floor which correspond to
    the number of visble access points and the min/max/median RSS strength.
    CSV files will be called: floor_[id]_[ap/min/max/median].csv in the same
    directory that the images are located"""
    if len(argv) != 2:
        exit("Usage: python {} [floor_id]".format(argv[0]))
    cur.execute("""SELECT imagePath from floor where id=%s""",[argv[1]])
    imagePath = cur.fetchone()
    if not imagePath:
        exit("{}:Floor with id={} not found".format(argv[0],argv[1]))
    imagePath = imagePath[0]
    floorId = argv[1]
    floors = cur.fetchall()
    full_path = os.path.join(os.getcwd(),path_offset, imagePath)
    try:
        img = Image.open(full_path)
    except IOError,err:
        exit("{}: Image not found at {}".format(argv[0],full_path))
    width, height = img.size
    #building APS
    cur.execute("""select x,y,count(*) from location 
        join accesspoint on location.id=location_id
        where floor_id=%s
        group by location.id""",[floorId])
    apCSV = make_csv(cur.fetchall(), height)
    apCSVPath= os.path.join(os.getcwd(),
     path_offset,
      "floor_{}_ap.csv".format(floorId))
    f = open(apCSVPath,"w+")
    f.write(apCSV)
    f.close()

if __name__ == "__main__":
    main()