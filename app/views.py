import re
import pandas as pd
import numpy as np
import requests
import json
import random
import time
import psycopg2
import geopy.geocoders
from flask import render_template, request

from app import app
from runrouter import RunRouter

rr = RunRouter()

@app.route('/')
@app.route("/index")
def cities_page_fancy():
    cities = []
    return render_template('cities.html', cities=cities)

@app.route('/input')
def cities_input():
    return render_template("input.html")

@app.route('/output')
def cities_output():
    address = request.args.get('ADDR')
    distance = int(request.args.get('DIST'))
    rr.do_route('355 berry st, san francisco', distance*1600)
    rr.update_folium_map()
    rr.run_map.create_map(path='app/templates/stamen_toner.html')
    return render_template("output.html", address=address,
                           distance=('%d' % distance))
