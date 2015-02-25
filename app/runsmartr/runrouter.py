from runrouter_data import RunRouterData

class RunRouter:

    def __init__(self, address, distance, eta0=1., alpha=1.):
        self.data = RunRouterData(address, distance)
        self.eta0 = eta0
        self.t = 0
        self.alpha = alpha

    def _eta(self):
        return self.eta0 / (self.alpha * self.t)

    def _eval_grad(self):
        # Evaluate gradient by picking one point near each of the
        # current controls, and moving the controls to those points
        # (vec := this move).
        # The approximate gradient is (delta cost)/|vec| along (vec) 
        return

    def _step(self):
        # Evaluate approximate gradient, then take step
        new_cost = self.current_cost
        while new_cost >= self.current_cost:
            print 'try - dist'
            new_nodes = self._step_trial(self.nodes)
            result, new_route = self._get_route(new_nodes)
            if result == 'success':
                new_cost = self._obj_fn(new_route)
        self.current_cost = new_cost
        self.nodes = new_nodes
        self.current_route = new_route

    def _initialize_search(self):
        # Currently finds random node near top-scored edge.  This is
        # slow and probably not the best starting point ...
        G = self.data.foot_graph
        run_scores = [float(G.get_edge_data(u,v)['run_score']) for u,v in G.edges()]
        top_node = G.edges()[run_scores.index(max(run_scores))][0]
        self.nodes = [self.data.start_node, 0, 0]
        result = 'failed'
        while result != 'success':
            self.nodes[1] = self.data.rand_rnode_within_n(
                top_node, 40)
            self.nodes[2] = self.data.rand_rnode_within_n(
                top_node, 40)
            result, self.current_route = self._get_route(self.nodes)
        self.current_cost = self._obj_fn(self.current_route)

    # Is it much faster to just find the shortest path length than to
    # find all the nodes in the path?  Probably not ... anyway, need
    # to find the whole path in order to eliminate these nodes from
    # graph.

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

    def _step_trial(self, nodes_old):
        nodes = [nodes_old[0], 0, 0]
        nodes[1] = self.data.rand_rnode_within_n(
            self.nodes[1], 100)
        nodes[2] = self.data.rand_rnode_within_n(
            self.nodes[2], 100)
        return nodes

    def _obj_fn(self, route):
        return abs(self.get_route_length(route) - self.data.distance)

    def get_route_length(self, route):
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
        while self.current_cost > 800.:
            self._step()
            print 'step - distance'
