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
    form.units.data = request.args.get('units')
    if request.args.get('units') == 'km':
        distance = float(request.args.get('distance')) * 1000.
    else:
        distance = float(request.args.get('distance')) * 1608.
    address = request.args.get('address')
    router = RunRouter(address, distance)
    latlon_string = '%f, %f' % router.data.start
    foot_graph = router.data.foot_graph_latlon()
    run_score = [edge['run_score'] for edge in foot_graph]
    min_score = min(run_score)
    max_score = max(run_score)
    edges = [{'edge': edge['edge'],
              'weight': 1 + 9*(edge['run_score']-min_score) / (max_score-min_score)}
             for edge in foot_graph]
    router.initialize_search()
    route = router.data.detailed_path_latlon(router.current_route)
    return render_template('output.html',
                           form=form,
                           latlon_string=latlon_string,
                           edges=edges,
                           route=route)
