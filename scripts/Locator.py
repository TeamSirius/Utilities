#   This Script:
#   - Currently:
#       - Receive Point (x,y) from Database
#       - Draws that point on Halligan Floor 2
#   - Future:
#       - Receive Floor Plan Name from Database
#       - Draw Point on Floor Plan File

from PIL import Image, ImageDraw
from db.db import cur
import os


def main():
    halligan_two = os.path.join(os.getcwd(), 'Halligan_2.png')
    cur.execute("""SELECT x,y from demhoes order by id desc limit 1 """)
    row = cur.fetchone()
    if row is not None:
        x = int(float(row[0]))
        y = int(float(row[1]))

    image = Image.open(halligan_two)

    radius = 5 # point radius
    draw_image = ImageDraw.Draw(image)
    draw_image.ellipse((x-radius,y-radius,x+radius,y+radius), fill='blue',outline='red')
    image.show()
    image.close()

if __name__ == '__main__':
    main()
