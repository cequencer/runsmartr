#!/usr/bin/env python

import numpy as np
import json
from runhere_queries import RunHereDB

route_tables = ('routes_presidio',)

# Done:
# route_tables = ('routes_south_of_market', 'routes_potrero_hill',
#                 'routes_financial_district', 'routes_downtown_civic_center',
#                 'routes_mission','routes_bayview', 'routes_bernal_heights',
#                 'routes_chinatown','routes_crocker_amazon',
#                 'routes_excelsior',
#                 'routes_nob_hill', 'routes_north_beach',
#                 'routes_russian_hill',
#                 'routes_visitacion_valley')

# route_tables = ('routes_bayview', 'routes_bernal_heights',
#                 'routes_chinatown','routes_crocker_amazon',
#                 'routes_downtown_civic_center', 'routes_excelsior',
#                 'routes_financial_district', 'routes_mission',
#                 'routes_nob_hill', 'routes_north_beach',
#                 'routes_potrero_hill', 'routes_russian_hill',
#                 'routes_south_of_market', 'routes_visitacion_valley')

def main():
    rh_db = RunHereDB()
    for table_name in route_tables:
        print 'Getting list of valid routes from %s' % (table_name,)
        route_ids = rh_db.fetch_valid_runs(table_name)
        nroutes = len(route_ids)
        print 'Analyzing %d routes from %s.' % (len(route_ids), table_name)
        route_ids = [node for node_tuple in route_ids for node in node_tuple]
        count = 1
        for id in route_ids:
            if not rh_db.already_done(id):
                route_points = json.loads(rh_db.query_raw(
                    "SELECT ST_AsGeoJSON(linestring) FROM %s WHERE mmf_id = '%d';"
                    % (table_name, id))[0][0])['coordinates']
                nearest_nodes = np.zeros(len(route_points))
                for n in range(len(route_points)):
                    nearest_nodes[n] = rh_db.fetch_nearest_highway_node(*route_points[n])
                print 'Done with route %d of %d (%s)' % (count, nroutes, table_name)
                nearest_nodes = np.unique(nearest_nodes)
                # rh_db.update_stats_mmf_score(nearest_nodes, id)
                rh_db.update_stats_route_nodes(id, nearest_nodes)
            else:
                print 'Already did route %d (%d of %d in %s)' % (id, count,
                                                                 nroutes, table_name)
            count += 1
            

if __name__ == '__main__':
    main()
