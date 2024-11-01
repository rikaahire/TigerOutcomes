from shiny import reactive, render
from shiny.express import input, ui
import prototype

income_range = 1
degree = "string"
values = prototype.get_values()[1]

# Add page title
ui.page_opts(title="TigerOutcomes", fillable=True)

# Add sidebar
with ui.sidebar(open="desktop"):
    ui.input_text("major_search", "Major:", ""),
    "You entered:"
    @render.text(inline=True)  
    def text():
        return input.major_search()
    ui.input_action_button("search", "Search", class_="btn-success"),

with ui.layout_columns(fill=False):
    with ui.value_box():
        "Income Range",
        income_range

    with ui.value_box():
        "value",
        degree

    with ui.value_box():
        "Degree",
        degree
