"""This is a python script which utilizes the OS X airport utility
    in order to find the location of a user"""

import json
import os
from PIL import Image, ImageDraw
import requests
import subprocess
import sys


SERVER_URL = "http://mapbuilder.herokuapp.com/"
SERVER_URL = "http://localhost:5000/"

floorPaths = ["","../Static_Files/Halligan_2.png","Static_Files/Halligan_1.png"
                ,"../Static_Files/Halligan_2.png","Static_Files/Halligan_1.png"]
        #Ordered by floor index

macIndex = 1
strengthIndex = 2

coverageIndex = 1

def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python {} [coverage]")

    try:
        k = int(sys.argv[coverageIndex])
    except ValueError, e:
        sys.exit("Coverage must be an integer of atleast 1")
    if k < 1:
        sys.exit("Coverage must be an integer of atleast 1")

    macStrength = {} #dictionary of mac address to strength

    for i in range(k):
        networkResults = subprocess.check_output(
        ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport","-s"])

        networkSplit = networkResults.split('\n')[1:] #Ignores the header line
       
        for line in networkSplit:
            info = filter(lambda x: x, line.split(' '))
            if not info:
                continue
            #Info array layout:
            #   [SSID, BSSID, RSSI, CHANNEL, HT, CC, SECURITY]
            if len(info) == 7:
                macStrength[info[macIndex]] = macStrength.get(info[macIndex],0) + int(info[strengthIndex])


    payload = {"lid": -1,"APS": []} #Data format to send to server

    for mac,strength in macStrength.iteritems():
        payload["APS"].append({"MAC":mac,"strength": strength / k})
    r = requests.post(SERVER_URL + "APS", data=json.dumps(payload))
    jsonData = json.loads(r.text)
    x = y = floorId = None
    if "success" in jsonData:
        x = int(jsonData["success"]["x"])
        y = int(jsonData["success"]["y"])
        floorId = jsonData["success"]["floor"]
        floorImagePath = os.path.join(os.getcwd(),floorPaths[floorId])
    if not x:
        exit("Error with server response")

    image = Image.open(floorImagePath)
    
    radius = 5 # point radius
    draw_image = ImageDraw.Draw(image)
    draw_image.ellipse((x-radius,y-radius,x+radius,y+radius), fill='blue',outline='red')
    image.show()

if __name__ == "__main__":
    main()