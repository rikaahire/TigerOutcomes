#!/usr/bin/env python

#-----------------------------------------------------------------------
# admin_server.py
# Author: Bryan Zhang
#-----------------------------------------------------------------------

import flask
import auth
import admin_database as db

from top import app

#-----------------------------------------------------------------------
def check_admin():
    username = auth.authenticate()
    return db.check_admin(username)

@app.route('/list_admin', methods=['GET'])
def list_admin():
    if check_admin():
        html_code = flask.render_template('admin.html')
    else:
        html_code = flask.render_template('landingpage.html')
    response = flask.make_response(html_code)
    return response

@app.route('/add_admin', methods=['GET'])
def add_admin():
    user = flask.request.args.get('user')
    if user is None:
        html_code = flask.render_template('landingpage.html')
    if check_admin():
        db.add_admin(user)
        html_code = flask.render_template('admin.html')
    else:
        html_code = flask.render_template('landingpage.html')
    response = flask.make_response(html_code)
    return response
