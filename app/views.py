from flask import render_template, redirect, request, url_for
from app import app
from .forms import InputForm
from app.runsmartr.runrouter import RunRouter
import networkx as nx
from app.runsmartr.credentials import cred
import geopy.geocoders

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def run_input():
    form = InputForm(request.form)
    if request.method == 'POST' and form.validate():
        return redirect(url_for('run_output',
                        address=form.address.data,
                        distance=form.distance.data,
                        units=form.units.data))
    form.distance.data = ''
    return render_template('input.html',
                           form=form)

@app.route('/run', methods=['GET', 'POST'])
def run_output():
    form = InputForm(request.form)
    if request.method == 'POST' and form.validate():
        return redirect(url_for('run_output',
                        address=form.address.data,
                        distance=form.distance.data,
                        units=form.units.data))
    address = request.args.get('address')
    units = request.args.get('units')
    distance = float(request.args.get('distance'))
    form.address.data = address
    form.distance.data = request.args.get('distance')
    form.units.data = units
    geocoder = geopy.geocoders.GoogleV3(**cred['google'])
    start = geocoder.geocode(address)
    start_latlon = (start.latitude, start.longitude)
    center_latlon = '%f, %f' % start_latlon
    return render_template(
        'output.html',
        form=form,
        center_latlon=center_latlon,
        address=address,
        distance=distance,
        units=units)
        
@app.route('/route', methods=['POST'])
def run_route():
    address = request.form['address']
    units = request.form['units']
    fac_units = {'km': 1000.,
                 'mi': 1608.}
    distance = float(request.form['distance']) * fac_units[units]
    router = RunRouter(address, distance)
    router.find_route()
    route, lat0, lon0, lat1, lon1, milemarkers = router.data.detailed_path_latlon_milemarkers(router.current_route, fac_units[units])
    route_length = (router.get_route_length(router.current_route) /
                    fac_units[units])
    units_str = {'km': 'km',
                 'mi': 'mile'}
    route_json = ('{"actual_distance":"%.1f %s","route":%s,"lat0":%f,"lon0":%f,"lat1":%f,"lon1":%f,"milemarkers":%s}'
                  % (route_length, units_str[units], route, lat0, lon0, lat1, lon1, milemarkers))
    return route_json

@app.route('/runscore', methods=['POST'])
def run_score():
    address = request.form['address']
    units = request.form['units']
    fac_units = {'km': 1000.,
                 'mi': 1608.}
    distance = float(request.form['distance']) * fac_units[units]
    router = RunRouter(address, distance)
    foot_graph = router.data.foot_graph_latlon()
    run_score = [edge['run_score'] for edge in foot_graph]
    min_score = min(run_score)
    max_score = max(run_score)
    edges = [{'edge': edge['edge'],
              'weight': 1 + 9*(edge['run_score']-min_score) / (max_score-min_score)}
             for edge in foot_graph]
    edges_json = '[' + ','.join(('{"edge":%s,"weight":%f}'
        % (edge['edge'],
           edge['weight']))
        for edge in edges) + ']'
    return edges_json
