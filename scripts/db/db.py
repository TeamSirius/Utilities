import pymysql

DEBUG = False

SERVER_URL = "http://mapbuilder.herokuapp.com/"
if DEBUG:
    SERVER_URL = "http://localhost:5000/"


class Database:
    def __init__(self, password):
        self.password = password
        self.cur = self.get_cur()

    def get_cur(self):
        host = 'seniorindoorlocation.chopksxzy4yo.us-east-1.rds.amazonaws.com'
        conn = pymysql.connect(host=host, db='sirius',
                               user='wormtail', passwd=self.password)
        conn.autocommit(True)
        return conn.cursor()

    def create_location(self):
        self.cur.execute("""DROP TABLE if exists location;""")
        self.cur.execute("""CREATE TABLE location(
        id INT NOT NULL AUTO_INCREMENT,
        PRIMARY KEY(id),
        name TEXT,
        verbose_name TEXT,
        x INT,
        y INT,
        direction INT,
        floor_id INT
        );""")

    def create_AP(self):
        self.cur.execute("""DROP TABLE if exists accesspoint;""")
        self.cur.execute("""CREATE TABLE accesspoint (
        id INT NOT NULL AUTO_INCREMENT,
        PRIMARY KEY(id),
        MAC TEXT,
        strength DOUBLE,
        std_dev FLOAT,
        location_id INT,
        recorded DATETIME
        );""")

    def create_floor(self):
        self.cur.execute("""DROP TABLE if exists floor;""")
        self.cur.execute("""CREATE TABLE floor (
        id INT NOT NULL AUTO_INCREMENT,
        PRIMARY KEY(id),
        imagePath TEXT,
        floor INT,
        building TEXT
        );""")

    def create_demhoes(self):
        self.cur.execute("""DROP TABLE if exists demhoes;""")
        self.cur.execute("""CREATE TABLE demhoes (
        id INT NOT NULL AUTO_INCREMENT,
        PRIMARY KEY(id),
        x TEXT,
        y INT,
        recorded DATETIME
        );""")

    def create_all_tables(self):
        self.create_location()
        self.create_AP()
        self.create_floor()
