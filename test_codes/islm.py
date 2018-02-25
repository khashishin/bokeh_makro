''' Present an interactive function explorer with slider widgets.
Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.
Use the ``bokeh serve`` command to run the example by executing:
    bokeh serve sliders.py
at your command prompt. Then navigate to the URL
    http://localhost:5006/sliders
in your browser.
'''
from bokeh.embed import server_document
from bokeh.layouts import column, row, widgetbox, layout
from bokeh.models import ColumnDataSource, Slider, TextInput, CustomJS, Span, HoverTool, Title
from bokeh.client import pull_session
from bokeh.embed import server_session
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.io import curdoc
from bokeh.resources import INLINE

from bokeh.models.widgets import Div

from sympy import *
import numpy as np
import math
import random

def create_equation():
    equation = "C = \\bar{C} + cY_d = \\bar{C} + c(Y-T), \space \\frac{\delta C}{\delta Y_d}"
    equation_text = "\({}\)".format(equation)
    return equation_text

def generate_text():
    # return "C = \\bar{C} + cY_d = \\bar{C} + c(Y-T), \space \\frac{\delta C}{\delta Y_d}"
    return str(random.randint(1, 500))  


# Set up data
#Definicja źródła danych, które generujemy numerycznie
# C = 10 + 0.5 Y
# I = 190 - 20i
c_const_value = 10
c_y_value = 0.5
i_i_value = 20
i_const_value = 190

# Set up data
#Definicja źródła danych, które generujemy numerycznie
N = 1000 # Liczba "numerycznie" wygenerowanych punktów - monte carlo
my_range = 20 # Max c_const X, ogranicza też widok Y i chwiliwo na jej podstawie tworzy się Ujemna, idaca w dol IS
x = np.linspace(0, my_range, N)
y = [ ((1 / (1 - (1-c_y_value)) ) * (c_const_value+i_const_value - (i_i_value * i))) for i in x]
# y3 = [-el+my_range for el in y2]
source = ColumnDataSource(data=dict(x=x, y=y))
# source2 = ColumnDataSource(data=dict(x=x, y=y2))
# source_plot2 = ColumnDataSource(data=dict(x=x, y=y3))

# Tworzenie wykresu - sam wykres jest nieinteraktywny
#https://bokeh.pydata.org/en/latest/docs/user_guide/quickstart.html
plot = figure(plot_height=800, plot_width=600, title="",
              x_range=[0, my_range], y_range=[0, my_range], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above",
               x_axis_label='Y', y_axis_label='i')

# plot2 = figure(plot_height=800, plot_width=600, title="",
#               x_range=[0, my_range], y_range=[0, my_range], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above")

#Wykresy danych
plot.line("x","y", source=source, legend="IS", line_width=3, line_color="Green", line_alpha=0.6)
# plot.line("x","y", source=source2, legend="LM", line_width=3, line_color="Red", line_alpha=0.6)
# plot2.line("x","y", source=source_plot2, legend="test", line_width=3, line_color="Blue", line_alpha=0.6)
#Os wspolrzednych
plot.renderers.extend([Span(location=0, dimension='height', line_color='black', line_width=1), Span(location=0, dimension='width', line_color='black', line_width=1)])

#Dodatkowy test
sometext = Title(text=generate_text(), align="center")
plot.add_layout(sometext, "below")

#INTERAKCJA - hover
#https://bokeh.pydata.org/en/latest/docs/user_guide/tools.html#basic-tooltips
hover = HoverTool(tooltips=None, mode='vline')
hover.tooltips = [("(x,y)", "($x,$y)"),
                    ("punkt rownowagi", "1245")]
plot.add_tools(hover) 

# Widgety - interackcja
#Bokeh nie ma float input - mozliwe bledy bez castowania
c_y = TextInput(title="Stala C", value=str(round(c_y_value,2)))
c_const = Slider(title="Funkcja Konsumpcji", value=c_y_value, start=0, end=1.0, step=0.1)
i_i = Slider(title="Funckja i", value=i_i_value, start=0, end=100.0, step=1)
i_const = TextInput(title="Stala i", value=str(round(i_const_value,2)))

# Callbacki - definiowane sa de facto jak w JavaScripcie - 
#czyli dzialaja jak dodamy je do on_change obiektów dopiero, nazwa funkcji nie jest wazna, odnosimy sie do niej tylko przy on_change

div = Div(text=""" 
    KRZYWA IS 

    C = {c_const} + {c_y} Y
    <br>
    I = {i_const} - {i_i} i
    <br>
    Y = AD = {c_const} + {c_y} Y + {i_const} - {i_i} i
    """.format(c_const=c_const, c_y=c_y, i_const = c_const , i_i= c_const),
width=400, height=300)

def update_data(attrname, old, new):
    # Wartości sliderów
    c_y_value = c_const.value
    i_const_value = i_const.value
    try:
        c_y_value = float(c_y.value)
    except ValueError:
        c_y_value = 1.0
    try:
        i_i_value = float(i_i.value)
    except ValueError:
        i_i_value = 1.0

    # Update source.data w efekcie generuje nowy wykres
    x = np.linspace(0, my_range, N)
    y = [ ((1 / (1 - (1-c_y_value)) ) * (c_const_value+i_const_value - (i_i_value * i))) for i in x]
    # y3 = [-el+my_range for el in y2]

    source.data  =dict(x=x, y=y)
    # source2.data = dict(x=x, y=y2)
    # source_plot2.data = dict(x=x, y=y3)

    div.text = "$$"+ """ 
    KRZYWA IS 

    C = {c_const} + {c_y} Y
    <br>
    I = {i_const} - {i_i} i
    <br>
    Y = AD = {c_const} + {c_y} Y + {i_const} - {i_i} i
    """.format(c_const=c_const_value, c_y=c_y_value, i_const = c_const_value , i_i= c_const_value) 
    +"$$"

#TODO based on https://bokeh.pydata.org/en/latest/docs/user_guide/interaction/callbacks.html#customjs-for-user-interaction-events
js_latexize_code = """
div_value = div.innerHTML;
MathJax.Hub.Queue(["Typeset",MathJax.Hub,div_value]);
""".replace("/","&#92")

for w in [c_y, c_const, i_const, i_i]:
    w.on_change('value', update_data)
    #Nie można tu wykorzystać texa ani nic podobnego, wszystkie dynamiczne rzeczy muszą odbywać się w kodzie JS w js_code.
    # Dzialanie nie do konca takie jak trzeba - Text nie moze miec on_change listenera...
    w.js_on_change('value', CustomJS(args=dict(div = div),code=js_latexize_code))

# Grupowanie widgetów i layout
widgets = widgetbox(c_y, c_const, i_const, i_i, width=150)
# layout = row(widgets, plot, plot2, width=400, height = 400)
complex_layout = layout([
  [widgets, plot],
  [div],
], sizing_mode='fixed')
#Finalne tworzenie dokumentu, który może zostać serwowany w serwerze
# doc.add_root(complex_layout)
# doc.title = "Sliders"
# doc.theme = Theme(filename="theme.yaml")

curdoc().add_root(row(widgets, plot, width=800))
curdoc().title = "Sliders"