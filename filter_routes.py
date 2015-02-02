#!/usr/bin/env python


import psycopg2
import pdb
import time


def main():

    conn = psycopg2.connect(dbname='runhere', user='andy', password='po9uwe5')
    cur = conn.cursor()

    # Store buffered roads/trails as new geography (buffer by 30 m)
    print 'Adding geometry to database ...'
    cur.execute("""
CREATE TABLE highways_buffered AS
(SELECT ST_Buffer(ST_Collect(highway)::geography, 30)::geometry AS the_geom FROM
(SELECT linestring AS highway FROM ways, neighborhoods
WHERE tags::hstore ? 'highway' AND ST_Intersects(linestring, polygon)) AS foo);""")
    conn.commit()

#     cur.execute("""
# SELECT ST_AsGeoJSON(ST_Union(ST_Accum(geometry)))
# FROM (SELECT linestring AS geometry
# FROM ways WHERE tags::hstore ? 'highway') AS highways
# WHERE ST_Intersects(geometry, ST_PolygonFromText(%s, 4326));""",
# (shapely.wkt.dumps(bbox),))
#     all_highways = cur.fetchone()[0]

#     # Get roads buffered by 20 m
#     cur.execute("""
# SELECT COUNT(highway) FROM
# (SELECT linestring AS highway FROM ways, neighborhoods
# WHERE tags::hstore ? 'highway' AND ST_Within(linestring, polygon)) AS foo;
# """, (shapely.wkt.dumps(bbox),))
#     print cur.fetchall()

#     t = time.time()
#     # Get roads/trails buffered by 20 m
#     cur.execute("""
# SELECT ST_AsText(ST_Buffer(ST_Collect(highway)::geography, 20)) FROM
# (SELECT linestring AS highway FROM ways, neighborhoods
# WHERE tags::hstore ? 'highway' AND ST_Intersects(linestring, polygon)) AS foo;""",
#                 (shapely.wkt.dumps(bbox),))
#     highways_boundary = shapely.ops.transform(m, shapely.wkt.loads(cur.fetchone()[0]))
#     print time.time()-t

#     # Get route coordinates from database
#     cur.execute("""
# SELECT ST_AsGeoJSON(point) FROM mmf_routes
# WHERE ST_Within(point, ST_PolygonFromText(%s, 4326));""",
# (shapely.wkt.dumps(bbox),))
#     route_coords = [ json.loads(el[0]) for el in cur.fetchall() ]
#     route_coords = np.array([ el['coordinates'] for el in route_coords ])


if __name__ == '__main__':
    main()
