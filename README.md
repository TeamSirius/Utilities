## Team Sirius' Marauder's Map Utilities

This repository contains the scripts and tools we use to help build and test the rest of the project.

### Tools

1. NewMapper
  * This is the important one. It allows us to specify an image and then draw in the locations where we will map our known data. There are useful tools like drawing rectangles and filling in a grid. 

1. Locator
  * This script pulls the most recently logged user location from the database and plots it on the Halligan Floor 2 map. This was very useful when initially debugging, but probably not as much going forward.

1. Analysis
  * I have no earthly idea what this does. Probably some sort of analysis

1. Dump
  * This dumps the database


### Use

To use any of these tools, install the required files listed in ```requirements.txt``` and then simply run ```python runner.py DATABASE_PASSWORD```. You'll be walked through a simple menu, and if any of the scripts require more information you'll be asked.
