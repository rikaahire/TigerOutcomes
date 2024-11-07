#!/usr/bin/env python

import flask
import database as db
import auth
from top import app
import dotenv

dotenv.load_dotenv()
# secret_key = os.environ['APP_SECRET_KEY']

#-----------------------------------------------------------------------

# helper functions here
#-----------------------------------------------------------------------
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def reg_overviews():

    auth.authenticate()
    major = flask.request.args.get('major')

    try:
        courses = db.get_rows("demographics", major)
        html_code = flask.render_template('search.html')
    except Exception:
        html_code = flask.render_template('servererror.html')

    response = flask.make_response(html_code)
    return response

#-----------------------------------------------------------------------

@app.route('/job', methods=['GET'])
def reg_details():

    auth.authenticate()
    html_code = flask.render_template('job.html')
    response = flask.make_response(html_code)

    return response


# from shiny import reactive, render
# from shiny.express import input, ui
# import prototype
# import os

# secret_key = os.environ['APP_SECRET_KEY']

# income_range = 1
# degree = "string"
# values = []

# # Add page title
# ui.page_opts(title="TigerOutcomes", fillable=True)

# # Add sidebar
# with ui.sidebar(open="desktop"):
#     ui.input_text("major_search", "Major:", "Computer Science"),
#     ui.input_action_button("search", "Search", class_="btn-success"),

# with ui.layout_columns(fill=False):
#     with ui.value_box():
#         "Degree",
#         @render.text(inline=True)  
#         def text():
#             return input.major_search()

#     with ui.value_box():
#         "First Gen",
#         @render.text(inline=True)  
#         def value_txt():
#             values = prototype.get_values(input.major_search())            
#             return values[2]
        
#     with ui.value_box():
#         "Income",
#         @render.text(inline=True)  
#         def income_txt():
#             values = prototype.get_values(input.major_search())
#             return "$" + str (values[3])
    
#     with ui.value_box():
#         "Degree Type",
#         @render.text(inline=True)  
#         def sex_txt():
#             values = prototype.get_values(input.major_search())
#             return values[4]
        

    
