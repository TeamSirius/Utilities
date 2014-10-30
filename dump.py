# This is a simple web application to handle get and post requests
# related to the indoor mapping project

from db import cur
# from db import conn
import json

q = """select floor_id,accesspoint.location_id,x,y,direction, GROUP_CONCAT(MAC) as MAC_list,GROUP_CONCAT(strength) as strength_list from accesspoint
 join location on location.id=accesspoint.location_id
  group by accesspoint.location_id,x,y,direction"""

def dump():
    fp = open('access_points.json', 'w')

    cur.execute(q)
    access_points = cur.fetchall()
    res = []
    for f in access_points:
        print f
        msg = {
            'floor_id': f[0],
            'location_id': f[1],
            'x': f[2],
            'y': f[3],
            'direction': f[4],
            'macs': f[5].split(','),
            'rss': map(int, f[6].split(','))
        }
        print json.dumps(msg)
        res.append(msg)
    print json.dump(res, fp)
    fp.close()


# json looks like:
# [
#     {'direction': int,
#      'macs': list(str),
#      'floor_id': int,
#      'y': int,
#      'x': int,
#      'location_id': int,
#      'rss': list(int)
#     },
#     ....
# ]

if __name__ == '__main__':
    dump()
