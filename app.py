# This is a simple web application to handle get and post requests
# related to the indoor mapping project

from flask import Flask
from flask import request
from db import cur, DEBUG
import sys,os
# from db import conn
import json

# import pymysql

app = Flask(__name__)

# The error response json
ERROR_RETURN = json.dumps({'error': "Error"})
SUCCESS_RETURN = json.dumps({'success': "Success"})

def log(msg):
    sys.stderr.write("{}\n".format(msg))

def handle_exception(e):
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    log("Error: {} in file {} at line {}".format(str(repr(e)), fname, exc_tb.tb_lineno))


def all_in(L, dic):
    """Given a list and a dictionary checks that
        all values in the list are keys in the dictionary"""
    for item in L:
        if item not in dic:
            return False
    return True

def valid_location(data):
    try:
        # x = int(data['x'])
        # y = int(data['y'])
        # d = int(data['d'])
        #TODO: REMOVE COMMENTS
        fid = int(data['floor_id'])
        x = cur.execute("""SELECT id from floor where id=%s""", (fid,)) #TODO: remove setting to x
        x = cur.fetchone()
        if x:
            return True
        else:
            return False
    except Exception:
        return False

@app.route('/APS', methods=['POST'])
def APS():
    #Takes a posted parameter of format:
    #{"lid":location_id, "APS":[ {"MAC":MAC, "strength":STRENGTH, "std": STD},... ]}

    #TODO: CHANGE NAME OF THIS OR /aps 
    lid = -1
    try:
        data = request.get_json(force=True) #TODO: REMOVE FORCE IF POSSIBLe
        lid = int(data['lid'])
        if lid < 1:
            from kNN import demo, AccessPoint
            from datetime import datetime
            knnData = {}
            APS = []
            for item in data["APS"]:
                if 'std' in item:
                    APS.append( ( item['MAC'], float(item['strength']), float(item['std']), datetime.now(), 10 ) )
                else:
                    APS.append( ( item['MAC'], float(item['strength']), 0, datetime.now(), 10 ) )
            (x, y) = demo(APS)
            cur.execute("""INSERT into demhoes (x,y, recorded)
                    VALUES ( %s, %s, NOW() )""", [x,y]) #UTC TIME
            return json.dumps({'success': {"x" : x, "y" : y}})
        else:
            cur.execute("""SELECT count(*) from accesspoint where location_id=%s""",[lid])
            count = cur.fetchone()[0]
            if not count or int(count) == 0: #Will only log new data -- if already logged will ignore
                for item in data["APS"]:
                    if 'std' in item:
                        cur.execute("""INSERT into accesspoint (MAC, strength, location_id, std_dev, recorded)
                            VALUES ( %s, %s, %s,%s, NOW() )""",
                            [item['MAC'], float(item['strength']),lid, float(item['std'])] ) #UTC TIME
                    else:
                        cur.execute("""INSERT into accesspoint (MAC, strength, location_id, std_dev, recorded)
                            VALUES ( %s, %s, %s,%s, NOW() )""",
                            [item['MAC'], float(item['strength']),lid, -1] ) #UTC TIME
    except Exception, e:
        handle_exception(e)
        return ERROR_RETURN
    return SUCCESS_RETURN

@app.route('/')
def hello_world():
    return 'Hello BERT!'

@app.route('/floor', methods=['GET','POST'])
def floor():
    #TODO: MAKE JUST POST THAT CHECKS AND GIVES ID
    #TODO: CHANGE NAME OF THIS OR FLOORS
    #TODO: ENSURE THAT floor unique by building + floor_number
    if request.method == 'GET':
        requested_path = request.args.get('path')
        if not requested_path:
            return ERROR_RETURN
        cur.execute("""SELECT id from floor where imagePath=%s""",
                    [requested_path])
        floor_id = cur.fetchone()
        if not floor_id:
            return ERROR_RETURN
        else:
            return json.dumps({'floor_id':floor_id[0]})
    else:
        r = request.get_json(force=True) #TODO: LOOK INTO FORCe LUKE said YODA
        add_path = r['path']
        floor_num = r['floor_number']
        building_name = r['building']
        try:
            floor_num = int(floor_num)
        except Exception, e:
            handle_exception(e)
            return ERROR_RETURN
        cur.execute("""INSERT into floor (imagePath, floor, building)
            VALUES (%s,%s,%s)""",[add_path,floor_num,building_name])
        return json.dumps({'floor_id':cur.lastrowid})

@app.route('/floors', methods=['GET'])
def floors():
    #TODO: CHANGE NAME OF THIS OR FLOOR
    cur.execute("""SELECT building, floor from floor""")
    res = []
    for f in cur.fetchall():
        # msg = "{} {}".format(f[0], f[1])
        msg = {
            'building': f[0],
            'floor': f[1]
        }
        res.append(msg)
    return json.dumps(res)


@app.route('/aps/<building>/<floor>', methods=['GET'])
def aps_by_building(building, floor):
    if not building or not floor:
        return ERROR_RETURN
    params = [building, floor]
    try:
        floor_number = int(params[1])
    except Exception, e:
        handle_exception(e)
        return ERROR_RETURN

    cur.execute("""SELECT id from floor where floor=%s and building=%s""",
                [floor_number, params[0]])
    floor_id = cur.fetchone()

    if not floor_id:
        return ERROR_RETURN

    cur.execute("""SELECT id,verbose_name,x,y from location where floor_id=%s """,
                [floor_id[0]])

    things = [] #TODO: CHANGE NAMES fosho
    for x in cur.fetchall():
        things.append({
            'id': x[0],
            'verbose_name': x[1],
            'x':x[2],
            'y':x[3]
        })

    return json.dumps(things)


@app.route('/location', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        data = request.get_json(force=True) #TODO: force again
        keys = ['x', 'y', 'd', 'name', 'verbose', 'floor_id']
        if not all_in(keys, data):
            return ERROR_RETURN
        #TODO: PUT IN TRY
        x = int(data['x'])
        y = int(data['y'])
        d = int(data['d'])
        fid = int(data['floor_id'])
        verb = data['verbose']
        name = data['name']
        if all_in(keys, data) and valid_location(data): #TODO: DONT NEED TO CHECK AGAIN
            #TODO: RUN VALID_LOCATION BEFORE INTS
            cur.execute("""INSERT INTO location (verbose_name,name,x,y,direction,floor_id)
                VALUES (%s,%s,%s,%s,%s,%s);""", [verb, name, x, y, d, fid])
            return SUCCESS_RETURN
        else:
            return ERROR_RETURN
    else:
        try:
            fid = request.args.get('lid') #TODO: CHANGE NAMES
            if not fid:
                return ERROR_RETURN
            x = cur.execute("""SELECT verbose_name,name,x,y,direction,floor_id from location where id=%s""",
                            [fid]).fetchone()
            if not x:
                return ERROR_RETURN
            keys = ['verbose_name', 'name', 'x', 'y', 'd', 'floor_id']
            json_return = {}
            for i in range(6): #TODO: CHANGE TO enumerate(KEYS)
                json_return[keys[i]] = x[i]
            return json.dumps(json_return) #TODO: MAKE RESPONSE FUNCTION --> string to json

        except Exception, e:
            handle_exception(e)
            return ERROR_RETURN


#TODO: LOG SPECIFIC ERRORS --> build log exception function
# try:
#     pass
# except Exception,e :
#     log_e(e)
#     return ERROR_RETURN
#TODO: BUILD IN PYTHON LOGGIN MODULE

if __name__ == '__main__':
    app.run()
