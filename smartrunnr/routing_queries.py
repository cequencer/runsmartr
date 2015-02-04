from credentials import cred
import psycopg2
import json
import geopy.geocoders

class RoutingDB:

    def __init__(self):
        self.db_conn = psycopg2.connect(**cred['db'])
        self.db_cur = self.db_conn.cursor()
        self.geocoder = geopy.geocoders.GoogleV3(**cred['google'])

    def find_rnode(self, rnode):
        ''' Find nearest routing node
        '''
        query = """
SELECT id FROM
    (SELECT point AS search_point FROM rnodes WHERE id = '%d') AS rnode,
    rnodes
ORDER BY search_point <-> point LIMIT 1;"""
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def find_rnode_address(self, address):
        ''' Find nearest routing node to <address> using google geocoder
        '''
        location = self.geocoder.geocode(address)
        return self.find_rnode_latlon(
            location.latitude, location.longitude)

    def find_rnode_latlon(self, lat, lon):
        ''' Find nearest routing node to (<lat>, <lon>)
        '''
        query = """
SELECT id FROM rnodes
ORDER BY point <-> ST_SetSRID(ST_MakePoint(%f, %f), 4326) LIMIT 1;""" % (lon, lat)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def distance(self, n1, n2):
        ''' Return distance between two nodes in meters
        '''
        query = """
SELECT ST_Distance(point_1::geography, point_2::geography) FROM
    (SELECT point AS point_1 FROM rnodes WHERE id = '%d') AS rnode_1,
    (SELECT point AS point_2 FROM rnodes WHERE id = '%d') AS rnode_2;""" % (n1, n2)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()[0][0]

    def routing(self, node):
        ''' Return list of edges for <node>
        '''
