# This is a simple web application to handle get and post requests
# related to the indoor mapping project

from flask import Flask
from db import cur
# from db import conn
import json

# import pymysql

app = Flask(__name__)

# The error response json
ERROR_RETURN = json.dumps({'error': "Error"})


def all_in(L, dic):
    """Given a list and a dictionary checks that
        all values in the list are keys in the dictionary"""
    for item in L:
        if item not in dic:
            return False
    return True


def valid_location(data):
    try:
        x = int(data['x'])
        # y = int(data['y'])
        # d = int(data['d'])
        fid = int(data['floor_id'])
        x = cur.execute("""SELECT id from floor where id=%s""", [fid])
        x = x.fetchone()
        if x:
            return True
        else:
            return False
    except:
        return False


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/floors', methods=['GET'])
def floors():
    cur.execute("""SELECT building, floor from floor""")
    res = []
    for f in cur.fetchall():
        res.append(f[0] + " " + str(f[1]))
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
    cur.execute("""SELECT verbose_name from location where floor_id=%s """,
                [floor_id])
    return json.dumps([x[0] for x in cur.fetchall()])


@app.route('/location', methods=['GET', 'POST'])
def location():
    if request.method == 'POST':
        data = request.form
        keys = ['x', 'y', 'd', 'name', 'verbose', 'floor_id']
        x = int(data['x'])
        y = int(data['y'])
        d = int(data['d'])
        fid = int(data['floor_id'])
        verb = data['verbose']
        name = data['name']
        if all_in(keys, data) and valid_location(keys, data):
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
            return json_return

        except:
            return ERROR_RETURN


if __name__ == '__main__':
    app.run()
