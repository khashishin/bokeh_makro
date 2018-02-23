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

def create_visualization(doc):
    # Set up data
    #Definicja źródła danych, które generujemy numerycznie
    N = 1000 # Liczba "numerycznie" wygenerowanych punktów - monte carlo
    my_range = 20 # Max wartosc X, ogranicza też widok Y i chwiliwo na jej podstawie tworzy się Ujemna, idaca w dol IS
    x = np.linspace(0, my_range, N)
    y = [math.pow(i, 1) for i in x]
    y2 = [my_range - math.pow(j,1) for j in x]
    y3 = [-el+my_range for el in y2]
    source = ColumnDataSource(data=dict(x=x, y=y))
    source2 = ColumnDataSource(data=dict(x=x, y=y2))
    source_plot2 = ColumnDataSource(data=dict(x=x, y=y3))

    # Tworzenie wykresu - sam wykres jest nieinteraktywny
    #https://bokeh.pydata.org/en/latest/docs/user_guide/quickstart.html
    plot = figure(plot_height=800, plot_width=600, title="",
                  x_range=[0, my_range], y_range=[0, my_range], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above",
                   x_axis_label='IS', y_axis_label='LM')

    plot2 = figure(plot_height=800, plot_width=600, title="",
                  x_range=[0, my_range], y_range=[0, my_range], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="above")

    #Wykresy danych
    plot.line("x","y", source=source, legend="IS", line_width=3, line_color="Green", line_alpha=0.6)
    plot.line("x","y", source=source2, legend="LM", line_width=3, line_color="Red", line_alpha=0.6)
    plot2.line("x","y", source=source_plot2, legend="test", line_width=3, line_color="Blue", line_alpha=0.6)
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
    potega = Slider(title="potega IS", value=1.0, start=0, end=5.0, step=0.1)
    wartosc = TextInput(title="wartosc IS", value="1.0")
    potega2 = Slider(title="potega LM", value=1.0, start=0, end=5.0, step=0.1)
    wartosc2 = TextInput(title="wartosc LM", value="1.0")
    # Callbacki - definiowane sa de facto jak w JavaScripcie - 
    #czyli dzialaja jak dodamy je do on_change obiektów dopiero, nazwa funkcji nie jest wazna, odnosimy sie do niej tylko przy on_change
    
    div = Div(text="""Your <a href="https://en.wikipedia.org/wiki/HTML">HTML</a>-supported text is initialized with the <b>text</b> argument.  The
    remaining div arguments are <b>width</b> and <b>height</b>. For this example, those values
    are <i>200</i> and <i>100</i> respectively.""",
    width=400, height=300)

    def update_data(attrname, old, new):
        # Wartości sliderów
        potega_value = potega.value
        potega2_value = potega2.value
        try:
            wartosc_value = float(wartosc.value)
        except ValueError:
            wartosc_value = 1.0
        try:
            wartosc2_value = float(wartosc2.value)
        except ValueError:
            wartosc2_value = 1.0

        # Update source.data w efekcie generuje nowy wykres
        x = np.linspace(0, my_range, N)
        y = [math.pow(wartosc_value*i, potega_value) for i in x]
        y2 = [my_range - math.pow(wartosc2_value*j,potega2_value) for j in x]
        y3 = [-el+my_range for el in y2]

        source.data  =dict(x=x, y=y)
        source2.data = dict(x=x, y=y2)
        source_plot2.data = dict(x=x, y=y3)

        random_number = generate_text()

        sometext.text = random_number
        div.text = "$$"+ random_number +"$$"

    #TODO based on https://bokeh.pydata.org/en/latest/docs/user_guide/interaction/callbacks.html#customjs-for-user-interaction-events
    js_latexize_code = """
    div_value = div.innerHTML;
    MathJax.Hub.Queue(["Typeset",MathJax.Hub,div_value]);
    """.replace("/","&#92")

    for w in [potega, wartosc, potega2, wartosc2]:
        w.on_change('value', update_data)
        #Nie można tu wykorzystać texa ani nic podobnego, wszystkie dynamiczne rzeczy muszą odbywać się w kodzie JS w js_code.
        # Dzialanie nie do konca takie jak trzeba - Text nie moze miec on_change listenera...
        w.js_on_change('value', CustomJS(args=dict(div = div),code=js_latexize_code))
    
    # Grupowanie widgetów i layout
    widgets = widgetbox(potega, wartosc, potega2, wartosc2, width=150)
    # layout = row(widgets, plot, plot2, width=400, height = 400)
    complex_layout = layout([
      [widgets, plot, plot2],
      [div],
    ], sizing_mode='fixed')
    #Finalne tworzenie dokumentu, który może zostać serwowany w serwerze
    doc.add_root(complex_layout)
    doc.title = "Sliders"
    doc.theme = Theme(filename="theme.yaml")

def create_equation():
    equation = "C = \\bar{C} + cY_d = \\bar{C} + c(Y-T), \space \\frac{\delta C}{\delta Y_d}"
    equation_text = "\({}\)".format(equation)
    return equation_text

def generate_text():
    # return "C = \\bar{C} + cY_d = \\bar{C} + c(Y-T), \space \\frac{\delta C}{\delta Y_d}"
    return str(random.randint(1, 500))  

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