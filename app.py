import flask

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
