#!/usr/bin/env python

from shapely.geometry import Point, LineString
import requests
import json
import psycopg2
from credentials import cred

import pdb

def main():
    # Use get_mmf_token.py to get a new authorization if necessary
    headers = cred['mmf']
    # headers = {'Api-Key': 'nsnxf9ptznw33fzh59wrdezt2rm3fnkt',
    #            'Authorization': 'Bearer b1b0e46c53ec8bbb2c8cebdcd9d2d765734108b1',
    #            'Content-Type': 'application/json'}
    # Get list of relevant route IDs
    conn = psycopg2.connect(**cred['db'])
    cur = conn.cursor()
    cur.execute("""
SELECT mmf_id FROM mmf_routes, neighborhoods
WHERE ST_Within(point, polygon) AND name = 'Presidio';""")
    route_IDs = [ el[0] for el in cur.fetchall() ]
    # Loop through these routes, fetching each one
    count = 0
    for id in route_IDs:
        cur.execute("SELECT * FROM routes_presidio WHERE mmf_id = %s;",
                    (id,))
        if cur.fetchall() == []:
            # Call the mapmyrun API for a lat,long and get some route start points
            url = ('https://api.ua.com/v7.0/route/%d/' % id)
            payload = {'field_set': 'detailed',
                       'format': 'json'}
            route = requests.get(url, params=payload, headers=headers)
            if route.status_code == 200:
                route_points = ([ (el['lng'], el['lat'])
                                  for el in route.json()['points'] ])
                if len(route_points) >= 2:
                    # Convert coordinates to Shapely object
                    route_linestring = LineString(route_points)
                    # Insert into database table
                    linestring = 'ST_GeomFromText(%s, 4326)' % (route_linestring.wkt)
                    cur.execute("""
                        INSERT INTO routes_presidio (mmf_id, linestring)
                        VALUES (%s,ST_GeomFromText(%s,4326));""", (id, route_linestring.wkt))
                    conn.commit()
                    print 'done with ID %d (%d of %d)' % (id, count, len(route_IDs))
            else:
                print "failed to fetch route %d, status %d" % (id, route.status_code)
        else:
            print 'already did ID %d (%d of %d)' % (id, count, len(route_IDs))
        count += 1
    cur.close()
    conn.close()
    return

if __name__ == '__main__':
    main()
