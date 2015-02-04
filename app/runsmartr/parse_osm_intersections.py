from runhere_queries import RunHereDB

def parse_osm_intersections_only():
    ''' Same as below, but consider only nodes at intersections
    - WARNING: RELIES ON RESULTS OF parse_osm() ALREADY BEING IN TABLE
    - Identify nodes with > 2 edges (i.e. intersections)
    - Add edges connecting these intersection nodes to other intersection nodes
    '''
    rh_db = RunHereDB()
    foot_ways = ('primary','secondary','tertiary','unclassified','minor',
                 'cycleway','residential', 'track','service','footway','steps')
    ways = get_foot_ways(rh_db, foot_ways)
    count = 1
    nways = len(ways)
    for way in ways:
        way_nodes = get_nodes_intersections(rh_db, way)
        for n in range(len(way_nodes)-1):
            routing0 = get_node_routing_int(rh_db, way_nodes[n])
            if routing0 == []:
                add_routing_entry_int(rh_db, way_nodes[n], way_nodes[n+1])
            elif way_nodes[n+1] not in routing0[0][0]:
                add_routing_edge_int(rh_db, way_nodes[n], way_nodes[n+1])
            routing1 = get_node_routing_int(rh_db, way_nodes[n+1])
            if routing1 == []:
                add_routing_entry_int(rh_db, way_nodes[n+1], way_nodes[n])
            elif way_nodes[n] not in routing1[0][0]:
                add_routing_edge_int(rh_db, way_nodes[n+1], way_nodes[n])
        print 'Done with way %d of %d.' % (count, nways)
        count += 1

def add_routing_entry_int(rh_db, node, edge):
    query = """
INSERT INTO rnodes_intersections (id, point)
    SELECT nodes.id as id, geom AS point FROM nodes WHERE nodes.id = '%d';""" % node
    rh_db.db_cur.execute(query)
    rh_db.db_conn.commit()
    query = """
INSERT INTO routing_intersections (node, edges) VALUES ('%d', '{%d}')""" % (node, edge)
    rh_db.db_cur.execute(query)
    rh_db.db_conn.commit()

def add_routing_edge_int(rh_db, node, edge):
    query = """
UPDATE routing_intersections SET edges = edges || '{%d}'
WHERE node = '%d';""" % (edge, node)
    rh_db.db_cur.execute(query)
    rh_db.db_conn.commit()

def get_node_routing_int(rh_db, node):
    return rh_db.query_raw(
        "SELECT edges FROM routing_intersections WHERE node = '%d';" % node)

def get_nodes_intersections(rh_db, way):
    nodes = rh_db.query_raw("""
SELECT way_nodes FROM
    routing,
    (SELECT unnest(nodes) AS way_nodes FROM ways WHERE id = %d) AS way_nodes_table
WHERE node = way_nodes AND array_length(edges, 1) > 2;""" % (way,))
    return [int(n) for node in nodes for n in node]

def get_foot_ways(rh_db, foot_way_types):
    query = """
SELECT ways.id from ways, neighborhoods
WHERE ST_Intersects(linestring, polygon)
    AND tags->'highway' IN (%s);""" % (', '.join("'"+type+"'"
        for type in foot_way_types))
    foot_ways = [int(way[0]) for way in rh_db.query_raw(query)]
    return foot_ways

if __name__ == '__main__':
    parse_osm_intersections_only()
