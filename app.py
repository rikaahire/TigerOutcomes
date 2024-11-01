from shiny import reactive, render
from shiny.express import input, ui

income_range = 1
degree = "string"

# Add page title and sidebar
ui.page_opts(title="TigerOutcomes", fillable=True)

with ui.sidebar(open="desktop"):
    ui.input_text("major_search", "Major:", ""),
    ui.input_action_button("search", "Search", class_="btn-success"),

with ui.layout_columns(fill=False):
    with ui.value_box():
        "Income Range",
        income_range

    ui.input_text("Text", "We will repeat this", "Example")
    "You entered:"
    @render.text(inline=True)  
    def text():
        return input.Text()

    with ui.value_box():
        "Degree",
        degree
