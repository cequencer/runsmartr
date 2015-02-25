from cycles_queries import CyclesDB

class RunRouter:

    _eta0 = 1
    _alpha = 1

    def __init__(self, address, distance):
        self.data = CyclesDB(address, distance)
        self.eta = _eta0

    def _update_eta(self):
        # Evaluate learning rate (eta) for next time step

    def _eval_grad(self):
        # Evaluate gradient by picking one point near each of the
        # current controls, and moving the controls to those points
        # (vec := this move).
        # The approximate gradient is (delta cost)/|vec| along (vec) 

    def _step(self):
        # Evaluate approximate gradient, then take step
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
            
    def _initialize_search(self):
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

    def _get_route(self, nodes):
        graph_remaining = self.data.foot_graph.copy()
        route = [nodes[0]]
        for n0, n1 in [[0, 1], [1, 2], [2, 0]]:
            result, r = self.data.shortest_path(
                nodes[n0], nodes[n1], graph_remaining)
            if result != 'success':
                return 'failed', []
            if n1 != 0:
                graph_remaining.remove_nodes_from(r[1:-1]);
            route += r[1:]
        return 'success', route
            
    def _step_trial(self, nodes_old, threshold=400.):
        nodes = [nodes_old[0], 0, 0]
        nodes[1] = self.data.rand_rnode_within_m(
            self.nodes[1], threshold)
        nodes[2] = self.data.rand_rnode_within_m(
            self.nodes[2], threshold)
        return nodes

    def _get_cost(self, route):
        return abs(self.get_route_length(route) - self.data.distance)
        
    def _get_route_length(self, route):
        route_length = 0.
        try:
            node0 = route[0]
        except IndexError:
            return 0.
        for node in route[1:]:
            route_length += float(self.data.foot_graph[node0][node]['dist'])
            node0 = node
        return route_length

    def find_route(self):
        self._initialize_search()
        # Take steps following prescribed learning schedule
        while self.current_cost > threshold:
            self._step()
            print 'step - distance'
