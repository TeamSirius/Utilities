
import pymysql
import os
#insert your sql information here
password = os.environ.get('SIRIUS_PASSWORD')
if password is None:
    raise Exception('Could not get database password')
conn = pymysql.connect(host='seniorindoorlocation.chopksxzy4yo.us-east-1.rds.amazonaws.com', db='sirius', user='wormtail', passwd=password)
conn.autocommit(True)

cur = conn.cursor()
DEBUG = False

SERVER_URL = "http://mapbuilder.herokuapp.com/"
if DEBUG:
  SERVER_URL = "http://localhost:5000/"

def create_location():
    cur.execute("""DROP TABLE if exists location;""")
    cur.execute("""CREATE TABLE location(
      id INT NOT NULL AUTO_INCREMENT,
      PRIMARY KEY(id),
      name TEXT,
      verbose_name TEXT,
      x INT,
      y INT,
      direction INT,
      floor_id INT
    );""")

def create_AP():
    cur.execute("""DROP TABLE if exists accesspoint;""")
    cur.execute("""CREATE TABLE accesspoint (
      id INT NOT NULL AUTO_INCREMENT,
      PRIMARY KEY(id),
      MAC TEXT,
      strength DOUBLE,
      std_dev FLOAT,
      location_id INT,
      recorded DATETIME
    );""")

def create_floor():
    cur.execute("""DROP TABLE if exists floor;""")
    cur.execute("""CREATE TABLE floor (
      id INT NOT NULL AUTO_INCREMENT,
      PRIMARY KEY(id),
      imagePath TEXT,
      floor INT,
      building TEXT
    );""")

def create_demhoes():
    cur.execute("""DROP TABLE if exists demhoes;""")
    cur.execute("""CREATE TABLE demhoes (
      id INT NOT NULL AUTO_INCREMENT,
      PRIMARY KEY(id),
      x TEXT,
      y INT,
      recorded DATETIME
    );""")


def create_all_tables():
    create_location()
    create_AP()
    create_floor()

