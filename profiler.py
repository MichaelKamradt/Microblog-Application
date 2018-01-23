# !flask/bin/python

from werkzeug.contrib.profiler import ProfilerMiddleware
from app import app

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30]) # Shows the 30 most expensive funtions
app.run(debug=True)