from cycles_queries import CyclesDB

import pdb

class RunRouter:
    ''' Find optimal closed route using SGD
    '''
    def __init__(self, address, distance):
        self.data = CyclesDB(address, distance)

    def do_route(self, threshold=800.):

        # (1) Start out in distance-finding mode; get within 0.5mi of correct
        #     distance without worrying about run_score.
        # (2) Once within distance threshold, never allow distance cost to
        #     exceed threshold again

        self.initialize_search()
        while self.current_cost > threshold:
            self.step_distance()
            print 'step - distance'
        # while :
        #     self.step_score()
        #     print 'step - score'
            
    def initialize_search(self):
        '''Initialize Search
        - Get control points
        - Compute first route
        - Store this route as minimum
        '''
        G = self.data.foot_graph
        run_scores = [float(G.get_edge_data(u,v)['run_score']) for u,v in G.edges()]
        top_node = G.edges()[run_scores.index(max(run_scores))][0]
        self.nodes = [[], [], []]
        self.nodes[0] = self.data.start_node
        result = 'failed'
        while result != 'success':
            threshold = self.data.distance/2. - self.data.straight_line_dist(
                self.data.start_node, top_node)
            self.nodes[1] = self.data.rand_rnode_within_m(
                top_node, self.data.distance/500.)
            self.nodes[2] = self.data.rand_rnode_within_m(
                top_node, self.data.distance/2.)
            result, self.current_route = self.get_route(self.nodes)
        self.current_cost = self.get_cost(self.current_route)
                
    def get_route(self, nodes):
        ''' Get route using start point and control points
        '''
        graph_remaining = self.data.foot_graph.copy()
        route = []
        result, r = self.data.shortest_path(
            nodes[0], nodes[1], graph_remaining)
        if result != 'success':
            return 'failed', []
        graph_remaining.remove_nodes_from(r[1:-1]);
        route += r
        result, r = self.data.shortest_path(
            nodes[1], nodes[2], graph_remaining)
        if result != 'success':
            return 'failed', []
        graph_remaining.remove_nodes_from(r[1:-1]);
        route += r[1:]
        result, r = self.data.shortest_path(
            nodes[2], nodes[0], graph_remaining)
        if result != 'success':
            return 'failed', []
        route += r[1:]
        return 'success', route

    def step_distance(self):
        new_cost = self.current_cost
        while new_cost >= self.current_cost:
            print 'try - dist'
            new_nodes = self.step_trial(self.nodes,
                                        threshold=self.current_cost)
            result, new_route = self.get_route(new_nodes)
            if result == 'success':
                new_cost = self.get_cost(new_route)
        self.current_cost = new_cost
        self.nodes = new_nodes
        self.current_route = new_route
            
    def step_score(self, alpha, threshold):
        trailing_variance = 999999
        while trailing_variance > threshold:
            print 'try - score'
            new_nodes = self.step_trial(self.nodes,
                                        threshold=self.current_cost)
            result, new_route = self.get_route(new_nodes)
            if result == 'success':
                new_cost = self.get_cost(new_route)
        self.current_cost = new_cost
        self.nodes = new_nodes
        self.current_route = new_route
            
    def step_trial(self, nodes_old, threshold=400.):
        nodes = [nodes_old[0], 0, 0]
        nodes[1] = self.data.rand_rnode_within_m(
            self.nodes[1], threshold)
        nodes[2] = self.data.rand_rnode_within_m(
            self.nodes[2], threshold)
        return nodes

    def get_cost(self, route):
        ''' Compute cost function for current state in SGD search
        - Cost = residual from target route length
        '''
        return abs(self.get_route_length(route) - self.data.distance)
        
    def get_route_length(self, route):
        ''' Get Route length
        '''
        route_length = 0.
        try:
            node0 = route[0]
        except IndexError:
            return 0.  # Bit of a hack, but this will force a new step in case
                       # a bad route somehow gets to this point
        for node in route[1:]:
            route_length += float(self.data.foot_graph[node0][node]['dist'])
            node0 = node
        return route_length
