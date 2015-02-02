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
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
import fiona
from itertools import chain
import requests
import json
import random
import time
import psycopg2

import pdb


def plot_sf(route_coords, m, region_left):

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

#     # Set up map_left dataframe
#     map_left = pd.DataFrame({
#         'poly': list(region_left),
#     })

    # Create Point objects in map coordinates from route_coords
    # lat and long values
    map_points = pd.Series([Point(m(mapped_x, mapped_y))
                            for mapped_x, mapped_y in route_coords])
    route_points = MultiPoint(list(map_points.values))

    # Draw neighborhood patches from polygons
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='#aaaaaa', ec='#444444', lw=.5, alpha=.9,
        zorder=4))

    # If Polygon
    map_left = PolygonPatch(region_left, fc='#000000', ec='#000000',
                            lw=.5, alpha=.3, zorder=5)

    # If MultiPolygon
    # map_left['patches'] = map_left['poly'].map(lambda x: PolygonPatch(
    #     x, fc='#000000', ec='#000000', lw=.5, alpha=.3, zorder=5))

    plt.clf()
    fig = plt.figure()
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)

    # Plot run coordinates on map
    m.scatter([geom.x for geom in route_points],
              [geom.y for geom in route_points],
              marker='o', lw=0.25, s=10,
              facecolor='#aa3333', edgecolor='#aa3333',
              alpha=0.9, zorder=3)

    # Plot neighborhoods by adding the PatchCollection to the axes instance
    ax.add_collection(PatchCollection(df_map['patches'].values,
                                      match_original=True))
    # Plot region I still need to get from database
    # ax.add_patch(map_left)
    # ax.add_collection(PatchCollection(map_left['patches'].values,
    #                                   match_original=True))

    fig.set_size_inches(10, 10)
    plt.tight_layout()
    plt.savefig('run_here.png', dpi=60, alpha=True)
    plt.show()

    return


def main():

    # Convert to SQL as soon as possible!
    datafile = 'mmf/routes_all_SF.dat'
    shapefile = 'regionSF.dat'

    # Bounding box in geographic coordinates
    lng0 = -122.517
    lng1 = -122.355
    lat0 = 37.707
    lat1 = 37.834

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

    # Create a Basemap instance, and open the shapefile
    m = Basemap(
        projection='tmerc',
        lon_0 = -122.0,
        lat_0 = 37.0,
        ellps = 'WGS84',
        llcrnrlon = coords[0],
        llcrnrlat = coords[1],
        urcrnrlon = coords[2],
        urcrnrlat = coords[3],
        lat_ts=0,
        resolution='i',
        suppress_ticks=True)

    # Initialize Polygon to keep track of space that has definitively
    # been accounted for.  The intersection of this and the bounding
    # box can be compared with the box itself to know when I am done.
    #
    # Can use a Basemap object to convert to map-projection
    # coordinates
    bbox = Polygon([m(lng0, lat0), m(lng1, lat0), m(lng1, lat1), m(lng0, lat1)])

    # Get route coordinates from database
    conn = psycopg2.connect(dbname='runhere', user='andy', password='po9uwe5')
    cur = conn.cursor()
    cur.execute("SELECT ST_AsGeoJSON(point) FROM mmf_routes, neighborhoods WHERE ST_Within(point, polygon);")
    route_coords = [ json.loads(el[0]) for el in cur.fetchall() ]
    route_coords = np.array([ el['coordinates'] for el in route_coords ])

    print route_coords.shape

    # route_coords = np.loadtxt(datafile)[:,1:3]
    # route_coords = np.array([[lng0,lat0],[lng1,lat1]])

    fid = open(shapefile, 'r')
    region_covered = shapely.wkt.loads(fid.read())
    fid.close()

    plot_sf(route_coords, m, bbox.difference(region_covered))

    return


if __name__ == '__main__':
    main()
