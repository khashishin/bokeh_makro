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

def modify_doc(doc):
    #Definicja źródła danych, które generujemy numerycznie
    N = 200
    x = np.linspace(0, 4*np.pi, N)
    y = np.sin(x)
    source = ColumnDataSource(data=dict(x=x, y=y))

    # Tworzenie wykresu - sam wykres jest nieinteraktywny
    plot = figure(plot_height=200, plot_width=400, title="",
                  x_range=[0, 4*np.pi], y_range=[-2.5, 2.5])

    plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)

    # Widgety - interackcja
    offset = Slider(title="offset", value=0.0, start=-5.0, end=5.0, step=0.1)
    amplitude = Slider(title="amplitude", value=1.0, start=-5.0, end=5.0, step=0.1)
    phase = Slider(title="phase", value=0.0, start=0.0, end=2*np.pi)
    freq = Slider(title="frequency", value=1.0, start=0.1, end=5.1, step=0.1)
    plot.renderers.extend([Span(location=0, dimension='height', line_color='black', line_width=1), Span(location=0, dimension='width', line_color='black', line_width=1)])

    # Callbacki - definiowane sa de facto jak w JavaScripcie - 
    #czyli dzialaja jak dodamy je do on_change obiektów dopiero, nazwa funkcji nie jest wazna, odnosimy sie do niej tylko przy on_change
    def update_data(attrname, old, new):
        # Wartości sliderów
        amplitude_value = amplitude.value
        offset_value = offset.value
        phase_value = phase.value
        freq_value = freq.value

        # Update source.data w efekcie generuje nowy wykres
        x = np.linspace(0, 4*np.pi, N)
        y = amplitude_value*np.sin(freq_value*x + phase_value) + offset_value
        source.data = dict(x=x, y=y)

        #Próba zmiany DIV na stronie
        # session = pull_session(url='http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
        # div = session.document.select_one({"id": "dynamic_equation"})
        # div.value = "TEST"


    #TODO based on https://bokeh.pydata.org/en/latest/docs/user_guide/interaction/callbacks.html#customjs-for-user-interaction-events
    # js_code = """
    # doc = document.getElementById("dynamic_equation");
    # doc.textContent = "{}";
    # """

    for w in [offset, amplitude, phase, freq]:
        w.on_change('value', update_data)
        #Nie można tu wykorzystać texa ani nic podobnego, wszystkie dynamiczne rzeczy muszą odbywać się w kodzie JS w js_code.
        # static_equation = create_equation()
        # w.js_on_change('value', CustomJS(args=dict(amplitude=amplitude, offset=offset, phase=phase, freq=freq),code=js_code.format(static_equation)))

    # Grupowanie widgetów i layout
    widgets = widgetbox(offset, amplitude, phase, freq)
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
    from threading import Thread
    server_thread = Thread(target=bk_server_worker)
    server_thread.start()
    script = server_document('http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
    # PRZYKLAD SERVER SESSION NIE DZIAŁA POPRAWNIE Z AKTUALIZACJA WYRKESU
    # session = pull_session(url='http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
    # session = change_visuals_for_page(session)
    # session.push()
    # script = server_session(None, session.id, url='http://localhost:{}{}'.format(bokeh_plot_server_1_port,application_link))
    return render_template("embed_flask.html", name=name, script=script, js_resources=js_resources, css_resources=css_resources, template="Flask", 
        static_math_expression = create_equation())

    #Startujemy serwer i odpowiednie wątki, tak żeby odświeżać nasz dokument
def bk_server_worker():
    server = Server({application_link: modify_doc}, allow_websocket_origin=["127.0.0.1:{}".format(main_server_port), "localhost:{}".format(main_server_port) ])
    server.start()
    server.io_loop.start()

if __name__ == '__main__':
    print ("Running bokeh server...")
    print ("Openning application on http://localhost:{}{}".format(bokeh_plot_server_1_port,application_link))
    print ("Openning server on http://localhost:{}".format(main_server_port))
    app.run(port=main_server_port, debug=False)


