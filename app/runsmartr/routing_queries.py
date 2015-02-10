from credentials import cred
import psycopg2
import json
import geopy.geocoders
from random import random as rnd

import pdb

class RoutingDB:

    def __init__(self, intersections_only=False):
        if intersections_only:
            self.rnodes_table = 'rnodes_intersections'
            self.routing_table = 'routing_intersections'
        else:
            self.rnodes_table = 'rnodes'
            self.routing_table = 'routing'
        self.db_conn = psycopg2.connect(**cred['db'])
        self.db_cur = self.db_conn.cursor()
        self.geocoder = geopy.geocoders.GoogleV3(**cred['google'])

    def rand_rnode_within_m(self, rnode, m):
        query = """
SELECT id FROM
    (SELECT ST_Translate(point, %f, %f) AS search_point
     FROM %s WHERE id = '%d') AS rnode,
    %s
ORDER BY search_point <-> point LIMIT 1;""" % ((m-m/2.)*rnd()/89012.,
                                               (m-m/2.)*rnd()/110978.,
                                               self.rnodes_table, rnode,
                                               self.rnodes_table)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def rand_rnode_within_threshold(self, rnode, threshold):
        query = """
SELECT id FROM
    (SELECT id FROM
        %s,
        (SELECT point AS origin FROM %s WHERE id = '%d')
            AS nodes_origin
    ORDER BY origin <-> point
    LIMIT %d) AS knn
ORDER BY RANDOM() LIMIT 1;""" % (self.rnodes_table, self.rnodes_table,
                                 rnode, threshold)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def find_rnode(self, rnode):
        ''' Find nearest routing node
        '''
        query = """
SELECT id FROM
    (SELECT point AS search_point FROM %s WHERE id = '%d') AS rnode,
    %s
ORDER BY search_point <-> point
LIMIT 1;""" % (self.rnodes_table, rnode, self.rnodes_table)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def find_rnode_address(self, address):
        ''' Find nearest routing node to <address> using google geocoder
        '''
        return self.find_rnode_latlon(*self.find_latlon_address(address))

    def find_latlon_address(self, address):
        ''' Find latlon of <address> using google geocoder
        '''
        location = self.geocoder.geocode(address)
        return location.latitude, location.longitude

    def find_rnode_latlon(self, lat, lon):
        ''' Find nearest routing node to (<lat>, <lon>)
        '''
        query = """
SELECT id FROM %s
ORDER BY point <-> ST_SetSRID(ST_MakePoint(%f, %f), 4326)
LIMIT 1;""" % (self.rnodes_table, lon, lat)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def get_node_latlon(self, id):
        ''' Select node by ID
        - Return point as list(lat, lon)
        '''
        self.db_cur.execute("""
SELECT ST_AsGeoJSON(geom) FROM nodes_highways
WHERE id = '%s';""", (id,))
        return json.loads(
            self.db_cur.fetchone()[0])['coordinates'][::-1]

    def distance(self, n1, n2):
        ''' Return distance between two nodes in meters
        '''
        query = """
SELECT ST_Distance(point_1::geography, point_2::geography) FROM
    (SELECT point AS point_1 FROM %s WHERE id = '%d') AS rnode_1,
    (SELECT point AS point_2 FROM %s WHERE id = '%d') AS rnode_2;""" % (self.rnodes_table, n1,
                                                                        self.rnodes_table, n2)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def routing(self, node):
        ''' Return list of edges for <node>
        '''
        query = "SELECT edges FROM %s WHERE node = '%d'" % (self.routing_table, node)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def _get_rnodes_within_radius(self, origin, radius):
        query = """
SELECT id
    FROM
        rnodes,
        (SELECT point AS origin FROM rnodes WHERE id = '%d') AS origin_table
    WHERE ST_DWithin(origin::geography, point::geography, %f)""" % (origin, radius)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0]

    def get_edges_within_radius(self, origin, radius):
        rnodes = self._get_rnodes_within_radius(origin, radius)
        query = """
WITH near_nodes AS
    (SELECT id
        FROM
            rnodes,
            (SELECT point AS origin
                FROM rnodes
                WHERE id = '%d') as origin_table
        WHERE ST_Dwithin(origin::geography, point::geography, %f))
SELECT end1, end2, distance, run_score
    FROM routing_edges_indexed
    WHERE
        end1 IN (SELECT id FROM near_nodes) OR
        end2 IN (SELECT id FROM near_nodes);""" % (origin, radius)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()
