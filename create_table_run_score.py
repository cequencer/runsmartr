#!/usr/bin/env python

import pandas as pd
import json
from credentials import cred
import psycopg2
from runhere_queries import RunHereDB

import pdb

route_tables = ('routes_south_of_market', 'routes_bayview', 'routes_bernal_heights',
                'routes_chinatown',
                'routes_crocker_amazon', 'routes_downtown_civic_center',
                'routes_excelsior', 'routes_financial_district',
                'routes_mission', 'routes_nob_hill', 'routes_north_beach',
                'routes_potrero_hill', 'routes_russian_hill',
                'routes_visitacion_valley')

def main():
    rh_db = RunHereDB()
    for table_name in route_tables:
        route_ids = rh_db.query_raw("""
SELECT mmf_id FROM %s;""" %  table_name)
        route_ids = [node for node_tuple in route_ids for node in node_tuple]
        for id in route_ids:
            
            # for each route, get list of nodes it passes near
            route_points = json.loads(rh_db.query_raw("""
SELECT ST_AsGeoJSON(linestring) FROM %s WHERE mmf_id = '%d';"""
                % (table_name, id))[0][0])['coordinates']
            for lonlat in route_points:

                # get id of nearest node    
                print lonlat
                id_NN = rh_db.fetch_nearest_highway_node(*lonlat)
                print id_NN

            # remove duplicates
            pdb.set_trace()

            # increment by one the entry for each node in this list
            

if __name__ == '__main__':
    main()
