import faicons as fa
import plotly.express as px

from shinywidgets import render_plotly
from shiny import reactive, render
from shiny.express import input, ui

income_range = 1


# Add page title and sidebar
ui.page_opts(title="TigerOutcomes", fillable=True)

with ui.sidebar(open="desktop"):
    
    ui.input_action_button("search", "Search")


with ui.layout_columns(fill=False):
    with ui.value_box():
        "Income Range",
        income_range
