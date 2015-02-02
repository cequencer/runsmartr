#!/usr/bin/env python

import pandas as pd
import json
from credentials import cred
import psycopg2
from runhere_queries import RunHereDB

import pdb

route_tables = ('routes_bayview', 'routes_bernal_heights',
                'routes_chinatown',
                'routes_crocker_amazon', 'routes_downtown_civic_center',
                'routes_excelsior', 'routes_financial_district',
                'routes_mission', 'routes_nob_hill', 'routes_north_beach',
                'routes_potrero_hill', 'routes_russian_hill',
                'routes_south_of_market', 'routes_visitacion_valley')

def main():
    rh_db = RunHereDB()
    for table_name in route_tables:

        # Consider all valid routes
        route_ids = rh_db.query_raw("""
SELECT mmf_id FROM %s, highways_buffered
WHERE ST_Within(linestring, the_geom);""" %  table_name)
        nroutes = len(route_ids)
        print 'Analyzing %d routes from %s.' % (len(route_ids), table_name)
        route_ids = [node for node_tuple in route_ids for node in node_tuple]
        count = 1
        for id in route_ids:
            
            # for each route, get list of nodes it passes near
            route_points = json.loads(rh_db.query_raw("""
SELECT ST_AsGeoJSON(linestring) FROM %s WHERE mmf_id = '%d';"""
                % (table_name, id))[0][0])['coordinates']
            for lonlat in route_points:

                # get id of nearest node    
                id_NN = rh_db.fetch_nearest_highway_node(*lonlat)

            print 'Done with route %d of %d (%s)' % (count, nroutes, table_name)
            count += 1
            # remove duplicates

            # increment by one the entry for each node in this list
            

if __name__ == '__main__':
    main()
