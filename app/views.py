from flask import render_template, request
from app import app
from .forms import InputForm
from app.runsmartr.runrouter import RunRouter

# rr = RunRouter()

@app.route('/')
@app.route('/index')
def cities_input():
    return render_template('base.html')

@app.route('/input', methods=['GET', 'POST'])
def input():
    form = InputForm()
    return render_template('input.html',
                           title='Input',
                           form=form);
