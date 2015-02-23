from credentials import cred
from random import random as rnd
import networkx as nx
import psycopg2
import geopy.geocoders
import json

import pdb

class CyclesDB:

    def __init__(self, address, distance):
        self._db_conn = psycopg2.connect(**cred['db'])
        self._cur = self._db_conn.cursor()
        self._geocoder = geopy.geocoders.GoogleV3(**cred['google'])
        start = self._geocoder.geocode(address)
        self.start = (start.latitude, start.longitude)
        self.distance = distance
        self.start_node = self._get_start_node()
        self.foot_graph = self._get_foot_graph()

    def _get_start_node(self):
        query = ("""
            SELECT id
                FROM rnodes_intersections
                ORDER BY point <-> ST_SetSRID(ST_MakePoint(%f, %f), 4326)
                LIMIT 1;""" % self.start[::-1])
        self._cur.execute(query)
        return int(self._cur.fetchall()[0][0])

    def _get_foot_graph(self):
        radius = self.distance/2.
        G = nx.Graph()
        query = ("""
            WITH origin AS
                (SELECT point
                    FROM rnodes_intersections
                    WHERE id = '%d')
            SELECT end1, end2, distance, run_score
                FROM routing_edges_latlon, origin
                WHERE
                    ST_Dwithin(origin.point::geography, point1::geography, %f) OR
                    ST_Dwithin(origin.point::geography, point2::geography, %f);"""
                 % (self.start_node, radius, radius))
        self._cur.execute(query)
        G.add_edges_from([[int(node[0]), int(node[1]), {'dist': node[2], 'run_score': node[3]}]
                          for node in self._cur.fetchall()])
        G_cycles = nx.Graph()
        for cycle in nx.cycle_basis(G):
            G_cycles.add_cycle(cycle)
        for edge in G.edges():
            if not G_cycles.has_edge(*edge):
                G.remove_edge(*edge)
        return G

    def _detailed_nodes_for_edge(self, node1, node2):
        query = ("""
            SELECT edge_nodes
                FROM routing_edges_latlon
                WHERE
                    (end1 = '%d' AND end2 = '%d') OR
                    (end2 = '%d' AND end1 = '%d');"""
                 % (node1, node2, node1, node2))
        self._cur.execute(query)
        nodes = [int(node) for node in self._cur.fetchone()[0]]
        if nodes[0] == node1:
            return nodes
        else:
            return nodes[::-1]

    def _node_latlon(self, node):
        query = """
            SELECT ST_AsGeoJSON(point)
                FROM rnodes
                WHERE id = '%d'""" % node
        self._cur.execute(query)
        return json.loads(self._cur.fetchone()[0])['coordinates'][::-1]

    def _nodes_distance(self, node0, node1):
        query = ("""
            SELECT ST_Distance(point0::geography, point1::geography)
                FROM
                    (SELECT point AS point0 FROM rnodes WHERE id = '%d') AS rnode0,
                    (SELECT point AS point1 FROM rnodes WHERE id = '%d') AS rnode1;"""
                 % (node0, node1))
        self._cur.execute(query)
        return self._cur.fetchone()[0]

    def shortest_path(self, node1, node2, G):
        try:
            path = nx.shortest_path(G, source=node1, target=node2, weight='dist')
        except nx.NetworkXNoPath:
            return 'failed', []
        return 'success', path

    def straight_line_dist(self, node1, node2):
        query = ("""
            SELECT ST_Distance(point_1::geography, point_2::geography)
                FROM
                    (SELECT point AS point_1
                        FROM rnodes WHERE id = '%d') AS rnode_1,
                    (SELECT point AS point_2
                        FROM rnodes WHERE id = '%d') AS rnode_2;"""
                 % (node1, node2))
        self._cur.execute(query)
        return self._cur.fetchone()[0]

    def rand_rnode_within_m(self, rnode, m):
        query = ("""
            SELECT id FROM
                (SELECT ST_Translate(point, %f, %f) AS search_point
                 FROM rnodes_intersections WHERE id = '%d') AS rnode,
                rnodes_intersections
            ORDER BY search_point <-> point LIMIT 1;"""
                 % (m*(rnd()-0.5) / 89012., m*(rnd()-0.5) / 110978., rnode))
        self._cur.execute(query)
        return self._cur.fetchall()[0][0]

    def detailed_path_latlon_milemarkers(self, nodes):
        distance = 0.
        current_milemarker = 0.
        detailed_nodes_list = []
        node0 = nodes[0]
        for node in nodes[1:]:
            detailed_nodes_list += self._detailed_nodes_for_edge(node0, node)
            node0 = node
        node0 = detailed_nodes_list[0]
        detailed_nodes_latlon = [self._node_latlon(detailed_nodes_list[0])]
        milemarkers_latlon = []
        for node in detailed_nodes_list[1:]:
            detailed_nodes_latlon.append(self._node_latlon(node))
            delta = self._nodes_distance(node0, node)
            distance += delta
            if distance >= current_milemarker:
                lat0, lon0 = detailed_nodes_latlon[-2]
                lat1, lon1 = detailed_nodes_latlon[-1]
                overshoot = distance - current_milemarker
                lat_milemarker = lat1 - (lat1-lat0) * overshoot/distance
                lon_milemarker = lon1 - (lon1-lon0) * overshoot/distance
                milemarkers_latlon.append([lat_milemarker, lon_milemarker])
                current_milemarker += 1608.
                print '%f --> %f' % (current_milemarker, distance)
            node0 = node
        lat_list, lon_list = zip(*detailed_nodes_latlon)
        lat0, lon0 = min(lat_list), min(lon_list)
        lat1, lon1 = max(lat_list), max(lon_list)
        return detailed_nodes_latlon, lat0, lon0, lat1, lon1, milemarkers_latlon

    def detailed_path_latlon(self, nodes):
        detailed_nodes_list = []
        node0 = nodes[0]
        for node in nodes[1:]:
            detailed_nodes_list += self._detailed_nodes_for_edge(node0, node)
            node0 = node
        detailed_nodes_latlon = [self._node_latlon(node)
                                 for node in detailed_nodes_list]
        lat_list, lon_list = zip(*detailed_nodes_latlon)
        lat0, lon0 = min(lat_list), min(lon_list)
        lat1, lon1 = max(lat_list), max(lon_list)
        return detailed_nodes_latlon, lat0, lon0, lat1, lon1

    def foot_graph_latlon(self):
        radius = self.distance/2.
        query = ("""
           WITH origin AS
               (SELECT point
                   FROM rnodes_intersections
                   WHERE id = '%d')
           SELECT
                   ST_AsGeoJSON(point1), ST_AsGeoJSON(point2),
                   distance, run_score,
                   end1, end2
               FROM routing_edges_latlon, origin
               WHERE
                   ST_Dwithin(origin.point::geography, point1::geography, %f) OR
                   ST_Dwithin(origin.point::geography, point2::geography, %f);"""
                 % (self.start_node, radius, radius))
        self._cur.execute(query)
        edges = []
        for edge in self._cur.fetchall():
            if self.foot_graph.has_edge(edge[4], edge[5]):
                edges.append(
                    {'edge': str([json.loads(edge[0])['coordinates'][::-1],
                                  json.loads(edge[1])['coordinates'][::-1]]),
                     'distance': float(edge[2]),
                     'run_score': float(edge[3])}
                )
        return edges
