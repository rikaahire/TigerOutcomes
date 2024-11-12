#!/usr/bin/env python

import flask
import database as db
# import auth
from top import app
# import dotenv
# import os

# dotenv.load_dotenv()
# secret_key = os.environ['APP_SECRET_KEY']

#-----------------------------------------------------------------------

# helper functions here
#-----------------------------------------------------------------------
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():

    # auth.authenticate()
    try:
        html_code = flask.render_template('homepage.html')
    except Exception as ex:
        print(ex)
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

#-----------------------------------------------------------------------

@app.route('/search', methods=['GET'])
def search():

    # auth.authenticate()
    # major = flask.request.args.get('major')
    major = 'English'
    try:
        # courses = db.get_student_by_major("pton_demographics", major) - deprecated, see below
        courses = db.get_rows("pton_demographics", "AcadPlanDescr", major)
        html_code = flask.render_template('search.html', majorsearch='English',
                                          data=courses)
    except Exception as ex:
        print(ex)
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

#-----------------------------------------------------------------------

@app.route('/landing', methods=['GET'])
def landing():

    # auth.authenticate()
    try:
        html_code = flask.render_template('landingpage.html')
    except Exception as ex:
        print(ex)
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

#-----------------------------------------------------------------------

@app.route('/job', methods=['GET'])
def job_details():

    # auth.authenticate()
    descript = db.get_occupational_data_full("11-1011.00")
    html_code = flask.render_template('job.html', description=descript[0], 
                                      skills=descript[1], knowledge=descript[2])
    response = flask.make_response(html_code)

    return response