#!/usr/bin/env python

import flask
import database as db
import json
import auth
import admin_server
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

@app.route('/home', methods=['GET'])
def home():
    auth.authenticate()
    try:
        html_code = flask.render_template('homepage.html')
    except Exception as ex:
        print(ex)
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

@app.route('/about', methods=['GET'])
def about():
    auth.authenticate()
    try:
        html_code = flask.render_template('about.html')
    except Exception as ex:
        print(ex)
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

@app.route('/help', methods=['GET'])
def help():
    auth.authenticate()
    try:
        html_code = flask.render_template('help.html')
    except Exception as ex:
        print(ex)
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

#-----------------------------------------------------------------------

@app.route('/search', methods=['GET'])
def search():
    auth.authenticate()
    return flask.send_file('templates/search.html')

@app.route('/favorites', methods=['GET'])
def favorite():
    auth.authenticate()
    return flask.send_file('templates/favorites.html')

#-----------------------------------------------------------------------

# get results from a major search
@app.route('/results', methods=['GET'])
def results():
    major = flask.request.args.get('major')
    if major is None:
        major = ''
        major = major.strip()
    algo = flask.request.args.get('algo')
    if algo is None:
        algo = ''
        algo = algo.strip()
    min_wage = flask.request.args.get('min_wage')
    if min_wage is None:
        min_wage = 0
    results = db.get_onet_soc_codes_by_acadplandesc(major, algo, min_wage)
    results = [{'row': row, 'soc_code': code} for (code, row) in results]
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
    work_styles = descript['work_styles']
    title = db.get_name_from_soc(soc_code)
    descript= {'description': [tuple(row) for row in description], 
               'skills': [tuple(row) for row in skills], 
               'knowledge': [tuple(row) for row in knowledge], 
               'wage': wage,
               'soc_code': soc_code,
               'title': [tuple(row) for row in title],
               'work_styles': [tuple(row) for row in work_styles]}
    json_doc = json.dumps(descript)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    # html_code = flask.render_template('job.html', description=descript[0], 
    #                                   skills=descript[1], knowledge=descript[2])
    # response = flask.make_response(html_code)

    return response

#-----------------------------------------------------------------------

# get all favorites for a user
@app.route('/preferences', methods=['GET'])
def preferences():
    user = auth.authenticate()
    # user = flask.request.args.get('user')
    # if user is None:
    #     return []
    fav = db.read_favorites(name=user, status=True)
    # gets soc_codes
    fav = [{"name": row[0], "soc_code": row[1], "title": row[3]} for row in fav]
    json_doc = json.dumps(fav)
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
    soc_code = flask.request.args.get('soc_code')
    if soc_code is None:
        json_doc = [False, 'missing soc code']
        response = flask.make_response(json_doc)
        response.headers['Content-Type'] = 'application/json'
        return response

    try:
        status = flask.request.args.get('status')
        ret = [True, db.clear_favorites(user, status, soc_code)]
        json_doc = json.dumps(ret)
    except:
        json_doc = [False, ('A server error occurred. Please contact'
                    ' the system administrator')]

    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

#-----------------------------------------------------------------------

@app.route('/write_comment', methods=['GET'])
def write_comment():
    user = auth.authenticate()
    soc_code = flask.request.args.get('soc_code')
    if not soc_code:
        json_doc = [False, "Missing soc_code"]
    print(soc_code)
    text = flask.request.args.get('text')
    if not text:
        json_doc = [False, "Missing text"]
    try:
        ret = db.write_comment(user, soc_code, text, valid=True)
        json_doc = json.dumps([True, ret])
    except Exception as e:
        json_doc = [False, f"Error posting comments: {e}"]
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/flag_comment', methods=['GET'])
def flag_comment():
    user = auth.authenticate()
    id = flask.request.args.get('id')
    if not id:
        json_doc = [False, "Missing id"]
    try:
        ret = db.update_comment(user, id, False)
        json_doc = json.dumps([True, ret])
    except Exception as e:
        json_doc = [False, f"Error flagging comment: {e}"]
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/comments', methods=['GET'])
def see_comments():
    soc_code = flask.request.args.get('soc_code')
    if not soc_code:
        json_doc = [False, "Missing soc_code"]
    try:
        comments = db.fetch_comments(soc_code)
        json_doc = json.dumps({"soc_code": soc_code, "continue": True, "full": comments})
    except Exception as e:
        json_doc = [False, f"Error getting comments: {e}"]
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

#-----------------------------------------------------------------------

@app.route('/get_user', methods=['GET'])
def get_user():
    user = auth.authenticate()
    try:
        json_doc = json.dumps({"user": user})
    except Exception as e:
        json_doc = [False, f"Error retrieving user: {e}"]
    
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

