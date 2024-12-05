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

@app.route('/add_admin', methods=['GET'])
def add_admin():
    username = auth.authenticate()
    user = flask.request.args.get('user')
    if user is None:
        html_code = flask.render_template('landingpage.html')
    if db.check_admin(username):
        db.add_admin(user)
        html_code = flask.render_template('admin.html')
    else:
        html_code = flask.render_template('landingpage.html')
    response = flask.make_response(html_code)
    return response
