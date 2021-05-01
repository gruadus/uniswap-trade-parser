import dash_html_components as html
import pandas as pd
import dash_core_components as dcc
import plotly.graph_objs as go
import dash

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

df = pd.read_csv('data.csv')

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df.date,
    y=df.price,
    name="price per trade",
))

app.layout = html.Div(children=[

    dcc.Graph(
        id='price',
        figure=fig,
        style={'height': '1000px', 'width': '2000px'}
    ),

],
)

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=True)
