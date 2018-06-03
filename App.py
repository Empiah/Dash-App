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

conditions = [
    (df['home_score'] == df['away_score']),
    (df['home_score'] > df['away_score']),
    (df['home_score'] < df['away_score'])]
choices = ['D', 'H', 'A']
df['result'] = np.select(conditions, choices)

available_indicators_home = np.sort(df['home_team'].unique())
available_indicators_away = ['Home', 'Away']
#available_indicators_away = np.sort(df['away_team'].unique())

app.layout = html.Div([
        html.Div([

            html.Div([
                dcc.Dropdown(
                    id='xaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators_home],
                    value='England'
                ),
            ],
            style={'width': '75%', 'display': 'inline-block'}),

            html.Div([
                dcc.Dropdown(
                    id='yaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators_away],
                    value='Home'
                ),
            ],
            style={'width': '23%', 'float': 'right', 'display': 'inline-block'})
        ], style={
            'borderBottom': 'thin lightgrey solid',
            'backgroundColor': 'rgb(250, 250, 250)',
            'padding': '10px 5px'
    }),
        html.Div(dcc.Slider(
            id='year',
            min=df['year'].min(),
            max=df['year'].max(),
            value=df['year'].max(),
            step=None,
            marks={str(year): str(year) for year in df['year'].unique()}
        ), style={'width': '98%', 'padding': '0px 20px 20px 20px'}),

        html.Div([
            dcc.Graph(
            id='result_scatter',
            hoverData={'points': [{'customdata':'England'}]}
            )
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
        html.Div([
            dcc.Graph(id='x-time-series'),
            dcc.Graph(id='y-time-series'),
        ], style={'display': 'inline-block', 'width': '49%'})
])

@app.callback(
    dash.dependencies.Output('result_scatter', 'figure'),
    [dash.dependencies.Input('xaxis-column', 'value'),
     dash.dependencies.Input('yaxis-column', 'value'),
     dash.dependencies.Input('year', 'value')])

def update_graph(xaxis_column_name, yaxis_column_name,
                 year_value):

    dff = df[df['year'] == year_value]

    while True:
        if yaxis_column_name == 'Home':
            goal1 = dff[dff['home_team'] == xaxis_column_name]['home_score']
            goal2 = dff.loc[dff['home_team'] == xaxis_column_name, 'away_score']
            name = dff[dff['home_team'] == xaxis_column_name]['away_team']
            custom = dff[dff['home_team'] == yaxis_column_name]['away_team']
            break

        else:
            goal1 = dff[dff['away_team'] == xaxis_column_name]['away_score']
            goal2 = dff.loc[dff['away_team'] == xaxis_column_name, 'home_score']
            name = dff[dff['away_team'] == xaxis_column_name]['home_team']
            custom = dff[dff['away_team'] == yaxis_column_name]['home_team']
            break

    """
    if int(goal1) > int(goal2):
        color_dots = 'green'
    elif int(goal1) == int(goal2):
        color_dots = 'blue'
    else:
        color_dots = 'red'
    """


    return {
        'data': [go.Scatter(
            x=goal1,
            y=goal2,
            text=name,
            customdata=custom,
            mode='markers',
            marker=dict(
                size = 15,
                opacity = 0.5,
                color = goal2 - goal1,
                line = dict(width = 0.5, color = 'black'
                )
            )
        )],
        'layout': go.Layout(
            xaxis={
                'title': xaxis_column_name,
            },
            yaxis={
                'title': 'Opponent'
            },
            margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
            height=450,
            hovermode='closest'
        )
    }

def create_time_series(dff, title):
    return {
        'data': [go.Scatter(
            x=dff['year'],
            y=dff['home_score'],
            mode='lines+markers'
        )],
        'layout': {
            'height': 225,
            'margin': {'l': 20, 'b': 30, 'r': 10, 't': 10},
            'annotations': [{
                'x': 0, 'y': 0.85, 'xanchor': 'left', 'yanchor': 'bottom',
                'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                'text': title
            }]
        }
    }


@app.callback(
    dash.dependencies.Output('x-time-series', 'figure'),
    [dash.dependencies.Input('result_scatter', 'hoverData'),
     dash.dependencies.Input('xaxis-column', 'value')])
def update_y_timeseries(hoverData, xaxis_column_name):
    country_name = hoverData['points'][0]['customdata']
    dff = df[df['home_team'] == country_name]
    dff = dff[dff['home_team'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(country_name, xaxis_column_name)
    return create_time_series(dff, title)


@app.callback(
    dash.dependencies.Output('y-time-series', 'figure'),
    [dash.dependencies.Input('result_scatter', 'hoverData'),
     dash.dependencies.Input('xaxis-column', 'value')])
def update_x_timeseries(hoverData, xaxis_column_name):
    country_name = hoverData['points'][0]['customdata']
    dff = df[df['home_team'] == country_name]
    dff = dff[dff['home_team'] == xaxis_column_name]
    title = '<b>{}</b><br>{}'.format(country_name, xaxis_column_name)
    return create_time_series(dff, title)


if __name__ == '__main__':
    app.run_server()
