# This is a simple web application to handle get and post requests
# related to the indoor mapping project

from flask import Flask
from flask import request
from db import cur
# from db import conn
import json

# import pymysql

app = Flask(__name__)

# The error response json
ERROR_RETURN = json.dumps({'error': "Error"})
SUCCESS_RETURN = json.dumps({'success': "Success"})

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
        fid = int(data['floor_id'])
        x = cur.execute("""SELECT id from floor where id=%s""", (fid,))
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
    #{"lid":location_id, "APS":[ (MAC, STRENGTH),... ]}
    lid = -1
    try:
        data = request.get_json(force=True)
        data["lid"]
        data["APS"]
        lid = cur.execute("""SELECT id from location where id=%s""", [ int(data['lid']) ] )
        if not lid:
            raise "ERROR"
        item['mac']
        item['strength']
        for item in data["APS"]:
            cur.execute("""INSERT into accesspoint (MAC, strength, location_id, recorded
                VALUES ( %s, %s, %s, NOW() )""", (item['MAC'], item['strength'],lid,))
    except:
        return ERROR_RETURN
    return SUCCESS_RETURN

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/floor', methods=['GET','POST'])
def floor():
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
            return {'floor_id':floor_id}
    else:
        r = request.get_json(force=True)
        add_path = r['path']
        floor_num = r['floor_number']
        building_name = r['building']
        try:
            floor_num = int(floor_num)
        except:
            return ERROR_RETURN
        cur.execute("""INSERT into floor (imagePath, floor, building)
            VALUES (%s,%s,%s)""",[add_path,floor_num,building_name])
        return json.dumps({'floor_id':cur.lastrowid})

@app.route('/floors', methods=['GET'])
def floors():
    print 'floors'
    cur.execute("""SELECT building, floor from floor""")
    print 'executed'
    res = []
    for f in cur.fetchall():
        # msg = "{} {}".format(f[0], f[1])
        msg = {
            'building': f[0],
            'floor': f[1]
        }
        res.append(msg)
        print f
    print res
    return json.dumps(res)


@app.route('/aps/<building>/<floor>', methods=['GET'])
def aps_by_building(building, floor):
    # Expects building in form url/aps/[building]/[floor]" -- NOT TRUE
    list_error = ['dummy',  'dummy', 'dummy']
    if not building or not floor:
        return json.dumps(list_error)
    params = [building, floor]
    if len(params) != 2:
        return json.dumps(list_error)
    try:
        floor_number = int(params[1]) + 0
    except:
        return json.dumps(list_error)

    cur.execute("""SELECT id from floor where floor=%s and building=%s""",
                [floor_number, params[0]])
    floor_id = cur.fetchone()

    if not floor_id:
        return json.dumps(list_error)
    print floor_id[0]

    cur.execute("""SELECT id,verbose_name from location where floor_id=%s """,
                [floor_id[0]])

    things = []
    for x in cur.fetchall():
        things.append({
            'id': x[0],
            'verbose_name': x[1]
        })

    return json.dumps(things)


@app.route('/location', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        data = request.form
        keys = ['x', 'y', 'd', 'name', 'verbose', 'floor_id']
        if not all_in(keys, data):
            return ERROR_RETURN
        x = int(data['x'])
        y = int(data['y'])
        d = int(data['d'])
        fid = int(data['floor_id'])
        verb = data['verbose']
        name = data['name']
        if all_in(keys, data) and valid_location(data):

            cur.execute("""INSERT INTO location (verbose_name,name,x,y,direction,floor_id)
                VALUES (%s,%s,%s,%s,%s,%s);""", [verb, name, x, y, d, fid])
        else:
            return ERROR_RETURN
    else:
        try:
            fid = request.args.get('lid')
            if not fid:
                return ERROR_RETURN
            x = cur.execute("""SELECT verbose_name,name,x,y,direction,floor_id from location where id=%s""",
                            [fid]).fetchone()
            if not x:
                return ERROR_RETURN
            keys = ['verbose_name', 'name', 'x', 'y', 'd', 'floor_id']
            json_return = {}
            for i in range(6):
                json_return[keys[i]] = x[i]
            return json.dumps(json_return)

        except:
            return ERROR_RETURN



if __name__ == '__main__':
    app.run()
