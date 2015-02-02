import json
from pyroutelib2.route import Router
from pyroutelib2.loadOsm import LoadOsm
import runhere_queries as rh
import folium
import geopy.geocoders
from credentials import cred

class RunRouter:
    ''' Find closed route using Stochastic Gradient Descent
    - For routing, relies on pyroutelib2 to traverse the
      street/path graph in the Open Streetmaps database
    '''

    def __init__(self):
        self.rh_db = rh.RunHereDB()
        self.data = LoadOsm('foot')
        # self.data.loadOsm('../osm/san-francisco_california.osm')
        self.router = Router(self.data)
        self.current_route = [[], [], []]
        self.nodes = [0, 0, 0]
        self.geocoder = geopy.geocoders.GoogleV3(**cred['google'])

    def do_route(self, address, distance, threshold=400):
        ''' Find a route
        - Threshold in meters for settling on a route
        - Return route as a Folium map
        '''
        self.initialize_search(address, distance)
        while self.get_cost(self.current_route) > threshold:
            self.step()
        print 'route found within threshold'
            
    def initialize_search(self, address, distance, threshold=1000):
        '''Initialize Search
        - Get control points
        - Compute first route
        - Store this route as minimum
        '''
        self.distance = distance
        self.nodes[0] = self.data.findNode(
            *self.latlon_from_address(address))
        # node_1 = self.rh_db.fetch_point_within_threshold(
        #     self.nodes[0], threshold)
        # self.nodes[1] = self.data.findNode(
        #     *self.rh_db.fetch_node_latlon(node_1))
        self.nodes[1] = self.data.findNode(
            *self.latlon_from_address('ferry building marketplace, san francisco'))
        # node_2 = self.rh_db.fetch_point_within_threshold(
        #     self.nodes[0], threshold)
        # self.nodes[2] = self.data.findNode(
        #     *self.rh_db.fetch_node_latlon(node_2))
        self.nodes[2] = self.data.findNode(
            *self.latlon_from_address('beale and market, san francisco'))
        self.current_route = self.get_route(self.nodes)
                
    def latlon_from_address(self, address):
        location = self.geocoder.geocode(address)
        latlon = [location.latitude, location.longitude]
        return latlon

    def step(self, threshold=1000):
        ''' Step control points stochastically within threshold
        - Update control points
        - Update route (ordered list of nodes)
        - Loop until found new route with reduced cost
        '''
        current_route = self.current_route
        current_cost = self.get_cost(current_route)
        new_cost = current_cost
        while new_cost >= current_cost:
            new_nodes = self.step_trial(self.nodes,
                                        threshold=threshold)
            new_route = self.get_route(new_nodes)
            new_cost = self.get_cost(new_route)
            print 'try step'
        print 'step'
        self.nodes = new_nodes
        self.current_route = new_route
            
    def step_trial(self, nodes_old, threshold=1000):
        nodes = [nodes_old[0], 0, 0]
        node_1 = self.rh_db.fetch_point_within_threshold(
            self.nodes[1], threshold)
        nodes[1] = self.data.findNode(
            *self.rh_db.fetch_node_latlon(node_1))
        node_2 = self.rh_db.fetch_point_within_threshold(
            self.nodes[2], threshold)
        nodes[2] = self.data.findNode(
            *self.rh_db.fetch_node_latlon(node_2))
        return nodes

    def get_route(self, nodes):
        ''' Get route using start point and control points
        '''
        route = [[], [], []]
        result, route[0] = self.router.doRoute(
            nodes[0],
            nodes[1])
        print result
        result, route[1] = self.router.doRoute(
            nodes[1],
            nodes[2])
        print result
        result, route[2] = self.router.doRoute(
            nodes[2],
            nodes[0])
        print result
        return route

    def get_cost(self, route):
        ''' Compute cost function for current state in SGD search
        - Cost = residual from target route length
        '''
        return abs(self.get_route_length(route) - self.distance)
        
    def get_route_length(self, route):
        ''' Get Route length
        '''
        current_dist = 0.
        for segment in route:
            current_dist += self.get_segment_length(segment)
        return current_dist

    def get_segment_length(self, segment):
        seg_dist = 0.
        for n in range(len(segment)-1):
            seg_dist += self.rh_db.get_dist(segment[n:n+2])[0][0]
        return seg_dist

    def get_centroid(self):
        return self.rh_db.get_centroid(
            [point for segment in self.current_route
             for point in segment])

    def update_folium_map(self):
        centroid = self.get_centroid()
        self.run_map = folium.Map(location=centroid, tiles='Stamen Toner',
                                  width=600, height=600, zoom_start=14)
        run_line = []
        self.add_mile_markers()
        for n in range(3):
            run_line += self.add_run_segment(
                self.current_route[n])
        self.run_map.line(locations=run_line,
                          line_color='blue', line_weight=6)

    def add_run_segment(self, segment):
        run_seg = []
        latlon_curr = self.rh_db.fetch_node_latlon(segment[0])
        run_seg.append(latlon_curr)
        for id in segment[1:]:
            latlon_curr = self.rh_db.fetch_node_latlon(id)
            run_seg.append(latlon_curr)
        return run_seg

    def add_mile_markers(self):
        ''' Put mile markers in node labels
        '''
        latlon = self.rh_db.fetch_node_latlon(
            self.current_route[0][0])
        self.run_map.circle_marker(location=latlon,
            radius=50, line_color='red',
            fill_color='blue', popup='start/finish',
            fill_opacity=1.)
        current_dist = 0.
        current_mile = 0
        for n in range(len(self.current_route)):
            for m in range(len(self.current_route[n])-1):
                current_dist += self.rh_db.get_dist(
                    self.current_route[n][m:m+2])[0][0] / 1600.
                if int(current_dist) > current_mile:
                    current_mile += 1
                    marker_label = ('%d' % current_mile)
                    latlon = self.rh_db.fetch_node_latlon(
                        self.current_route[n][m+1])
                    self.run_map.circle_marker(location=latlon,
                        radius=50, line_color='blue',
                        fill_color='blue',
                        popup=('mile %s' % marker_label),
                        fill_opacity=1.)

    def folium_add_segment(self, segment, color):
        run_line = []
        latlon_curr = self.rh_db.fetch_node_latlon(segment[0])
        # self.run_map.circle_marker(location=latlon_curr,
        #                            radius=10, line_color=color,
        #                            fill_color=color)
        run_line.append(latlon_curr)
        latlon_last = latlon_curr
        for id in segment[1:]:
            latlon_curr = self.rh_db.fetch_node_latlon(id)
            # self.run_map.circle_marker(location=latlon_curr,
            #                            radius=10, line_color=color,
            #                            fill_color=color)
            run_line.append(latlon_curr)
            # self.run_map.line(locations=[latlon_last, latlon_curr],
            #                   line_color=color, line_weight=7,
            #                   line_)
            latlon_last = latlon_curr
        self.run_map.line(locations=run_line,
                          line_color=color, line_weight=6)