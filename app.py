import flask
import database

#----------------------------------------------------------------------

app = flask.Flask(__name__, template_folder='.')

#----------------------------------------------------------------------
# General Routes
#----------------------------------------------------------------------
# Homepage
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    html = flask.render_template('templates/homepage.html')
    response = flask.make_response(html)
    return response
@app.route('/job', methods=['GET'])
def index():
    html = flask.render_template('templates/job.html')
    response = flask.make_response(html)
    return response
@app.route('/search', methods=['GET'])
def index():
    html = flask.render_template('templates/search.html')
    response = flask.make_response(html)
    return response
@app.route('/settings', methods=['GET'])
def index():
    html = flask.render_template('templates/settings.html')
    response = flask.make_response(html)
    return response
