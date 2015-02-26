from runrouter_data import RunRouterData

class RunRouter:

    def __init__(self, address, distance, eta0=1., alpha=1.):
        self.data = RunRouterData(address, distance)
        self.eta0 = eta0
        self.t = 0
        self.alpha = alpha

    def _initialize_search(self):
        G = self.data.foot_graph
        run_scores = [float(G.get_edge_data(u,v)['run_score']) for u,v in G.edges()]
        top_node = G.edges()[run_scores.index(max(run_scores))][0]
        self.nodes = [self.data.start_node, 0, 0]
        result = 'first_try'
        while result != 'success':
            self.nodes[1] = self.data.rand_rnode_within_n(
                top_node, 40)
            self.nodes[2] = self.data.rand_rnode_within_n(
                top_node, 40)
            result, self.current_route = self._get_route(self.nodes)
        self.current_cost = self._obj_fn(self.current_route)

    def _eta(self):
        return self.eta0 / (self.alpha * self.t)

    def _eval_grad(self):
        return

    def _step(self):
        

        new_cost = self.current_cost
        while new_cost >= self.current_cost:
            new_nodes = self._step_trial(self.nodes)
            result, new_route = self._get_route(new_nodes)
            if result == 'success':
                new_cost = self._obj_fn(new_route)
            print 'try %f --> %f' % (self.current_cost, new_cost)
        self.current_cost = new_cost
        self.nodes = new_nodes
        self.current_route = new_route

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
        while self.current_cost > 800.:
            self._step()
            print 'step - distance'
