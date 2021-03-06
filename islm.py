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

from bokeh import events
from bokeh.models.widgets import Div

from sympy import *
import numpy as np
import math
import random

import jinja2       

static_is_div_test = """ 
        Krzywa \space IS 
        <br>
        {main_equation}
        <br>
        C = a + b (Y - tY) + G - T
        <br>
        tY = {tax_value} Y
        <br>
        T = {tax_constant}
        <br>
        G = {g_value}
        <br>
        C = {c_const} + {c_y} (Y - {tax_value}Y) - {tax_constant}
        <br>
        I = {i_const} - {i_i} i
        <br>
        Y = {c_const} + {c_y} (Y - {tax_value}Y) + {i_const} - {i_i} i + {g_value} - {tax_constant}
        <br>
        Y = \\frac {{ 1}} {{1 - b }} (a + \\bar{{I}}) - di
        <br>
        Y = \\frac {{ 1}} {{1 - {c_y} * (1 - {tax_value}) }}  * ({c_const}+{i_const}+{g_value}-{tax_constant} - {i_i} i )  
        """

static_lm_div_test = """ 
        Krzywa \space LM
        <br>
        M_d = M_s
        <br>
        M_d = {money_constant} + {prod_money_coeff} Y  - {i_prod_money_coeff} i
        <br>
        M_s = \\frac{{M}}{{P}}= {money_supply}
        <br>
        i =  \\frac {{ {prod_money_coeff} Y + {money_constant} - {money_supply} }} {{ {i_prod_money_coeff} }}
        <br>
        """

def create_equation():
    return "C = \\bar{C} + cY_d = \\bar{C} + c(Y-T), \space "

def generate_text():
    return str(random.randint(1, 500))  

def escape_to_latex(text):
    return "$$" +text+ "$$"

def generate_x_and_y_islm(c_y_value, c_const_value, i_i_value, i_const_value, g_value, tax_value, tax_constant):
    N = 2000 # Liczba "numerycznie" wygenerowanych punktów - monte carlo    
    x = np.linspace(0, 100, N)
    y = [ ((1 / (1 - c_y_value*(1 - tax_value)) ) * (c_const_value+i_const_value+g_value-tax_constant - (i_i_value * i))) for i in x]
    return x,y

def generate_x_and_y_lm(prod_money_coeff, money_constant, i_prod_money_coeff, money_supply):
    N = 2000 # Liczba "numerycznie" wygenerowanych punktów - monte carlo    
    x = np.linspace(0, 10000, N) # STOPA PROCENTOWA   
    y = [ ( ( (prod_money_coeff * i) + (money_constant - money_supply)) / i_prod_money_coeff ) for i in x]
    return y,x


# Problem 6 - works http://www.economicsdiscussion.net/is-lm-curve-model/algebraic-analysis-of-is-lm-model-with-numerical-problems/10609
c_const_value = 100
c_y_value = 0.8
i_const_value = 50
i_i_value = 25
g_value = 50
tax_value = 0.0
tax_constant = 40

x_range_is = 10
y_range_is = 400

prod_money_coeff = 1
money_constant = 0
i_prod_money_coeff = 25
money_supply = 200

#Definicja źródła danych, które generujemy numerycznie
x, y = generate_x_and_y_islm(c_y_value, c_const_value, i_i_value, i_const_value, g_value, tax_value, tax_constant)
source = ColumnDataSource(data=dict(x=x, y=y))
x_2, y_2 = generate_x_and_y_lm(prod_money_coeff, money_constant, i_prod_money_coeff, money_supply)
source2 = ColumnDataSource(data=dict(x=x_2, y=y_2))

# Tworzenie wykresu - sam wykres jest nieinteraktywny
#https://bokeh.pydata.org/en/latest/docs/user_guide/quickstart.html
plot = figure(plot_height=800, plot_width=600, title="Krzywa IS",
              x_range=[0, x_range_is], y_range=[0, y_range_is], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above",
               x_axis_label="stopa procentowa i", y_axis_label="Y")

plot2 = figure(plot_height=800, plot_width=600, title="Krzywa LM",
              x_range=[0, x_range_is], y_range=[0, y_range_is], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above",
               x_axis_label="Y", y_axis_label="stopa procentowa i")


plot3 = figure(plot_height=800, plot_width=600, title="IS LM",
              x_range=[0, x_range_is], y_range=[0, y_range_is], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above",
               x_axis_label="IS", y_axis_label="LM")

#Wykresy danych
plot.line("x","y", source=source, legend="IS", line_width=3, line_color="Green", line_alpha=0.6)
plot2.line("x","y", source=source2, legend="LM", line_width=3, line_color="Red", line_alpha=0.6)

plot3.line("x","y", source=source, legend="IS", line_width=3, line_color="Green", line_alpha=0.6)
plot3.line("x","y", source=source2, legend="LM", line_width=3, line_color="Red", line_alpha=0.6)

#Os wspolrzednych i tooltip na mouse hover
tooltips = [("(x,y)", "($x,$y)")]
hover = HoverTool(tooltips=tooltips, mode='vline')
#INTERAKCJA - hover
#https://bokeh.pydata.org/en/latest/docs/user_guide/tools.html#basic-tooltips
for plotobj in [plot, plot2, plot3]:
    plotobj.renderers.extend([Span(location=0, dimension='height', line_color='black', line_width=1), Span(location=0, dimension='width', line_color='black', line_width=1)])
    plotobj.add_tools(hover) 

#Dodatkowy test
# sometext = Title(text=create_equation(), align="center")
# plot.add_layout(sometext, "below")

# Widgety - interackcja
#Bokeh nie ma float input - mozliwe bledy bez castowania
c_const_input = TextInput(title="Stała A - Wydatki autonomiczne", value=str(round(c_const_value,2)))
c_y_input = Slider(title="Funkcja Konsumpcji", value=c_y_value, start=0, end=1.0, step=0.1)
i_i_input = Slider(title="b", value=i_i_value, start=0, end=100.0, step=1)
i_const_input = TextInput(title="Stała inwestycji", value=str(round(i_const_value,2)))
g_input = TextInput(title="Wydatki Rządowe", value=str(round(g_value,2)))
tax_input = Slider(title="Podatki (funkcja uzalezniona od Y)", value=tax_value, start=0, end=1.0, step=0.1)
taxcon_input = TextInput(title="Podatki", value=str(round(tax_constant,2)))

#WIDGETY LM
prod_money_coeff_input = Slider(title="Funkcja Y - popyt konsumpc na pieniadz", value=prod_money_coeff, start=0, end=1.0, step=0.1)
money_constant_input = TextInput(title="Stały popyt - minumum", value=str(round(money_constant,2)))
i_prod_money_coeff_input = TextInput(title="Funkcja inwestycji", value=str(round(i_prod_money_coeff,2)))
money_supply_input = TextInput(title="Podaz Pieniadza M/P", value=str(round(money_supply,2)))

#Divy z tekstem
div = Div(text=escape_to_latex(static_is_div_test.format(main_equation = create_equation(), c_const=c_const_value, c_y=c_y_value, 
    i_const = i_const_value , i_i= i_i_value, tax_value = tax_value, g_value = g_value, tax_constant = tax_constant).replace("<br>", "\\\\ ")),
width=800, height=300)

div2 = Div(text=escape_to_latex(static_lm_div_test.format(prod_money_coeff = prod_money_coeff, money_constant = money_constant, i_prod_money_coeff = i_prod_money_coeff, money_supply = money_supply).replace("<br>", "\\\\ ")),
width=800, height=300)

static_resources_text = """
<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"> </script>
<script type="text/x-mathjax-config">
MathJax.Hub.Config({
  TeX: {
     equationNumbers: {  autoNumber: "AMS"  },
     extensions: ["AMSmath.js", "AMSsymbols.js", "autobold.js", "color.js"],
     inlineMath: [['$$','$$'], ['\\(','\\)']]
  }
});
"""
static_div = Div(width=0, height=0, text =static_resources_text)


# Callbacki - definiowane sa de facto jak w JavaScripcie - 
#czyli dzialaja jak dodamy je do on_change obiektów dopiero, nazwa funkcji nie jest wazna, odnosimy sie do niej tylko przy on_change
def update_data(attrname, old, new):
    # Wartości sliderów
    c_const_value = float(c_const_input.value)
    i_const_value = float(i_const_input.value)
    c_y_value = float(c_y_input.value)
    i_i_value = float(i_i_input.value)
    g_value = float(g_input.value)
    tax_value = float(tax_input.value)
    tax_constant = float(taxcon_input.value)

    prod_money_coeff = float(prod_money_coeff_input.value)
    money_constant = float(money_constant_input.value)
    i_prod_money_coeff = float(i_prod_money_coeff_input.value)
    money_supply = float(money_supply_input.value)

    # Update source.data w efekcie generuje nowy wykres
    x,y = generate_x_and_y_islm(c_y_value, c_const_value, i_i_value, i_const_value, g_value, tax_value, tax_constant)
    x_2,y_2 = generate_x_and_y_lm(prod_money_coeff, money_constant, i_prod_money_coeff, money_supply)

    source.data = dict(x=x, y=y)
    source2.data = dict(x=x_2, y=y_2)

    div.text = escape_to_latex(static_is_div_test.format(main_equation = create_equation(), c_const=c_const_value, c_y=c_y_value, 
        i_const = i_const_value , i_i= i_i_value, tax_value = tax_value, g_value = g_value, tax_constant = tax_constant).replace("<br>", "\\\\ "))

    div2.text = escape_to_latex(static_lm_div_test.format(prod_money_coeff = prod_money_coeff, money_constant = money_constant, 
    i_prod_money_coeff = i_prod_money_coeff, money_supply = money_supply).replace("<br>", "\\\\ "))

#TODO based on https://bokeh.pydata.org/en/latest/docs/user_guide/interaction/callbacks.html#customjs-for-user-interaction-events
js_latexize_code = """
div2_value = div2.innerHTML;
MathJax.Hub.Queue(["Typeset",MathJax.Hub,div2_value]);
div_value = div.innerHTML;
MathJax.Hub.Queue(["Typeset",MathJax.Hub,div_value]);
""".replace("/","&#92")

for w in [c_y_input, c_const_input, i_const_input, i_i_input, g_input, tax_input, taxcon_input, prod_money_coeff_input, money_constant_input, i_prod_money_coeff_input, money_supply_input]:
    w.on_change('value', update_data)
    w.js_on_change('value', CustomJS(args=dict(div = div, div2 = div2),code=js_latexize_code))
    #Nie można tu wykorzystać texa ani nic podobnego, wszystkie dynamiczne rzeczy muszą odbywać się w kodzie JS w js_code.
    # Dzialanie nie do konca takie jak trzeba - Text nie moze miec on_change listenera...

# Grupowanie widgetów i layout
widgets = widgetbox(c_y_input, c_const_input, i_const_input, i_i_input, g_input, tax_input, taxcon_input, width=150)
widgets2 = widgetbox(prod_money_coeff_input, money_constant_input, i_prod_money_coeff_input, money_supply_input, width=150)
complex_layout = layout([
  [widgets, plot],
  [div],
  [widgets2, plot2],
  [div2],
  [plot3]
], sizing_mode='fixed')


# Bugi oparte na plotrender - https://groups.google.com/a/continuum.io/forum/#!msg/bokeh/_-m57q6JIMo/rgAXOBuwAwAJ
for plotobj in [plot, plot2, plot3]:
    for event in [events.MouseWheel, events.LODEnd, events.ButtonClick]:
        plotobj.js_on_event(event,CustomJS(args=dict(div = div, div2 = div2),code=js_latexize_code))

#Finalne tworzenie dokumentu, który może zostać serwowany w serwerze
js_resources = INLINE.render_js()
css_resources = INLINE.render_css()
templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "index.html"
template = templateEnv.get_template(TEMPLATE_FILE)

curdoc().template = template
curdoc().template_variables["js_resources"] = js_resources
curdoc().template_variables["css_resources"] = css_resources
curdoc().add_root(complex_layout)
curdoc().title = "Model IS-LM"
curdoc().theme = Theme(filename="theme.yaml")

