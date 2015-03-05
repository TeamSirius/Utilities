from db.db import Database
from sys import argv, exit
import os
from PIL import Image
import math
from matplotlib import cm
import matplotlib.pyplot as plt
import StringIO

#RESIZE:     img = img.resize((basewidth,hsize), PIL.Image.ANTIALIAS)


my_dpi = 100

BLOCK_SIZE = 50

SHOW = False # Determines if images are shown or merely saved

password = os.environ.get('SIRIUS_PASSWORD')

radius = 5 # point radius

THRESHOLD = 225

if password is None:
    raise Exception('No password available')

db = Database(password)
cur = db.get_cur()

path_offset = "../Static_Files/" # Path offset from cwd to image directory

def dist(x1,y1,x2,y2):
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)


def overlay_image(img,data,zero=0):
    width,height = img.size
    contourImage,legendImage = make_contour_map(data, height,width,zero)
    overlay = Image.new("RGB", (width, height), "white")
    overlayPixels = overlay.load()
    contourPixels = contourImage.load()
    cw,ch = contourImage.size
    mapPixels = img.load()
    for w in range(width):
        for h in range(height):
            r,g,b = mapPixels[w,h]
            if r <= THRESHOLD and g <= THRESHOLD and b <= THRESHOLD:
                overlayPixels[w,h] = (255,255,255)
            else:
                if w < cw and h < ch:
                    overlayPixels[w,h] = contourPixels[w,h]
                else:
                    overlayPixels[w,h] = mapPixels[w,h]
    return overlay, legendImage


def crop_box(img):
    """returns a cropbox for an image in which removes as much white boarder as possible without
    removing any pixeles that are not == (255,255,255)"""
    width,height = img.size
    xs = []
    ys = []
    pixeles = img.load()
    for w in range(width):
        for h in range(height):
            if pixeles[w,h] != (255,255,255):
                xs.append(w)
                ys.append(h)
    if not xs or not ys:
        return (0,0,width,height)
    return (min(xs),min(ys),max(xs),max(ys))


def current_fig_image():
    """Takes current figure of matplotlib and returns it as a PIL image. 
    Also clears the current plot"""
    plt.axis('off')
    fig = plt.gcf()
    buff = StringIO.StringIO()
    fig.savefig(buff)
    buff.seek(0)
    img = Image.open(buff).convert('RGB')
    plt.clf()
    return img

def rectify_data(data,zero=0):
    """Assumes data is a proper 2D array"""
    if len(data) == 0:
        return []
    rows = len(data)
    cols = len(data[0])
    new_data = [[0 for j in range(cols)] for i in range(rows)]
    for row in range(rows):
        for col in range(cols):
            new_data[row][col] = block_average(data,row,col,BLOCK_SIZE, cols,rows,zero)
    return new_data


def weighted_avg(L,zero=0):
    #[(dist,value),...]
    if not L:
        return zero
    s = float(sum([x[0] for x in L]))
    return sum( [x[1] / s for x in L] )


def rectify_data_dist(data,zero=0):
    """Assumes data is a proper 2D array"""
    if len(data) == 0:
        return []
    rows = len(data)
    cols = len(data[0])
    new_data = [[zero for j in range(cols)] for i in range(rows)]
    dist_data = [[[] for j in range(cols)] for i in range(rows)]

    for row in range(rows):
        for col in range(cols):
            if data[row][col] == 0:
                for r in range(rows):
                    for c in range(cols):
                        if r != row and c != col:
                            dist_data[row][col].append((dist(row,col,r,c), data[r][c]))
                new_data[row][col] = weighted_avg(dist_data[row][col],zero)
            else:
                new_data[row][col] = data[row][col]
    return new_data





def block_average(data,row,col,BLOCK_SIZE,width,height,zero=0):
    """averages the values in data in a block of side size BLOCK_SIZE."""
    r = BLOCK_SIZE // 2
    s = 0
    counter = 0
    for i in range( max(0,row - r), min( row + r ,height - 1) ):
        for j in range( max(0,col - r), min( col + r ,width - 1) ):
            if data[i][j] != 0:
                s += data[i][j]
                counter += 1
    if counter == 0:
        return zero
    return float(s) / counter

 
def make_contour_map(data,height,width,zero=0):
    """Takes the given data and builds the csv string. 
    This function DOES NOT save the file. The expected input data
    should be a list in the format [(x,y,z),...]. The y data will be
    flipped such that the generated file from matlab will match the
    image orientation."""
    xs = sorted(set([item[0] for item in data]))
    ys = sorted(set([height - item[1] for item in data]))
    Z = [item[2] for item in data]
    min_z = 0
    #Flips ys
    num_X = len(xs)
    num_Y = len(ys)
    zs = [[min_z for j in range(width)] for i in range(height)]
        #indexed row column
    for (dx,dy,dz) in data:
        zs[height - dy][dx] = dz

    zs = rectify_data(zs,zero)
    plt.gca().set_ylim([0,height])
    plt.gca().set_xlim([0,width])
    plt.gcf().set_frameon(False)
    cs = plt.contourf([x for x in range(width)],[y for y in range(height)],zs)
    if zero == 0:
        labels = map(lambda x: str(x) + " APs" ,cs.levels)
    else:   
        labels = map(lambda x: str(x) + " -db" ,cs.levels)
    proxy = [plt.Rectangle((0,0),1,1,fc = pc.get_facecolor()[0]) 
        for pc in cs.collections]
    contourImage = current_fig_image()
    contourImage = contourImage.crop( crop_box(contourImage) )
    contourImage = contourImage.resize((width,height), Image.BILINEAR)
    plt.legend(proxy, labels)
    legendImage = current_fig_image()
    legendImage = legendImage.crop( crop_box(legendImage) )
    return contourImage,legendImage

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
    img_path = os.path.join(os.getcwd(),path_offset, imagePath)
    try:
        img = Image.open(img_path).convert('RGB')
    except IOError,err:
        exit("{}: Image not found at {}".format(argv[0],img_path))
    #Access point density map
    cur.execute("""select x,y,count(*) from marauder_location 
        join marauder_accesspoint on location.id=location_id
        where floor_id=%s
        group by location.id""",[floorId])
    imgCon, leg = overlay_image(img,cur.fetchall(),0)
    imgCon.save(os.path.join(os.getcwd(),path_offset,"floor_{}_AP_map.jpg".format(floorId) ) )
    leg.save(os.path.join(os.getcwd(),path_offset,"floor_{}_AP_legend.jpg".format(floorId) ) )
    #Maximim strength map
    cur.execute("""select x,y,max(strength) from marauder_location 
        join marauder_accesspoint on location.id=location_id
        where floor_id=%s
        group by location.id""",[floorId])
    imgCon, leg = overlay_image(img,cur.fetchall(),-120)
    imgCon.save(os.path.join(os.getcwd(),path_offset,"floor_{}_max_map.jpg".format(floorId) ) )
    leg.save(os.path.join(os.getcwd(),path_offset,"floor_{}_max_legend.jpg".format(floorId) ) )
    #Minimum strength map
    cur.execute("""select x,y,min(strength) from marauder_location 
        join marauder_accesspoint on location.id=location_id
        where floor_id=%s
        group by location.id""",[floorId])
    imgCon, leg = overlay_image(img,cur.fetchall(),-120)
    imgCon.save(os.path.join(os.getcwd(),path_offset,"floor_{}_min_map.jpg".format(floorId) ) )
    leg.save(os.path.join(os.getcwd(),path_offset,"floor_{}_min_legend.jpg".format(floorId) ) )
    #Mean strength map
    cur.execute("""select x,y,sum(strength)/count(*) from marauder_location 
        join marauder_accesspoint on location.id=location_id
        where floor_id=%s
        group by location.id""",[floorId])
    imgCon, leg = overlay_image(img,cur.fetchall(),-120)
    imgCon.save(os.path.join(os.getcwd(),path_offset,"floor_{}_median_map.jpg".format(floorId) ) )
    leg.save(os.path.join(os.getcwd(),path_offset,"floor_{}_median_legend.jpg".format(floorId) ) )
  


if __name__ == "__main__":
    main()