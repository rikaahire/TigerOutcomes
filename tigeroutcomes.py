#!/usr/bin/env python

import flask
import database as db
import json
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

@app.route('/results', methods=['GET'])
def results():
    major = flask.request.args.get('major')
    if major is None:
        major = ''
        major = major.strip()
    results = db.get_rows("pton_demographics", "AcadPlanDescr", major)
    results = [tuple(row) for row in results]
    # will want to change results to a major -> job call
    json_doc = json.dumps(results)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

#-----------------------------------------------------------------------

@app.route('/job', methods=['GET'])
def job_details():
    soc_code = flask.request.args.get('soc_code')
    if soc_code is None:
        return []
    # auth.authenticate()
    descript = db.get_occupational_data_full(soc_code)
    descript = [tuple(row) for row in descript]
    json_doc = json.dumps(descript)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    # html_code = flask.render_template('job.html', description=descript[0], 
    #                                   skills=descript[1], knowledge=descript[2])
    # response = flask.make_response(html_code)

    return response