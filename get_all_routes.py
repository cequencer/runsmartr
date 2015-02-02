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

    # Create Point objects in map coordinates from route_coords
    # lat and long values
    map_points = pd.Series([Point(m(mapped_x, mapped_y))
                            for mapped_x, mapped_y in route_coords])
    route_points = MultiPoint(list(map_points.values))

    # Draw neighborhood patches from polygons
    df_map['patches'] = df_map['poly'].map(lambda x: PolygonPatch(
        x, fc='#55aa55', ec='#448844', lw=.5, alpha=.9,
        zorder=4))

    map_left = PolygonPatch(region_left, fc='#000000', ec='#000000',
                            lw=.5, alpha=.3, zorder=5)

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
    ax.add_patch(map_left)

    plt.title("run.here")
    fig.set_size_inches(8, 6)
    # plt.savefig('run_here.png', dpi=300, alpha=True)
    plt.show()

    return


def main():

    # Convert to SQL as soon as possible!
    datafile = 'routesSFlandsEnd.dat'
    shapefile = 'regionSFlandsEnd.dat'

#     # Bounding box in geographic coordinates
#     lng0 = -122.517
#     lng1 = -122.355
#     lat0 = 37.707
#     lat1 = 37.834

    # Land's End
    lng0 = -122.521
    lng1 = -122.484
    lat0 = 37.778
    lat1 = 37.793

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

    # Use get_mmf_token.py to get a new authorization if necessary
    url = 'https://api.ua.com/v7.0/route/'
    headers = {'Api-Key': 'nsnxf9ptznw33fzh59wrdezt2rm3fnkt',
               'Authorization': 'Bearer 0b8a90cbd6f83a724f3467c9f6e49cda644d94e2',
               'Content-Type': 'application/json'}

    # Initialize Polygon to keep track of space that has definitively
    # been accounted for.  The intersection of this and the bounding
    # box can be compared with the box itself to know when I am done.
    #
    # Can use a Basemap object to convert to map-projection
    # coordinates
    bbox = Polygon([m(lng0, lat0), m(lng1, lat0), m(lng1, lat1), m(lng0, lat1)])
    region_covered = Polygon()
    # fid = open(shapefile, 'r')
    # region_covered = shapely.wkt.loads(fid.read())
    # fid.close()

    # Loop until the whole bbox has been covered
    done = False
    # while done == False:
    for n in range(500):

        # Use shapely.object.representative_point() to get a point
        # from the remaining area in the bbox
        lng, lat = m(bbox.difference(region_covered).representative_point().x,
                     bbox.difference(region_covered).representative_point().y, inverse=True)

        # Call the mapmyrun API for a lat,long and get some route start points
        payload = {'close_to_location': ('%.6f,%.6f' % (lat, lng)),
                   'limit': '40'}
        r = requests.get(url, params=payload, headers=headers)

        route_coords =  np.array([ route['starting_location']['coordinates']
                                   for route in r.json()['_embedded']['routes'] ]).astype('float')
        route_IDs =  np.array([ route['_links']['self'][0]['id']
                                for route in r.json()['_embedded']['routes'] ]).astype('int')

        # Append coordinates list to file
        fid = open(datafile, 'a')
        for c in range(route_coords.shape[0]):
            fid.write(('%d %f %f\n' % (route_IDs[c], route_coords[c,0],
                                        route_coords[c,1])))
        fid.close()

        # Adjust the region_covered representation by adding a circle
        # around the query point
        search_point = Point(m(lng, lat))
        route_points = [ Point(m(r_lng, r_lat)) for r_lng, r_lat in
                         route_coords ]
        route_search_radii = np.array([ search_point.distance(r_point) for
                                        r_point in route_points ])
        new_region_covered = search_point.buffer(route_search_radii.max())
        region_covered = shapely.ops.unary_union([region_covered, new_region_covered])

        # Save shapely representation region_covered
        fid = open(shapefile, 'w')
        fid.write(region_covered.wkt)

        # # Wait for a random time between 1 and 5 seconds
        # time.sleep(1)

        # Print percent remaining
        print('%3d %f' % (n, bbox.difference(region_covered).area / bbox.area))

        # done = True

    # plot_sf(route_coords, m, bbox.difference(region_covered))

    return


if __name__ == '__main__':
    main()
