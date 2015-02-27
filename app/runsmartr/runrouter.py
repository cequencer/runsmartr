from runrouter_data import RunRouterData

import pdb

class RunRouter:

    def __init__(self, address, distance, eta0=2e-9):
        self.data = RunRouterData(address, distance)
        self.eta0 = eta0
        self.t = 1

    def _initialize_search(self):
        G = self.data.foot_graph
        run_scores = [float(G.get_edge_data(u,v)['run_score']) for u,v in G.edges()]
        top_node = G.edges()[run_scores.index(max(run_scores))][0]
        self.nodes = [self.data.start_node, 0, 0]
        result = ''
        while result != 'success':
            self.nodes[1] = self.data.rand_rnode_within_n(
                top_node, 40)
            self.nodes[2] = self.data.rand_rnode_within_n(
                top_node, 40)
            result, self.current_route = self._get_route(self.nodes)
        self.current_obj_fn = self._obj_fn(self.current_route)

    def _eta(self):
        self.t += 0
        return self.eta0 / self.t

    def _eval_grad(self):
        result = ''
        while result != 'success':
            nodes_test = [self.data.rand_rnode_within_n(node, 8)
                          for node in self.nodes[1:]]
            result, route_test = self._get_route([self.nodes[0]] + nodes_test)
        x_route = (self.data.rnode_latlon(self.nodes[1]) +
                   self.data.rnode_latlon(self.nodes[2]))
        x_test = (self.data.rnode_latlon(nodes_test[0]) +
                  self.data.rnode_latlon(nodes_test[1]))
        d_obj_fn = self._obj_fn(route_test) - self.current_obj_fn
        x_new = [x[0] - self._eta() * d_obj_fn / (x[1] - x[0])
                for x in zip(x_route, x_test)]
        nodes_new = [self.nodes[0]]
        nodes_new.append(self.data.nearest_accessible_rnode(*x_new[0:2]))
        nodes_new.append(self.data.nearest_accessible_rnode(*x_new[2:4]))
        return nodes_new

    def _step(self):
        result = ''
        while result != 'success':
            nodes_step = self._eval_grad()
            result, route_step = self._get_route(nodes_step)
        self.nodes = nodes_step
        self.current_route = route_step
        self.current_obj_fn = self._obj_fn(route_step)

    def _get_route(self, nodes):
        graph_remaining = self.data.foot_graph.copy()
        route = [nodes[0]]
        for n in [[0, 1], [1, 2], [2, 0]]:
            result, r = self.data.shortest_path(
                nodes[n[0]], nodes[n[1]], graph_remaining)
            if result != 'success':
                return 'failed', []
            route += r[1:]
            if n[1] != 0:
                graph_remaining.remove_nodes_from(r[1:-1]);
        return 'success', route

    def _obj_fn(self, route):
        return abs(self.get_route_length(route) - self.data.distance)

    def get_route_length(self, route):
        route_length = 0.
        node0 = route[0]
        for node in route[1:]:
            route_length += float(self.data.foot_graph[node0][node]['dist'])
            node0 = node
        return route_length

    def find_route(self):
        self._initialize_search()
        print self.current_obj_fn
        for n in range(10):
            self._step()
            print self.current_obj_fn
