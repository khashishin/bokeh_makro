''' Present an interactive function explorer with slider widgets.
Scrub the sliders to change the properties of the ``sin`` curve, or
type into the title text box to update the title of the plot.
Use the ``bokeh serve`` command to run the example by executing:
    bokeh serve sliders.py
at your command prompt. Then navigate to the URL
    http://localhost:5006/sliders
in your browser.
'''
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import row, widgetbox
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import Slider, TextInput, InputWidget
from bokeh.plotting import figure
import math

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


for w in [potega, wartosc, potega2, wartosc2]:
    w.on_change('value', update_data)


# Set up layouts and add to document
inputs = widgetbox(potega, wartosc, potega2, wartosc2)

curdoc().add_root(row(inputs, plot, width=800))
curdoc().title = "Sliders"