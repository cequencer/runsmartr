from flask import render_template, request
from app import app
from app.runsmartr.runrouter import RunRouter

# rr = RunRouter()

@app.route('/')
@app.route('/index')
def cities_input():
    return render_template("index.html")

# @app.route('/output')
# def cities_output():
#     address = request.args.get('ADDR')
#     distance = int(request.args.get('DIST'))
#     rr.do_route(address, distance*1600)
#     rr.update_folium_map()
#     rr.run_map.create_map(path='app/templates/stamen_toner.html')
#     return render_template("output.html", address=address,
#                            distance=('%d' % distance))
