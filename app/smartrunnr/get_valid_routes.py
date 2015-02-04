#!/usr/bin/env python

"""
CREATE VIEW routes_potrero_hill_valid
AS (SELECT * FROM routes_potrero_hill, highways_buffered
WHERE ST_Within(linestring, the_geom));"""

