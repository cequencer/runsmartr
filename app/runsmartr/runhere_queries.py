from credentials import cred
import psycopg2
import json

class RunHereDB:

    def __init__(self):
        self.db_conn = psycopg2.connect(**cred['db'])
        self.db_cur = self.db_conn.cursor()

    def query_raw(self, query):
        '''Pass your own query, get raw response.
        '''
        self.db_cur.execute(query)
        return self.db_cur.fetchall()

    def highways_buffered(self):
        '''Get buffered highways.
        '''
        self.db_cur.execute("""
SELECT ST_AsGeoJSON(the_geom) FROM highways_buffered;""")
        return self.db_cur.fetchone()[0]

    def fetch_valid_runs(self, table_name):
        query = """
SELECT mmf_id FROM %s, highways_buffered
WHERE ST_Within(linestring, the_geom);""" % (table_name,)
        self.db_cur.execute(query)
        return self.db_cur.fetchall()

    def fetch_valid_run(self, offset):
        '''Get one valid run from the database.
        Return:  (centroid GeoJSON, linestring GeoJSON)
        '''
        self.db_cur.execute("""
SELECT ST_AsGeoJSON(ST_Centroid(linestring)), ST_AsGeoJSON(linestring)
FROM routes_potrero_hill, highways_buffered
WHERE ST_Within(linestring, the_geom)
LIMIT 1 OFFSET %s;""", (offset,))
        run = self.db_cur.fetchall()[0]
        return json.loads(run[0])['coordinates'][::-1], run[1]

    def fetch_node(self, id):
        ''' Select node by ID
        - Return point as GeoJSON string
        '''
        self.db_cur.execute("""
SELECT ST_AsGeoJSON(geom) FROM nodes_highways
WHERE id = '%s';""", (id,))
        return self.db_cur.fetchone()[0]

    def fetch_node_latlon(self, id):
        ''' Select node by ID
        - Return point as list(lat, lon)
        '''
        self.db_cur.execute("""
SELECT ST_AsGeoJSON(geom) FROM nodes_highways
WHERE id = '%s';""", (id,))
        return json.loads(
            self.db_cur.fetchone()[0])['coordinates'][::-1]

    def fetch_point_within_threshold(self, point, threshold):
        ''' Random point within threshold of <point>
        - Point given by Open Streetmaps ID
        - Chooses randomly from list of <threshold> nearest nodes to
          <point>
        '''
        self.db_cur.execute("""
SELECT id FROM
    (SELECT id FROM
        nodes_highways,
        (SELECT geom AS origin FROM nodes_highways WHERE id = '%s')
            AS nodes_origin
    ORDER BY ST_Distance(origin::geography, geom::geography)
    LIMIT %s) AS knn
ORDER BY RANDOM() LIMIT 1;""", (point, threshold))
        return self.db_cur.fetchall()[0][0]

    def fetch_nearest_highway_node(self, lon, lat):
        self.db_cur.execute("""
SELECT id FROM
    nodes_highways
ORDER BY geom <-> 'SRID=4326;POINT(%s %s)'::geometry
LIMIT 1;""", (lon, lat))
        return self.db_cur.fetchall()[0][0]

    def get_centroid(self, route):
        route_str = ', '.join("'"+str(el)+"'" for el in route)
        query = """
SELECT ST_AsGeoJSON(ST_Centroid(ST_MakeLine(geom)))
FROM nodes WHERE id IN (%s);""" % route_str
        self.db_cur.execute(query)
        route_centroid = json.loads(
            self.db_cur.fetchall()[0][0])['coordinates'][::-1]
        return route_centroid

    def get_dist(self, points):
        ''' Return distance between two points in meters
        - points is a tuple (node_1_id, node_2_id)
        '''
        self.db_cur.execute("""
SELECT ST_Distance(point_1, point_2) FROM
    (SELECT geom::geography AS point_1 FROM nodes WHERE id = '%s') AS g_1,
    (SELECT geom::geography AS point_2 FROM nodes WHERE id = '%s') AS g_2;""",
        (points[0], points[1]))
        return self.db_cur.fetchall()

    def already_done(mmf_id):
        ''' Check if the route has already been tallied.
        '''
        query = "SELECT * FROM mmf_routes_nodes WHERE mmf_id = %d" % mmf_id
        self.db_cur.execute(query)
        return self.db_cur.fetchall() != []

    def update_stats_mmf_score(self, nearest_nodes, mmf_id):
        nearest_nodes_string = ', '.join("'"+('%d' % id)+"'"
            for id in nearest_nodes)
        query = """
UPDATE nodes_highways_mmf_routes SET route_count = route_count + 1
WHERE id IN (%s);""" % nearest_nodes_string
        self.db_cur.execute(query)
        self.db_conn.commit()
        query = """
UPDATE nodes_highways_mmf_routes SET routes = routes || '{%d}'
WHERE id IN (%s);""" % (mmf_id, nearest_nodes_string)
        self.db_cur.execute(query)
        self.db_conn.commit()

    def update_stats_route_nodes(self, mmf_id, nearest_nodes):
        nearest_nodes_string = '{' + ', '.join(('%d' % id)
            for id in nearest_nodes) + '}'
        query = """
INSERT INTO mmf_routes_nodes
VALUES (%d, %s);""" % (mmf_id, nearest_nodes_string)
        self.db_cur.execute(query)
        self.db_conn.commit()
