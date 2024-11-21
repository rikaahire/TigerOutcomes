#!/usr/bin/env python

import flask
import database as db
import json
import auth
from top import app
import dotenv
import os

dotenv.load_dotenv()
app.secret_key = os.environ['APP_SECRET_KEY']

#-----------------------------------------------------------------------

# helper functions here
#-----------------------------------------------------------------------
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
@app.route('/home', methods=['GET'])
def home():

    username = auth.authenticate()
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
    return flask.send_file('templates/search.html')

@app.route('/favorites', methods=['GET'])
def favorite():
    return flask.send_file('templates/favorites.html')

#-----------------------------------------------------------------------

# get results from a major search
@app.route('/results', methods=['GET'])
def results():
    major = flask.request.args.get('major')
    if major is None:
        major = ''
        major = major.strip()
    results = db.get_positions_by_acadplandesc(major)
    results = [{'row': row, 'soc_code': '11-1011.00'} for row in results]
    # results = db.get_rows("pton_demographics", "AcadPlanDescr", major)
    # results = [{'row':tuple(row), 'soc_code': '11-1011.00'} for row in results]
    # will want to change results to a major -> job call
    json_doc = json.dumps(results)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

# details for a job (soc_code)
@app.route('/job', methods=['GET'])
def job_details():
    auth.authenticate()
    soc_code = flask.request.args.get('soc_code')
    if soc_code is None:
        return ['Nada here']
    descript = db.get_occupational_data_full(soc_code)
    description = descript['description']
    skills = descript['skills']
    knowledge = descript['knowledge']
    wage = descript['wage']
    descript= {'description': [tuple(row) for row in description], 'skills': [tuple(row) for row in skills], 'knowledge': [tuple(row) for row in knowledge], 'wage': [tuple(row) for row in wage]}
    json_doc = json.dumps(descript)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    # html_code = flask.render_template('job.html', description=descript[0], 
    #                                   skills=descript[1], knowledge=descript[2])
    # response = flask.make_response(html_code)

    return response

# get all favorites for a user
@app.route('/preferences', methods=['GET'])
def preferences():
    user = auth.authenticate()
    # user = flask.request.args.get('user')
    # if user is None:
    #     return []
    descript = db.read_favorites(name=user, status=True)
    # gets soc_codes
    descript = [tuple(row) for row in descript]
    json_doc = json.dumps(descript)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    # html_code = flask.render_template('job.html', description=descript[0], 
    #                                   skills=descript[1], knowledge=descript[2])
    # response = flask.make_response(html_code)

    return response

# get all favorites for a user
@app.route('/update', methods=['GET'])
def update():
    user = auth.authenticate()
    # user = flask.request.args.get('user')
    # if user is None:
    #     return []
    soc_code = flask.request.args.get('soc_code')
    if soc_code is None:
        return []
    status = flask.request.args.get('status')
    if status is None:
        return []
    else:
        status = bool(status)
    descript = [db.write_favorite(name=user, soc_code=soc_code, status=status)]
    json_doc = json.dumps(descript)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/delete', methods=['GET'])
def delete():
    user = auth.authenticate()
    # user = flask.request.args.get('user')
    # if user is None:
    #     return []
    status = flask.request.args.get('status')
    ret = db.clear_favorites(user, status)
    json_doc = json.dumps(ret)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response