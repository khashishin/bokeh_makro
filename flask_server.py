import numpy as np
from flask import Flask, render_template

from bokeh.embed import server_document
from bokeh.layouts import column, row, widgetbox
from bokeh.models import ColumnDataSource, Slider,  TextInput, CustomJS
from bokeh.client import pull_session
from bokeh.embed import server_session
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.io import curdoc
from bokeh.resources import INLINE

from sympy import *

import math

app = Flask(__name__)
#Defnicja Javascriptowych zrodel dla bokeh
js_resources = INLINE.render_js()
css_resources = INLINE.render_css()

def create_visualization(doc):
    # Set up data
    #Definicja źródła danych, które generujemy numerycznie
    N = 200 # Liczba "numerycznie" wygenerowanych punktów - monte carlo
    my_range = 20 # Max wartosc X, ogranicza też widok Y i chwiliwo na jej podstawie tworzy się Ujemna, idaca w dol IS
    x = np.linspace(0, my_range, N)
    y = [math.pow(i, 1) for i in x]
    y2 = [my_range - math.pow(j,1) for j in x]
    source = ColumnDataSource(data=dict(x=x, y=y))
    source2 = ColumnDataSource(data=dict(x=x, y=y2))

    # Tworzenie wykresu - sam wykres jest nieinteraktywny
    plot = figure(plot_height=800, plot_width=600, title="",
                  x_range=[0, my_range], y_range=[0, my_range], tools="pan,wheel_zoom", active_scroll="wheel_zoom", toolbar_location="below",
                   x_axis_label='IS', y_axis_label='LM')
    #https://bokeh.pydata.org/en/latest/docs/user_guide/quickstart.html

    #LEGENDA
    plot.line("x","y", source=source, legend="IS", line_width=3, line_color="Green", line_alpha=0.6)
    plot.line("x","y", source=source2, legend="LM", line_width=3, line_color="Red", line_alpha=0.6)

    # Widgety - interackcja
    #Bokeh nie ma float input - mozliwe bledy bez castowania
    potega = Slider(title="potega IS", value=1.0, start=0, end=5.0, step=0.1)
    wartosc = TextInput(title="wartosc IS", value="1.0")
    potega2 = Slider(title="potega LM", value=1.0, start=0, end=5.0, step=0.1)
    wartosc2 = TextInput(title="wartosc LM", value="1.0")
    # Callbacki - definiowane sa de facto jak w JavaScripcie - 
    #czyli dzialaja jak dodamy je do on_change obiektów dopiero, nazwa funkcji nie jest wazna, odnosimy sie do niej tylko przy on_change
    
    def update_data(attrname, old, new):
        # Wartości sliderów
        import math
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
        source.data = dict(x=x, y=y)
        source2.data = dict(x=x, y=y2)

        #Próba zmiany DIV na stronie
        # session = pull_session(url='http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
        # div = session.document.select_one({"id": "dynamic_equation"})
        # div.value = "TEST"

    #TODO based on https://bokeh.pydata.org/en/latest/docs/user_guide/interaction/callbacks.html#customjs-for-user-interaction-events
    # js_code = """
    # doc = document.getElementById("dynamic_equation");
    # doc.textContent = potega.value;
    # """

    for w in [potega, wartosc, potega2, wartosc2]:
        w.on_change('value', update_data)
        #Nie można tu wykorzystać texa ani nic podobnego, wszystkie dynamiczne rzeczy muszą odbywać się w kodzie JS w js_code.
        # w.js_on_change('value', CustomJS(args=dict(potega=potega, wartosc=wartosc, potega2=potega2, wartosc2=wartosc2),code=js_code))

    # Grupowanie widgetów i layout
    widgets = widgetbox(potega, wartosc, potega2, wartosc2)
    layout = row(widgets, plot, width=400, height = 400 )

    #Finalne tworzenie dokumentu, który może zostać serwowany w serwerze
    doc.add_root(layout)
    doc.title = "Sliders"
    doc.theme = Theme(filename="theme.yaml")

def create_equation():
    equation = "C = \\bar{C} + cY_d = \\bar{C} + c(Y-T), \space \\frac{\delta C}{\delta Y_d}"
    equation_text = "\({}\)".format(equation)
    return equation_text

def change_visuals_for_page(session):
    #Ten element można wykorzystać do dodawnia elementów do strony - nie wiem czy są inne selektory niż children.
    session.document.roots[0].children[1].title.text = "Przykład dodania elementu do generowanej sesji strony"
    return session

def calculate_value(val1,val2,val3,val4):
    val = val1+val2+val3+val4
    return round(val,2)

main_server_port = 8000
bokeh_plot_server_1_port = "5006"
application_link = "/bkapp"
@app.route('/', defaults={'name': ''})
@app.route('/<string:name>', methods=['GET']) 
#Przekazujemy prosty parametr tekstowy - dla czytelnosci że się da i działa, tutaj nie można umieszczać nic 
#To co tutaj jest dotyczy zachowania aplikcji po wpisaniu /<string>

#To jest aplikacja kliencka Bokeha ktora laczy sie z serwerem w bk_server_worker
def bkapp_page(name):
    session = pull_session(url='http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
    session = change_visuals_for_page(session)
    session.push()
    script = server_session(None, session.id, url='http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
    return render_template("embed_flask.html", name=name, script=script, js_resources=js_resources, css_resources=css_resources, template="Flask", 
        static_math_expression = create_equation())

    #Startujemy serwer i odpowiednie wątki, tak żeby odświeżać nasz dokument
def bk_server_worker():
    server = Server({application_link: create_visualization}, allow_websocket_origin=["127.0.0.1:{}".format(main_server_port), "localhost:{}".format(main_server_port)]) 
    # UWAGA - Tylko 1 origin (1 watek) moze miec dostep do aktualizujacego sie wykresu, wiec proba dodania np. 5006 do listy i dostania sie przez niego skutkuje nieinteraktywnym wykresem
    #LOKALNY 5006 ["127.0.0.1:{}".format(bokeh_plot_server_1_port), "localhost:{}".format(bokeh_plot_server_1_port)]
    #Na serwerze 8000 ["127.0.0.1:{}".format(main_server_port), "localhost:{}".format(main_server_port)]
    server.start()
    try:
        server.io_loop.start()
    except KeyboardInterrupt:
        server.io_loop.stop()

if __name__ == '__main__':
    print ("Running bokeh server...")
    from threading import Thread
    server_thread = Thread(target=bk_server_worker)
    server_thread.start()

    print ("Openning application on http://localhost:{}{}".format(bokeh_plot_server_1_port,application_link))
    print ("Openning server on http://localhost:{}".format(main_server_port))
    app.run(port=main_server_port, debug=False)