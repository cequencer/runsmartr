#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python


import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
import fiona
from itertools import chain
import requests
import json
import random
import time


def plot_sf(route_coords):

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
        llcrnrlon = coords[0],  # + w*0.55,
        llcrnrlat = coords[1],  # + h*0.45,
        urcrnrlon = coords[2],
        urcrnrlat = coords[3],
        lat_ts=0,
        resolution='i',
        suppress_ticks=True)

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
        x, fc='#55aa55', ec='#448844', lw=.5, alpha=.9
        , zorder=4))

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

    # Draw the map
    m.drawmapscale(coords[0], coords[1],
                   coords[0], coords[1],
                   1.0,
                   units='mi')

    plt.title("run.here")
    fig.set_size_inches(8, 6)
    # plt.savefig('run_here.png', dpi=300, alpha=True)
    plt.show()

    return


def main():

    # Convert to SQL as soon as possible!
    datafile = 'routesSF.dat'

    # Box limits in geographic coordinates
    lng0 = -122.517
    lng1 = -122.357
    lat0 = 37.707
    lat1 = 37.834

    # Loop to get as many routes as possible
    done = False
    while done == False:

        # Generate a random coordinate pair within the bounding box
        lng = random.random() * (lng1-lng0) + lng0
        lat = random.random() * (lat1-lat0) + lat0

        # Call the mapmyrun API for a lat,long and get some route start points
        # Use get_mmf_token.py to get a new authorization if necessary
        url = 'https://api.ua.com/v7.0/route/'
        headers = {'Api-Key': 'nsnxf9ptznw33fzh59wrdezt2rm3fnkt',
                   'Authorization': 'Bearer 0b8a90cbd6f83a724f3467c9f6e49cda644d94e2',
                   'Content-Type': 'application/json'}

        payload = {'close_to_location': ('%.6f,%.6f' % (lat, lng)),
                   'limit': '40'}

        r = requests.get(url, params=payload, headers=headers)

        # Get the coordinates for the start of each route
        route_coords = np.array(re.findall(r'"coordinates":\[(-*\d+.\d+),(\d+.\d+)\]',
                                           r.text)).astype('float')

        # Get route distances
        route_dists = np.array(re.findall(r'"distance":(\d+.\d+)',
                                          r.text)).astype('float')

        # Get route IDs
        route_IDs = np.array(re.findall(r'(\d+)\\/\?format=kml',
                                        r.text)).astype('int')

        # Append coordinates list to file
        if route_coords.shape[0] == 40 and route_dists.shape[0] == 40 and route_IDs.shape[0] == 40:
            fid = open(datafile, 'a')
            for c in range(route_coords.shape[0]):
                fid.write(('%d %f %f %f\n' % (route_IDs[c], route_coords[c,0],
                                            route_coords[c,1], route_dists[c])))
            fid.close()

        # Wait for a random time between 1 and 5 seconds
        time.sleep(random.randrange(1,6))

        # done = True

    # plot_sf(route_coords)

    return


if __name__ == '__main__':
    main()
