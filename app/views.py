from flask import render_template, redirect, request, url_for
from app import app
from .forms import InputForm
from app.runsmartr.runrouter_cycles import RunRouter
import networkx as nx

import pdb

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
    return render_template('base.html',
                           form=form)

@app.route('/run', methods=['GET', 'POST'])
def run_output():
    form = InputForm(request.form)
    if request.method == 'POST' and form.validate():
        return redirect(url_for('run_output',
                        address=form.address.data,
                        distance=form.distance.data,
                        units=form.units.data))
    form.address.data = request.args.get('address')
    form.distance.data = request.args.get('distance')
    form.units.data = units
    center_latlon = '%f, %f' % router.data.start

    return render_template(
        'output.html',
        center_latlon=center_latlon)
        
@all.route('/route', methods=['POST'])
def run_route():
    address = request.args.get('address')
    units = request.args.get('units')
    fac_units = {'km': 1000,
                 'mi': 1608}
    distance = (float(request.args.get('distance')) *
                fac_units[units])
    router = RunRouter(address, distance)
    router.do_route()
    route = router.data.detailed_path_latlon(router.current_route)
    route_length = (router.get_route_length(router.current_route) /
                    fac_units[units])
    units_str = {'km': 'km', 'mi': 'mile'}
    route_json = "{'distance':%f,'route':%s}" % (distance, route)
    return route_json

@app.route('/runscore', methods=['POST'])
def run_score():
    router = RunRouter(address, distance)
    foot_graph = router.data.foot_graph_latlon()
    run_score = [edge['run_score'] for edge in foot_graph]
    min_score = min(run_score)
    max_score = max(run_score)
    edges = [{'edge': edge['edge'],
              'weight': 1 + 9*(edge['run_score']-min_score) / (max_score-min_score)}
             for edge in foot_graph]
