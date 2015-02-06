from flask import render_template, request
from app import app
from .forms import InputForm
from app.runsmartr.runrouter import RunRouter

# rr = RunRouter()

@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
def cities_input():
    form = InputForm()
    return render_template('base.html',
                           form=form)
