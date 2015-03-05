# This is a simple web application to handle get and post requests
# related to the indoor mapping project

from db.db import Database
import argparse
import json

q = """select floor_id,accesspoint.location_id,x,y,direction, GROUP_CONCAT(MAC) as MAC_list,GROUP_CONCAT(strength) as strength_list from marauder_accesspoint
 join marauder_location on location.id=accesspoint.location_id
  group by accesspoint.location_id,x,y,direction"""

q2 = """select floor_id,accesspoint.location_id,x,y,direction, GROUP_CONCAT(MAC) as MAC_list,GROUP_CONCAT(strength) as strength_list from marauder_accesspoint
 join marauder_location on location.id=accesspoint.location_id WHERE location.id = 61
  group by accesspoint.location_id,x,y,direction"""


def dump(password, output_file):
    db = Database(password)
    cur = db.get_cur()
    fp = open('output/{}'.format(output_file), 'w+')

    cur.execute(q2)
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
            'rss': map(float, f[6].split(','))
        }
        print json.dumps(msg)
        res.append(msg)
    json.dump(res, fp)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('db_password', help='The database password')
    parser.add_argument('output_file', help='The file to dump to')
    args = parser.parse_args()
    dump(args.db_password, args.output_file)
