#!/usr/bin/env python


import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
from mpl_toolkits.basemap import Basemap
import shapely.ops
import shapely.wkt
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape, box
from shapely.prepared import prep
from descartes import PolygonPatch
import fiona
from itertools import chain
import requests
import json
import random
import time
import psycopg2
import geopy.geocoders

import pdb


def plot_sf(all_highways, m, route_coords, lng0, lat0):

    m.readshapefile(
        'sf_data/planning_neighborhoods_geo',
        'sf',
        color='none',
        zorder=2)

    # Set up a map dataframe
    df_map = pd.DataFrame({
        'poly': [Polygon(xy) for xy in m.sf],
        'name': [w['neighborho'] for w in m.sf_info],
    })

    # Create Point objects in map coordinates from route_coords
    # lat and long values
    map_points = pd.Series([Point(m(mapped_x, mapped_y))
                            for mapped_x, mapped_y in route_coords])
    route_points = MultiPoint(list(map_points.values))

    # Draw neighborhood patches from polygons
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='#aaaaaa', ec='#444444', lw=.5, alpha=.9,
        zorder=4))

    plt.clf()
    fig = plt.figure()
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)

    # Plot all highways
    all_highways_json = json.loads(all_highways)
    for highway in all_highways_json['coordinates']:

        lng, lat = zip(*highway)

        m.plot(lng, lat, latlon=True, color='red')

    # Plot run coordinates on map
    m.scatter([geom.x for geom in route_points],
              [geom.y for geom in route_points],
              marker='o', lw=0.25, s=10,
              facecolor='blue', edgecolor='blue',
              alpha=0.9, zorder=3)

    m.scatter(*m(lng0, lat0), marker='o', lw=0.25, s=100,
              facecolor='#00ff00', edgecolor='#00ff00',
              alpha=1.0, zorder=3)

    # Plot neighborhoods by adding the PatchCollection to the axes instance
    ax.add_collection(PatchCollection(df_map['patches'].values,
                                      match_original=True))

    # plt.title("run.here")
    fig.set_size_inches(10, 10)
    plt.tight_layout()
    plt.savefig('run_here.png', dpi=60, alpha=True)
    # plt.show()

    return


def main():

    geocoder = geopy.geocoders.GoogleV3(api_key='AIzaSyBg00FnRgYjGBfj8z9R0hII5Sv63QlROvI')
    location = geocoder.geocode('ferry building san francisco')

    lng = location.longitude
    lat = location.latitude

    # Initialize Basemap object
    # Get shapefile data
    shape_file = 'sf_data/planning_neighborhoods_geo.shp'

    # Plot locations on a map of SF neighborhoods
    shp = fiona.open(shape_file)
    crs_data = shp.crs
    bds = shp.bounds
    shp.close()
    ll = (bds[0], bds[1])
    ur = (bds[2], bds[3])
    coords = list(chain(ll, ur))
    w, h = coords[2] - coords[0], coords[3] - coords[1]

    # # Create a Basemap instance, and open the shapefile
    # m = Basemap(
    #     projection='tmerc',
    #     lon_0 = lng,
    #     lat_0 = lat,
    #     ellps = 'WGS84',
    #     llcrnrlon = coords[0],
    #     llcrnrlat = coords[1],
    #     urcrnrlon = coords[2],
    #     urcrnrlat = coords[3],
    #     lat_ts=0,
    #     resolution='i',
    #     suppress_ticks=True)

    # Create a Basemap instance, and open the shapefile
    m = Basemap(
        projection='tmerc',
        lon_0 = lng,
        lat_0 = lat,
        ellps = 'WGS84',
        width = 3200,
        height = 3200,
        lat_ts=0,
        resolution='i',
        suppress_ticks=True)

    # Calculate bounding box in lat, lng
    x0, y0 = m(lng, lat)
    lng0, lat0 = m(x0-1600, y0-1600, inverse=True)
    lng1, lat1 = m(x0+1600, y0+1600, inverse=True)
    bbox = box(lng0, lat0, lng1, lat1)

    # Get roads & trails from database
    conn = psycopg2.connect(dbname='runhere', user='andy', password='po9uwe5')
    cur = conn.cursor()
    cur.execute("""
SELECT ST_AsGeoJSON(ST_Union(ST_Accum(geometry)))
FROM (SELECT linestring AS geometry
FROM ways WHERE tags::hstore ? 'highway') AS highways
WHERE ST_Intersects(geometry, ST_PolygonFromText(%s, 4326));""",
(shapely.wkt.dumps(bbox),))
    all_highways = cur.fetchone()[0]

#     # Get roads buffered by 20 m
#     conn = psycopg2.connect(dbname='runhere', user='andy', password='po9uwe5')
#     cur = conn.cursor()
#     cur.execute("""
# SELECT ST_AsText(ST_Buffer(ST_Union(ST_Accum(geometry)), 20))
# FROM
# (SELECT tags->'name' AS name, tags->'highway' AS category, linestring AS geometry
# FROM  ways WHERE tags::hstore ? 'highway') AS highways,
# (SELECT polygon FROM neighborhoods
# WHERE name = 'Potrero Hill' OR name = 'Mission') as potrero
# WHERE ST_Intersects(geometry, polygon);""")
#     highways_boundary = shapely.wkt.loads(cur.fetchone()[0])

    # Get route coordinates from database
    conn = psycopg2.connect(dbname='runhere', user='andy', password='po9uwe5')
    cur = conn.cursor()
    cur.execute("""
SELECT ST_AsGeoJSON(point) FROM mmf_routes
WHERE ST_Within(point, ST_PolygonFromText(%s, 4326));""",
(shapely.wkt.dumps(bbox),))
    route_coords = [ json.loads(el[0]) for el in cur.fetchall() ]
    route_coords = np.array([ el['coordinates'] for el in route_coords ])

    # Plot buffered roadways
    plot_sf(all_highways, m, route_coords, lng, lat)

    return


if __name__ == '__main__':
    main()
