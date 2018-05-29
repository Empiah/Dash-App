import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objs as go

app = dash.Dash()

df = pd.read_csv('Data/results.csv')
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year
df = df[df['date'].dt.year >= 1975]

available_indicators_home = np.sort(df['home_team'].unique())
available_indicators_away = np.sort(df['away_team'].unique())

app.layout = html.Div([
        html.Div([

            html.Div([
                dcc.Dropdown(
                    id='xaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators_home],
                    value='England'
                ),
            ],
            style={'width': '49%', 'display': 'inline-block'}),

            html.Div([
                dcc.Dropdown(
                    id='yaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators_away],
                    value='Italy'
                ),
            ],
            style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
        ], style={
            'borderBottom': 'thin lightgrey solid',
            'backgroundColor': 'rgb(250, 250, 250)',
            'padding': '10px 5px'
    }),

        html.Div(dcc.Slider(
            id='year-slider',
            min=df['year'].min(),
            max=df['year'].max(),
            value=df['year'].max(),
            step=None,
            marks={str(year): str(year) for year in df['year'].unique()}
        ), style={'width': '98%', 'padding': '0px 20px 20px 20px'}),

        html.Div([
            dcc.Graph(
            id='basic-interactions',
            hoverData={'points': [{'customdata':'England'}]}
            )
        ], style={'width': '98%', 'display': 'inline-block', 'padding': '0 20'})
])

@app.callback(
    dash.dependencies.Output('basic-interactions', 'figure'),
    [dash.dependencies.Input('xaxis-column', 'value'),
     dash.dependencies.Input('yaxis-column', 'value'),
     dash.dependencies.Input('year-slider', 'value')])

def update_graph(xaxis_column_name, yaxis_column_name,
                 year_value):
    dff = df[df['year'] == year_value]

    return {
        'data': [go.Scatter(
            x=dff[dff['home_team'] == xaxis_column_name]['home_score'],
            y=dff[dff['away_team'] == yaxis_column_name]['away_score'],
            text=dff[dff['away_team'] == yaxis_column_name]['date'],
            customdata=dff[dff['away_team'] == yaxis_column_name]['date'],
            mode='markers',
            marker={
                'size': 15,
                'opacity': 0.5,
                'line': {'width': 0.5, 'color': 'white'}
            }
        )],
        'layout': go.Layout(
            xaxis={
                'title': xaxis_column_name,
            },
            yaxis={
                'title': yaxis_column_name
            },
            margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
            height=450,
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server()
