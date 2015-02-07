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
