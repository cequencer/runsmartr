from cycles_queries import CyclesDB
import networkx as nx

import pdb

class RunRouter:
    ''' Find closed route using Stochastic Gradient Descent
    - Rather than manipulating nodes, manipulate elements of the cycle basis
      for the accessible part of the foot-ways graph.
    '''
    def __init__(self, address, distance):
        self.data = CyclesDB(address, distance)
