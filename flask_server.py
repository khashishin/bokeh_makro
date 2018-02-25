from flask import Flask, render_template
from threading import Thread

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
        """

static_lm_div_test = """ 
        Krzywa \space LM
        <br>
        M_d = M_s
        <br>
        M_d = {money_coeff} Y + {money_constant} - {i_money_coeff} i
        <br>
        M_s = {money_supply}
        """


def generate_x_and_y_islm(y_range, c_y_value, c_const_value, i_i_value, i_const_value, g_value, tax_value, tax_constant):
    N = 1000 # Liczba "numerycznie" wygenerowanych punktów - monte carlo    
    x = np.linspace(0, y_range, N)
    y = [ ((1 / (1 - c_y_value*(1 - tax_value)) ) * (c_const_value+i_const_value+g_value-tax_constant - (i_i_value * i))) for i in x]
    return x,y

def generate_x_and_y_lm(y_range, money_coeff, money_constant, i_money_coeff, money_supply):
    N = 1000 # Liczba "numerycznie" wygenerowanych punktów - monte carlo    
    x = np.linspace(0, y_range, N)    
    y = [ ((( money_coeff * i) / i_money_coeff )  - (  (money_supply - money_constant) / i_money_coeff ) ) for i in x]
    return x,y

def create_visualization(doc):
    c_const_value = 100
    c_y_value = 0.75
    i_const_value = 50
    i_i_value = 25
    g_value = 50
    tax_value = 0.1
    tax_constant = 50

    x_range_is = 10
    y_range_is = 400

    money_coeff = 0.2
    money_constant = 0 
    i_money_coeff = 5
    money_supply = 85

    # Set up data
    #Definicja źródła danych, które generujemy numerycznie
    x, y = generate_x_and_y_islm(y_range_is, c_y_value, c_const_value, i_i_value, i_const_value, g_value, tax_value, tax_constant)
    source = ColumnDataSource(data=dict(x=x, y=y))
    x_2, y_2 = generate_x_and_y_lm(15, money_coeff, money_constant, i_money_coeff, money_supply)
    source2 = ColumnDataSource(data=dict(x=x_2, y=y_2))

    # Tworzenie wykresu - sam wykres jest nieinteraktywny
    #https://bokeh.pydata.org/en/latest/docs/user_guide/quickstart.html
    plot = figure(plot_height=800, plot_width=600, title="Krzywa IS",
                  x_range=[0, x_range_is], y_range=[0, y_range_is], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above",
                   x_axis_label="stopa procentowa i", y_axis_label="Y")

    plot2 = figure(plot_height=800, plot_width=600, title="Krzywa LM",
                  x_range=[0, 10], y_range=[0, 10], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above",
                   x_axis_label="stopa procentowa i", y_axis_label="M/P")

    #Wykresy danych
    plot.line("x","y", source=source, legend="IS", line_width=3, line_color="Green", line_alpha=0.6)
    plot2.line("x","y", source=source2, legend="LM", line_width=3, line_color="Red", line_alpha=0.6)

    #Os wspolrzednych
    plot.renderers.extend([Span(location=0, dimension='height', line_color='black', line_width=1), Span(location=0, dimension='width', line_color='black', line_width=1)])
    plot2.renderers.extend([Span(location=0, dimension='height', line_color='black', line_width=1), Span(location=0, dimension='width', line_color='black', line_width=1)])
    
    #Dodatkowy test
    # sometext = Title(text=create_equation(), align="center")
    # plot.add_layout(sometext, "below")

    #INTERAKCJA - hover
    #https://bokeh.pydata.org/en/latest/docs/user_guide/tools.html#basic-tooltips
    tooltips = [("(x,y)", "($x,$y)")
                        # ,("punkt rownowagi", "1245")]
                        ]
    hover = HoverTool(tooltips=tooltips, mode='vline')
    plot.add_tools(hover) 
    plot2.add_tools(hover)

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
    money_coeff_input = Slider(title="Funkcja Y - popyt konsumpc na pieniadz", value=money_coeff, start=0, end=1.0, step=0.1)
    money_constant_input = TextInput(title="Stały popyt - minumum", value=str(round(money_constant,2)))
    i_money_coeff_input = TextInput(title="Funkcja inwestycji", value=str(round(i_money_coeff,2)))
    money_supply_input = TextInput(title="Podaz Pieniadza Ms", value=str(round(money_supply,2)))

    #Divy z tekstem
    div = Div(text=escape_to_latex(static_is_div_test.format(main_equation = create_equation(), c_const=c_const_value, c_y=c_y_value, 
        i_const = i_const_value , i_i= i_i_value, tax_value = tax_value, g_value = g_value, tax_constant = tax_constant).replace("<br>", "\\\\ ")),
    width=800, height=300)

    div2 = Div(text=escape_to_latex(static_lm_div_test.format(money_coeff = money_coeff, money_constant = money_constant, i_money_coeff = i_money_coeff, money_supply = money_supply).replace("<br>", "\\\\ ")),
    width=800, height=300)


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

        money_coeff = float(money_coeff_input.value)
        money_constant = float(money_constant_input.value)
        i_money_coeff = float(i_money_coeff_input.value)
        money_supply = float(money_supply_input.value)

        # Update source.data w efekcie generuje nowy wykres
        x,y = generate_x_and_y_islm(y_range_is, c_y_value, c_const_value, i_i_value, i_const_value, g_value, tax_value, tax_constant)
        x_2,y_2 = generate_x_and_y_lm(15, money_coeff, money_constant, i_money_coeff, money_supply)

        source.data = dict(x=x, y=y)
        source2.data = dict(x=x_2, y=y_2)

        div.text = escape_to_latex(static_is_div_test.format(main_equation = create_equation(), c_const=c_const_value, c_y=c_y_value, 
            i_const = i_const_value , i_i= i_i_value, tax_value = tax_value, g_value = g_value, tax_constant = tax_constant).replace("<br>", "\\\\ "))

        div2.text = escape_to_latex(static_lm_div_test.format(money_coeff = money_coeff, money_constant = money_constant, 
        i_money_coeff = i_money_coeff, money_supply = money_supply).replace("<br>", "\\\\ "))

    #TODO based on https://bokeh.pydata.org/en/latest/docs/user_guide/interaction/callbacks.html#customjs-for-user-interaction-events
    js_latexize_code = """
    div2_value = div2.innerHTML;
    MathJax.Hub.Queue(["Typeset",MathJax.Hub,div2_value]);
    div_value = div.innerHTML;
    MathJax.Hub.Queue(["Typeset",MathJax.Hub,div_value]);
    """.replace("/","&#92")

    for w in [c_y_input, c_const_input, i_const_input, i_i_input, g_input, tax_input, taxcon_input, money_coeff_input, money_constant_input, i_money_coeff_input, money_supply_input]:
        w.on_change('value', update_data)
        w.js_on_change('value', CustomJS(args=dict(div = div, div2 = div2),code=js_latexize_code))
        #Nie można tu wykorzystać texa ani nic podobnego, wszystkie dynamiczne rzeczy muszą odbywać się w kodzie JS w js_code.
        # Dzialanie nie do konca takie jak trzeba - Text nie moze miec on_change listenera...

    
    # Grupowanie widgetów i layout
    widgets = widgetbox(c_y_input, c_const_input, i_const_input, i_i_input, g_input, tax_input, taxcon_input, width=150)
    widgets2 = widgetbox(money_coeff_input, money_constant_input, i_money_coeff_input, money_supply_input, width=150)
    # layout = row(widgets, plot, plot2, width=400, height = 400)
    complex_layout = layout([
      # [widgets, plot, plot2],
      [widgets, plot],
      [div],
      [widgets2, plot2],
      [div2]
    ], sizing_mode='fixed')
    #Finalne tworzenie dokumentu, który może zostać serwowany w serwerze
    doc.add_root(complex_layout)
    doc.title = "Model IS-LM"
    doc.theme = Theme(filename="theme.yaml")

def create_equation():
    return "C = \\bar{C} + cY_d = \\bar{C} + c(Y-T), \space "

def generate_text():
    return str(random.randint(1, 500))  

def escape_to_latex(text):
    return "$$" +text+ "$$"

app = Flask(__name__)
#Defnicja Javascriptowych zrodel dla bokeh
js_resources = INLINE.render_js()
css_resources = INLINE.render_css()
main_server_port = 8000
bokeh_plot_server_1_port = 9090
application_link = "/bkapp"
@app.route('/', defaults={'name': ''})
@app.route('/<string:name>', methods=['GET']) 
#Przekazujemy prosty parametr tekstowy - dla czytelnosci że się da i działa, tutaj nie można umieszczać nic 
#To co tutaj jest dotyczy zachowania aplikcji po wpisaniu /<string>

#To jest aplikacja kliencka Bokeha ktora laczy sie z serwerem w bk_server_worker
def bkapp_page(name):
    server_thread = Thread(target=bk_server_worker)
    server_thread.start()
    #Startujemy serwer i odpowiednie wątki, tak żeby odświeżać nasz dokument
    script = server_document('http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
    return render_template("embed_flask.html", name=name, script=script, js_resources=js_resources, css_resources=css_resources, template="Flask", 
        static_math_expression = create_equation())

def bk_server_worker():
    server = Server({application_link: create_visualization}, allow_websocket_origin=["127.0.0.1:{}".format(main_server_port), "localhost:{}".format(main_server_port)], port=int(bokeh_plot_server_1_port)) 
    server.start()
    server.io_loop.start()

if __name__ == '__main__':
    print ("Running bokeh server...")
    # print ("Openning bokeh worker server application on http://localhost:{}{}".format(bokeh_plot_server_1_port,application_link))
    print ("Openning single process Flask app with embedded Bokeh application on http://localhost:{}".format(main_server_port))

    app.run(port=main_server_port, debug=False)