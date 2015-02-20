from db.db import Database
import os
from PIL import Image, ImageDraw

SHOW = False # Determines if images are shown or merely saved

password = os.environ.get('SIRIUS_PASSWORD')

radius = 5 # point radius


if password is None:
    raise Exception('No password available')

db = Database(password)
cur = db.get_cur()

path_offset = "../Static_Files/" # Path offset from cwd to image directory


def overlay(FID1, FID2):
    """Given 2 arrays of (x,y) and an image will plot points on the same
    image. This is useful when plotting test points and gathered points 
    on the same map. The saved image will be saved as floor_FID1_AND_FID2.png.
    The image paths are assumed the same and the image from FID1 is used.
    Points from FID1 are in blue while points from FID2 are in red."""
    cur.execute("""SELECT imagePath from floor where id=%s""",[FID1])
    floor_path = cur.fetchone()
    if not floor_path:
        return
    imagePath = floor_path[0] #extracting string from tuple
    full_path = os.path.join(os.getcwd(),path_offset, imagePath)
    try:
        image = Image.open(full_path)
    except IOError,err:
        print "Image {} not found. Skipping overlay".format(full_path)
        return        
    draw_image = ImageDraw.Draw(image)
    cur.execute("""SELECT x,y from location where floor_id=%s""",[FID1])
    locations = cur.fetchall()
    for location in locations:
        x,y = location
        draw_image.ellipse((x-radius,y-radius,x+radius,y+radius), fill='blue')

    cur.execute("""SELECT x,y from location where floor_id=%s""",[FID2])
    locations = cur.fetchall()
    for location in locations:
        x,y = location
        draw_image.ellipse((x-radius,y-radius,x+radius,y+radius), fill='red')

    if SHOW:
        image.show()
    image_name = os.path.join(os.getcwd(),path_offset,
        "floor_{}_and_{}.png".format(FID1,FID2))
    image.save(image_name,"PNG")
    

def main():
    """Finds all floors and locations on those floors and plots them on the
    floor map image. If the image is not found the floor is skipped. The image
    is saved in the same folder the images are found with the name 
    floor_[id]_points.png"""
    cur.execute("""SELECT id,imagePath from floor""")
    floors = cur.fetchall()
    for floor in floors:
        floorId = floor[0]
        imagePath = floor[1] 
        full_path = os.path.join(os.getcwd(),path_offset, imagePath)
        try:
            image = Image.open(full_path)
        except IOError,err:
            print "Image {} not found. Skipping floor".format(full_path)
            continue        
        draw_image = ImageDraw.Draw(image)
        cur.execute("""SELECT x,y from location where floor_id=%s""",[floorId])
        locations = cur.fetchall()
        for location in locations:
            x,y = location
            draw_image.ellipse((x-radius,y-radius,x+radius,y+radius), fill='blue')
        if SHOW:
            image.show()
        image_name = os.path.join(os.getcwd(),path_offset,
            "floor_{}_points.png".format(floorId))
        image.save(image_name,"PNG")
        image = None

       # overlay(2,6)


if __name__ == "__main__":
    main()