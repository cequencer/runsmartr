#!/usr/bin/env python
'''Class for plotting geometries on top of SF-neighborhood outlines.
'''

import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import psycopg2
from credentials import cred
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch

# import pandas as pd
# import re
# import pandas as pd
# import matplotlib.font_manager as fm
# import shapely.ops
# import shapely.wkt
# from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape, box
# from shapely.prepared import prep
# import fiona
# from itertools import chain
# import requests
# import random
# import time
# import geopy.geocoders

import pdb

class SFPlot:

    def __init__(self):
        self.db_conn = psycopg2.connect(**cred['db'])
        self.db_cur = self.db_conn.cursor()
        self.the_map = self.get_basemap()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, axisbg='w', frame_on = False)
        self.np_patches = self.get_nb_patches()

    def get_bbox(self):
        self.db_cur.execute("""
SELECT ST_AsGeoJSON(ST_Envelope(ST_Collect(polygon)))
FROM neighborhoods;""")
        bbox = json.loads(self.db_cur.fetchone()[0])
        return np.array(bbox['coordinates'][0])

    def get_basemap(self):
        bbox = self.get_bbox()[(0, 2),:]
        m = Basemap(projection = 'tmerc',
            lon_0 = bbox[:,0].mean(), lat_0 = bbox[:,1].mean(),
            ellps = 'WGS84',
            llcrnrlon = bbox[0,0], llcrnrlat = bbox[0,1],
            urcrnrlon = bbox[1,0], urcrnrlat = bbox[1,1],
            lat_ts=0, resolution='i', suppress_ticks=True)
        return m

    def get_nb_patches(self):
        '''Return polygon-patch collection of neighborhoods.
        '''
        

# def plot_linestring():
#     return

# def plot_polygon():
#     return

# def plot_multipolygon():
#     return

# def main():
#     return

# if __name__ == '__main__':
#     main()
