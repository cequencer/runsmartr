#!/usr/bin/python
#----------------------------------------------------------------
# Routing for OSM data
#
#------------------------------------------------------
# Usage as library:
#   datastore = loadOsm('transport type')
#   router = Router(datastore)
#   result, route = router.doRoute(node1, node2)
#
# (where transport is cycle, foot, car, etc...)
#------------------------------------------------------
# Copyright 2007-2008, Oliver White
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#------------------------------------------------------
import sys
import math 
from routing_queries import RoutingDB

import pdb

class Router:

  def __init__(self, intersections_only=True):
    self.closed = []
    self.data = RoutingDB(intersections_only=intersections_only)

  def distance(self,n1,n2):
    """Calculate distance between two nodes"""
    return self.data.distance(n1, n2)
  
  def doRoute(self,start,end,keep_closed=False):
    """Do the routing"""
    self.searchEnd = end
    if keep_closed:
      self.closed.append(start)
    else:
      self.closed = [start]
    self.queue = []
    
    # Start by queueing all outbound links from the start node
    blankQueueItem = {'end':-1,'distance':0,'nodes':str(start)}

    try:
      for i in self.data.routing(start):
        self.addToQueue(start,i, blankQueueItem)
    except KeyError:
      return('no_such_node',[])

    # Limit for how long it will search
    count = 0
    while count < 1000:
      # pdb.set_trace()
      count = count + 1
      try:
        nextItem = self.queue.pop(0)
      except IndexError:
        # Queue is empty: failed
        # TODO: return partial route?
        return('no_route',[])
      x = nextItem['end']
      if x in self.closed:
        continue
      if x == end:
        # Found the end node - success
        routeNodes = [int(i) for i in nextItem['nodes'].split(",")]
        return('success', routeNodes)
      self.closed.append(x)
      try:
        for i in self.data.routing(x):
          if not i in self.closed:
            self.addToQueue(x,i,nextItem)
      except KeyError:
        pass
    else:
      return('gave_up',[])
  
  def addToQueue(self,start,end, queueSoFar, weight = 1):
    """Add another potential route to the queue"""

    # If already in queue, ignore
    for test in self.queue:
      if test['end'] == end:
        return
    distance = self.distance(start, end)
    if(weight == 0):
      return
    distance = distance / weight
    
    # Create a hash for all the route's attributes
    distanceSoFar = queueSoFar['distance']
    queueItem = { \
      'distance': distanceSoFar + distance,
      'maxdistance': distanceSoFar + self.distance(end, self.searchEnd),
      'nodes': queueSoFar['nodes'] + "," + str(end),
      'end': end}
    
    # Try to insert, keeping the queue ordered by decreasing worst-case distance
    count = 0
    for test in self.queue:
      if test['maxdistance'] > queueItem['maxdistance']:
        self.queue.insert(count,queueItem)
        break
      count = count + 1
    else:
      self.queue.append(queueItem)

if __name__ == "__main__":
  # Test suite - do a little bit of easy routing in birmingham
  data = LoadOsm("cycle")

  node1 = data.findNode(52.552394,-1.818763)
  node2 = data.findNode(52.563368,-1.818291)

  print(node1)
  print(node2)

  router = Router(data)
  result, route = router.doRoute(node1, node2)
  if result == 'success':
    # list the nodes
    print(route)

    # list the lat/long
    for i in route:
      node = data.rnodes[i]
      print("%d: %f,%f" % (i,node[0],node[1]))
  else:
    print("Failed (%s)" % result)
