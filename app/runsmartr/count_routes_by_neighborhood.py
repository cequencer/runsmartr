#!/usr/bin/env python
import pandas as pd
import psycopg2
from credentials import cred

def count_routes():
    conn = psycopg2.connect(**cred['db'])
    cur = conn.cursor()
    cur.execute('''
SELECT DISTINCT name FROM neighborhoods;''')
    names = [name for nt in cur.fetchall() for name in nt]
    count = []
    for name in names:
        cur.execute('''
SELECT COUNT(*)
    FROM mmf_routes, neighborhoods
WHERE
    ST_Within(point, polygon) AND name = %s''', (name,))
        count.append(cur.fetchall()[0][0])
    results = pd.DataFrame({
        'names': names,
        'count': count
    })
    print results

if __name__ == '__main__':
    count_routes()
