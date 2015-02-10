from credentials import cred
import networkx as nx
import psycopg2
import geopy.geocoders

class CyclesDB:

    def __init__(self, address, distance):
        self._db_conn = psycopg2.connect(**cred['db'])
        self._cur = self._db_conn.cursor()
        self._geocoder = geopy.geocoders.GoogleV3(**cred['google'])
        self.start = self._geocoder.geocode(address)
        self.distance = distance
        self.start_node = self._get_start_node()
        self.foot_graph = self._get_foot_graph()

    def _get_start_node(self):
        query = ("""
            SELECT id
                FROM rnodes
                ORDER BY point <-> ST_SetSRID(ST_MakePoint(%f, %f), 4326)
                LIMIT 1;""" % (self.start.longitude,
                               self.start.latitude))
        self._cur.execute(query)
        return self._cur.fetchall()[0][0]

    def _get_foot_graph(self):
        radius = self.distance/2.
        query = ("""
            WITH origin AS
                (SELECT point
                    FROM rnodes
                    WHERE id = '%d')
            SELECT end1, end2, distance, run_score
                FROM routing_edges_indexed, origin
                WHERE
                    ST_Dwithin(origin.point::geography,point1::geography, %f) OR
                    ST_Dwithin(origin.point::geography, point2::geography, %f);"""
                 % (self.start_node, radius, radius))
        self._cur.execute(query)
        return 

    def foot_graph_latlon(self):
        radius = self.distance/2.
        query = ("""
           WITH origin AS
               (SELECT point
                   FROM rnodes
                   WHERE id = '%d')
           SELECT ST_AsGeoJSON(point1), ST_AsGeoJSON(point2), distance, run_score
               FROM routing_edges_indexed, origin
               WHERE
                   ST_Dwithin(origin.point::geography,point1::geography, %f) OR
                   ST_Dwithin(origin.point::geography, point2::geography, %f);"""
                 % (self.start_node, radius, radius))
        self._cur.execute(query)
        edges = self._cur.fetchall()
        return [{'edge': str([json.loads(edge[0])['coordinates'][::-1],
                              json.loads(edge[1])['coordinates'][::-1]]),
                 'distance': float(edge[2]),
                 'run_score': float(edge[3])}
                for edge in self._cur.fetchall()]
