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
import flickrapi



def main():

    outfile = 'flickr_corr.dat'

    # Box limits in geographic coordinates
    lng0 = -122.517
    lng1 = -122.357
    lat0 = 37.707
    lat1 = 37.834

    # Use get_mmf_token.py to get a new authorization if necessary
    url = 'https://api.ua.com/v7.0/route/'
    headers = {'Api-Key': 'nsnxf9ptznw33fzh59wrdezt2rm3fnkt',
               'Authorization': 'Bearer 0b8a90cbd6f83a724f3467c9f6e49cda644d94e2',
               'Content-Type': 'application/json'}

    # Initialize flikr API
    api_key = u'61148eca31da30212db319ce60df63e1'
    api_secret = u'e8c32cc2e0018acf'
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')
    flickr.authenticate_via_browser(perms='read')

    # Loop to try as many locations as possible
    done = False
    while done == False:

        # Generate a random coordinate pair within the bounding box
        lng = random.random() * (lng1-lng0) + lng0
        lat = random.random() * (lat1-lat0) + lat0

        # Call the mapmyrun API for a lat,long and get some route start points
        # 40 seems to be the hard limit for the API
        payload = {'close_to_location': ('%.6f,%.6f' % (lat, lng)),
                   'limit': '40'}
        r = requests.get(url, params=payload, headers=headers)

        # Get the coordinates for the start of each route
        route_coords = np.array(re.findall(r'"coordinates":\[(-*\d+.\d+),(\d+.\d+)\]',
                                           r.text)).astype('float')

        # Calculate route density
        dlat = route_coords[:,1] - lat
        dlng = route_coords[:,0] - lng
        route_drad = [ np.sqrt(dx**2 + dy**2) for dx,dy in
                       zip(dlat, dlng) ]
        density = 1/(np.array(route_drad).max()**2)
                    
        # Query Flickr for photos near search lat,lng
        photos = flickr.photos.search(lat=('%f' % lat),
                                      lon=('%f' % lng),
                                      radius='0.5',
                                      extras='views')

        # Calculate flickr score
        flickrscore = np.array([ x['views']
                                 for x in photos['photos']['photo'] ]).astype('int').sum()
        
        # Append density, flickr score to file
        fid = open(outfile, 'a')
        fid.write(('%f %d\n' % (density, flickrscore)))
        fid.close()

        # Wait for a random time between 1 and 5 seconds
        time.sleep(random.randrange(1,6))

        # done = True

    # Plot correlation

    return


if __name__ == '__main__':
    main()
