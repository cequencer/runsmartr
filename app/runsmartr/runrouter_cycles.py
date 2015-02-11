from cycles_queries import CyclesDB

import pdb

class RunRouter:
    ''' Find closed route using Stochastic Gradient Descent
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
        while result != 'success':
            self.nodes[1] = self.data.rand_rnode_within_m(
                self.nodes[0], self.data.distance/2.)
            self.nodes[2] = self.data.rand_rnode_within_m(
                self.nodes[0], self.data.distance/2.)
            result, self.current_route = self.get_route(self.nodes)
                
    def get_route(self, nodes):
        ''' Get route using start point and control points
        '''
        route = []
        result, r = self.data.shortest_path(nodes[0], nodes[1])
        if result != 'success':
            return 'failed', []
        route += r
        result, r = self.data.shortest_path(nodes[1], nodes[2])
        if result != 'success':
            return 'failed', []
        route += r[1:]
        result, r = self.data.shortest_path(nodes[2], nodes[0])
        if result != 'success':
            return 'failed', []
        route += r[1:]
        return 'success', route

# ------------------------------------------------------------------------------
    def step(self, threshold=400.):
        ''' Step control points stochastically within threshold
        - Update control points
        - Update route (ordered list of nodes)
        - Loop until found new route with reduced cost (approximate gradient)
        '''
        new_cost = self.current_cost
        count = 0
        while new_cost >= self.current_cost:
            count += 1
            new_nodes = self.step_trial(self.nodes)
            result, new_route = self.get_route(new_nodes)
            if result == 'success':
                new_cost = self.get_cost(new_route)
            print 'try step, new cost = %f' % new_cost
            if count > 10:
                # self.current_route = self.old_route
                # return
                new_cost = 0  # Give up and output current route
        self.current_cost = new_cost
        print 'step'
        self.nodes = new_nodes
        self.old_route = self.current_route
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
        return abs(self.get_route_length(route) - self.distance)
        
    def get_route_length(self):
        ''' Get Route length
        '''
        route_length = 0.
        node0 = self.current_route[0]
        for node in self.current_route[1:]:
            route_length += self.data.foot_graph[node0][node]
            node0 = node
        return route_length

    def get_segment_length(self, segment):
        seg_dist = 0.
        for n in range(len(segment)-1):
            seg_dist += self.data.distance(segment[0],
                                           segment[1])
        return seg_dist

# ------------------------------------------------------------------------------
#     def get_centroid(self):
#         return self.rh_db.get_centroid(
#             [point for segment in self.current_route
#              for point in segment])

#     def get_route_points(self):
#         route_points = []
#         for seg in self.current_route:
#             route_points += self.add_route_segment(seg)
