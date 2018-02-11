import numpy as np
from flask import Flask, render_template

from bokeh.embed import server_document
from bokeh.layouts import column, row, widgetbox
from bokeh.models import ColumnDataSource, Slider,  TextInput
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.resources import INLINE

app = Flask(__name__)

#Defnicja Javascriptowych zrodel biblioteki
js_resources = INLINE.render_js()
css_resources = INLINE.render_css()


def modify_doc(doc):
    #Definicja źródła danych, które generujemy numerycznie
    N = 200
    x = np.linspace(0, 4*np.pi, N)
    y = np.sin(x)
    source = ColumnDataSource(data=dict(x=x, y=y))


    # Tworzenie wykresu - sam wykres jest nieinteraktywny
    plot = figure(plot_height=400, plot_width=400, title="",
                  x_range=[0, 4*np.pi], y_range=[-2.5, 2.5])

    plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)


    # Widgety - interackcja
    offset = Slider(title="offset", value=0.0, start=-5.0, end=5.0, step=0.1)
    amplitude = Slider(title="amplitude", value=1.0, start=-5.0, end=5.0, step=0.1)
    phase = Slider(title="phase", value=0.0, start=0.0, end=2*np.pi)
    freq = Slider(title="frequency", value=1.0, start=0.1, end=5.1, step=0.1)
    # text = TextInput(title="title", value='my sine wave')


    # Callbacki - definiowane sa de facto jak w JavaScripcie - 
    #czyli dzialaja jak dodamy je do on_change obiektów dopiero, funkcja nie jest wazna
    def update_data(attrname, old, new):

        # Get the current slider values
        a = amplitude.value
        b = offset.value
        w = phase.value
        k = freq.value

        # Generate the new curve
        x = np.linspace(0, 4*np.pi, N)
        y = a*np.sin(k*x + w) + b

        source.data = dict(x=x, y=y)

    for w in [offset, amplitude, phase, freq]:
        w.on_change('value', update_data)

    # def update_title(attrname, old, new):
        # plot.title.text = text.value
    # text.on_change('value', update_title)


    # Grupowanie widgetów i layout
    widgets = widgetbox(offset, amplitude, phase, freq)
    layout = row(widgets, plot, width=800)

    #Finalne tworzenie dokumentu, który może zostać serwowany w serwerze
    doc.add_root(layout)
    doc.title = "Sliders"
    doc.theme = Theme(filename="theme.yaml")

application_link = "/bkapp"
@app.route('/<string:name>', methods=['GET']) 
#Przekazujemy prosty parametr tekstowy - dla czytelnosci że się da i działa, tutaj nie można umieszczać nic 
#To co tutaj jest dotyczy zachowania aplikcji po wpisaniu /<string>
def bkapp_page(name):
    script = server_document('http://localhost:5006{}'.format(application_link))
    return render_template("embed_flask.html", name=name, script=script, js_resources=js_resources, css_resources=css_resources, template="Flask")

def bk_worker():
    #Startujemy serwer i odpowiednie wątki, tak żeby odświeżać nasz dokument
    server = Server({application_link: modify_doc}, allow_websocket_origin=["127.0.0.1:8000", "localhost:8000"])
    server.start()
    server.io_loop.start()

from threading import Thread
Thread(target=bk_worker).start()

if __name__ == '__main__':
    print ("Running bokeh server...")
    print ("Openning http://localhost:5006{}".format(application_link))
    app.run(port=8000, debug=True)