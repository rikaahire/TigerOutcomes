from shiny import reactive, render
from shiny.express import input, ui
import prototype



income_range = 1
degree = "string"
values = []

# Add page title
ui.page_opts(title="TigerOutcomes", fillable=True)

# Add sidebar
with ui.sidebar(open="desktop"):
    ui.input_text("major_search", "Major:", ""),
    ui.input_action_button("search", "Search", class_="btn-success"),

with ui.layout_columns(fill=False):
    with ui.value_box():
        "Degree",
        @render.text(inline=True)  
        def text():
            values = prototype.get_values(input.major_search())
            return input.major_search()

    with ui.value_box():
        "First Gen",
        @render.text(inline=True)  
        def value_txt():
            values = prototype.get_values(input.major_search())            
            return values[2]
        
    with ui.value_box():
        "Income",
        @render.text(inline=True)  
        def income_txt():
            values = prototype.get_values(input.major_search())
            return "$" + str (values[3])
    
    with ui.value_box():
        "Degree Type",
        @render.text(inline=True)  
        def sex_txt():
            values = prototype.get_values(input.major_search())
            return values[4]
        

    
