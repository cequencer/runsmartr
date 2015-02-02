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
from sqlalchemy import *
from geoalchemy2 import Geometry

import pdb


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

    m.readshapefile(
        'sf_data/planning_neighborhoods_geo',
        'sf',
        color='none',
        zorder=2)

    lnglat = [ [ m(x, y, inverse=True) for x, y in poly ] for poly in m.sf ]

    # Set up a map dataframe
    df_map = pd.DataFrame({
        'polygon': [Polygon(xy).wkt for xy in lnglat],
        'name': [w['neighborho'] for w in m.sf_info]})

    pdb.set_trace()

    # Write this dataframe to a postgresql table
    engine = create_engine('postgresql://andy:po9uwe5@localhost:5432/runhere')
    metadata = MetaData(engine)
    my_table = Table('neighborhoods', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', Text),
        Column('polygon', Geometry('POLYGON')))
    my_table.create(engine)
    conn = engine.connect()
    ins = my_table.insert()
    conn.execute(my_table.insert(), df_map.to_dict('records'))

    return


if __name__ == '__main__':
    main()
