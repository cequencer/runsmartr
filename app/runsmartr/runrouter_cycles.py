from cycles_queries import CyclesDB

import pdb

class RunRouter:
    ''' Find optimal closed route using SGD
    '''
    def __init__(self, address, distance):
        self.data = CyclesDB(address, distance)

    def do_route(self, threshold=800.):
        ''' Find a route
        - Threshold in meters for settling on a route
        - Return route as a Folium map
        '''
        self.initialize_search()
        while self.current_cost > threshold:
            self.step()
        print 'route found within threshold'
            
    def initialize_search(self, threshold=400.):
        '''Initialize Search
        - Get control points
        - Compute first route
        - Store this route as minimum
        '''
        self.nodes = [[], [], []]
        self.nodes[0] = self.data.start_node
        result = 'failed'

        # (*) Choose initial nodes intelligently -- (1) Node adjacent to edge
        #     with highest score within range, (2) Node adjacent to edge with
        #     highest score within some threshold of one of the two points that
        #     could possibly complete a triangle with the other two points.
        #
        #     Add some randomness in case a path cannot be found

        while result != 'success':
            self.nodes[1] = self.data.rand_rnode_within_m(
                self.nodes[0], self.data.distance/2.)
            self.nodes[2] = self.data.rand_rnode_within_m(
                self.nodes[0], self.data.distance/2.)
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

    def step(self, threshold=800.):
        ''' Step control points stochastically within threshold
        - Update control points
        - Update route (ordered list of nodes)
        - Loop until found new route with reduced cost (approximate gradient)
        '''

        # (1) Start out in distance-finding mode; get within 0.5mi of correct
        #     distance without worrying about run_score.
        # (2) Once within distance threshold, never allow distance cost to
        #     exceed threshold again

        new_cost = self.current_cost
        count = 0
        while new_cost >= self.current_cost:
            count += 1
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
