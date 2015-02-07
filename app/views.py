from flask import render_template, redirect, request, url_for
from app import app
from .forms import InputForm
from app.runsmartr.runrouter import RunRouter

@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def run_input():
    form = InputForm(request.form)
    if request.method == 'POST' and form.validate():
        return redirect(url_for('run_output',
                        address=form.address.data,
                        distance=form.distance.data,
                        units=form.units.data))
    return render_template('base.html',
                           form=form)

@app.route('/run', methods=['GET', 'POST'])
def run_output():
    form = InputForm(request.form)
    form.address.data = request.args.get('address')
    form.distance.data = request.args.get('distance')
    form.units.data = request.args.get('units')
    if request.args.get('units') == 'km':
        distance = float(request.args.get('distance')) * 1000.
    else:
        distance = float(request.args.get('distance')) * 1608.
    rr = RunRouter()
    latlon = rr.data.find_latlon_address(
        request.args.get('address'))
    latlon_string = '%f, %f' % (latlon[0], latlon[1])
    return render_template('output.html',
                           form=form,
                           latlon_string=latlon_string)
