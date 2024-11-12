from shiny import App, reactive, render
from shiny.express import input, ui
import prototype

income_range = 1
degree = "string"
values = []

app_ui = ui.page_fluid(  # Define app UI
    ui.page_opts(title="TigerOutcomes", fillable=True),
    
    # Add sidebar
    ui.sidebar(
        open="desktop",
        ui.input_text(id="major_search", label="Major:", placeholder="Computer Science"),  # Updated argument names to resolve syntax conflict
        ui.input_action_button(id="search", label="Search", class_="btn-success")
    ),
    
    # Add layout columns
    ui.layout_columns(fill=False,
        ui.value_box(
            "Degree",
            render.text(inline=True)(lambda: input.major_search())
        ),
        ui.value_box(
            "First Gen",
            render.text(inline=True)(lambda: prototype.get_values(input.major_search())[2])
        ),
        ui.value_box(
            "Income",
            render.text(inline=True)(lambda: "$" + str(prototype.get_values(input.major_search())[3]))
        ),
        ui.value_box(
            "Degree Type",
            render.text(inline=True)(lambda: prototype.get_values(input.major_search())[4])
        ),
    )
)

app = App(app_ui)  # Define the app with app_ui
