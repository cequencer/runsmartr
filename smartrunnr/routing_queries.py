from credentials import cred
import psycopg2
import json

class RoutingDB:

    def __init__(self):
        self.db_conn = psycopg2.connect(**cred['db'])
        self.db_cur = self.db_conn.cursor()


