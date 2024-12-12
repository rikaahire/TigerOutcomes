#!/usr/bin/env python

#-----------------------------------------------------------------------
# admin_server.py
# Author: Bryan Zhang
#-----------------------------------------------------------------------

import flask
import auth
import json
import admin_database as dba

from top import app

# Admin commands
#-----------------------------------------------------------------------

# Generic admin checker
def check_admin():
    username = auth.authenticate()
    return dba.check_admin(username)

# Host the admin page
@app.route('/admin', methods=['GET'])
def admin():
    try:
        if check_admin():
            return flask.send_file('templates/admin.html')
        else:
            html_code = flask.render_template('homepage.html')
    except Exception as ex:
        print(ex)
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

# List all admin users
@app.route('/list_admin', methods=['GET'])
def list_admin():
    if check_admin():
        html_code = dba.get_admins()
    else:
        html_code = "Bad user"
    
    json_doc = json.dumps(html_code)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

# Add an admin user
@app.route('/add_admin', methods=['GET'])
def add_admin():
    user = flask.request.args.get('user')
    if user is None or not user:
        html_code = "No input"

    if check_admin():
        dba.add_admin(user)
        html_code = "Added admin: " + user;
    else:
        html_code = "Bad user"
    
    json_doc = json.dumps(html_code)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

# Remove an admin user
@app.route('/remove_admin', methods=['GET'])
def remove_admin():
    user = flask.request.args.get('user')
    if user is None or not user:
        html_code = "No input"
    
    if check_admin():
        dba.remove_admin(user)
        html_code = "Removed admin: " + user;
    else:
        html_code = "Bad user"
    
    json_doc = json.dumps(html_code)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

# Comment commands
#-----------------------------------------------------------------------

# List all comments users have flagged
@app.route('/list_flagged_comments', methods=['GET'])
def list_unapproved_comments():
    if check_admin():
        html_code = dba.fetch_flagged_comments()
    else:
        html_code = "Bad user"
    
    json_doc = json.dumps(html_code)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

# Approve a comment (let it stay)
@app.route('/approve_comment', methods=['GET'])
def approve_comment():
    id = flask.request.args.get('id')
    if id is None or not id:
        html_code = "No comment selected"
    
    if check_admin():
        html_code = dba.approve(id)
    else:
        html_code = "Not an admin"
    
    json_doc = json.dumps(html_code)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

# Remove a comment ("unapprove it")
@app.route('/remove_comment', methods=['GET'])
def remove_comment():
    id = flask.request.args.get('id')
    if id is None or not id:
        html_code = "No comment selected"
    
    if check_admin():
        html_code = dba.remove(id)
    else:
        html_code = "Not an admin"
    
    json_doc = json.dumps(html_code)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response

# Call as admin to remove all comments from system
@app.route('/flush_comments', methods=['GET'])
def flush_comments():
    if check_admin():
        html_code = dba.removeAll()
    else:
        html_code = "Not an admin"
    
    json_doc = json.dumps(html_code)
    response = flask.make_response(json_doc)
    response.headers['Content-Type'] = 'application/json'
    return response