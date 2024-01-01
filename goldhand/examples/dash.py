import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import time
from goldhand import *

tw=Tw()
df =tw.stock

# Sample list of names
name_list =  list(df['name'])

# Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='live-update-graph',responsive=True),
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(
    Output('live-update-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n):
    # Get the next name in the list
    ticker = name_list[n % len(name_list)]
    # Get the plot for the next name
    t = GoldHand(ticker)
    fig = t.plot_goldhand_line(plot_title=tw.get_plotly_title(ticker))
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)