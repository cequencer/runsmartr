from runhere_queries import RunHereDB

class routingReduce():

    def __init__(self):
        self.db = RunHereDB()

    def _get_edges(self, node):
        query = """
SELECT edges FROM routing WHERE node = '%s';""" % node;
        return [int(node) for node in self.db.query_raw(query)[0][0]]

    def _get_rnodes_not2(self):
        '''Get list of all rnodes except for those connected to exactly
        two edges.
        '''
        query = """
SELECT node
    FROM routing
    WHERE
        array_length(edges, 1) >= 3 OR
        array_length(edges, 1) = 1;"""
        return [int(node[0]) for node in self.db.query_raw(query)]

    def _edge_strings(self, node, edge, nodes_along_edge):
        edge_string = '%d, %d' % (node, edge)
        edge_nodes_string = ', '.join(('%d' % n)
                                      for n in nodes_along_edge)
        return edge_string, edge_nodes_string

    def _row_exists(self, node, edge, nodes_along_edge):
        edge_string, edge_nodes_string = self._edge_strings(
            node, edge, nodes_along_edge)
        query = """
SELECT edge
    FROM routing_edges
    WHERE
        edge = '{%s}' AND
        edge_nodes = '{%s}';""" % (edge_string, edge_nodes_string)
        exists_forward = self.db.query_raw(query) != []
        edge_string, edge_nodes_string = self._edge_strings(
            edge, node, nodes_along_edge[::-1])
        query = """
SELECT edge
    FROM routing_edges
    WHERE
        edge = '{%s}' AND
        edge_nodes = '{%s}';""" % (edge_string, edge_nodes_string)
        exists_backward = self.db.query_raw(query) != []
        return exists_backward or exists_forward

    def _get_run_score(self, nodes):
        run_score = 0
        for node in nodes:
            query = """
SELECT COUNT(*)
    FROM mmf_routes_nodes
    WHERE nodes @> ARRAY[%d::bigint];""" % node
            run_score += self.db.query_raw(query)[0][0]
        return float(run_score)/len(nodes)

    def _get_distance(self, nodes):
        distance = 0.
        n0 = nodes[0]
        for n1 in nodes[1:]:
            query = """
SELECT ST_Distance(point_1::geography, point_2::geography)
    FROM
        (SELECT point AS point_1
             FROM rnodes WHERE id = '%d') AS rnode_1,
        (SELECT point AS point_2
             FROM rnodes WHERE id = '%d') AS rnode_2;""" % (n0, n1)
            self.db.db_cur.execute(query)
            distance += self.db.db_cur.fetchall()[0][0]
            n0 = n1
        return distance

    def _record_row(self, node, edge, nodes_along_edge):
        distance = self._get_distance(nodes_along_edge)
        run_score = self._get_run_score(nodes_along_edge)
        edge_string, edge_nodes_string = self._edge_strings(
            node, edge, nodes_along_edge)
        query = """
INSERT INTO routing_edges (edge, edge_nodes, distance, run_score)
    VALUES ('{%s}', '{%s}', '%f', '%f');""" % (edge_string, edge_nodes_string,
                                               distance, run_score)
        self.db.db_cur.execute(query)
        self.db.db_conn.commit()

    def _record_row_if_new(self, node, edge, nodes_along_edge):
        if not self._row_exists(node, edge, nodes_along_edge):
            self._record_row(node, edge, nodes_along_edge)
            print 'Added edge {%d, %d} to table' % (node, edge)
        else:
            print '{%d, %d} already recorded in table' % (node, edge)

    def populate_edge_table(self):
        ''' Reduce foot-ways routing graph to get rid of all nodes with
        only two connections (i.e., not endpoints of ways and not
        intersections).  Store all edges as a two-element tuple (which is
        what I need for importing into NetworkX.
        - Uses <rnodes> and <routing> tables output by parse_osm.py
        - Second column:  List of all intermediate nodes for this edge
        - Third column:  Total distance for this edge (calculated using
          all intermediate points)
        - Additional columns can be added for other edge features!
        '''
        self.db = RunHereDB()
        rnodes = self._get_rnodes_not2()
        for node in rnodes:
            edges = self._get_edges(node)
            for edge in edges:
                found_intersection = False
                current_node = edge
                nodes_along_edge = [node]
                while not found_intersection:
                    nodes_along_edge.append(current_node)
                    if current_node in rnodes:
                        found_intersection = True
                    else:
                        next_edges = self._get_edges(current_node)
                        n = 0
                        while next_edges[n] == nodes_along_edge[-2]: n += 1
                        current_node = next_edges[n]
                self._record_row_if_new(node, current_node, nodes_along_edge)

if __name__ == '__main__':
    rr = routingReduce()
    rr.populate_edge_table()
