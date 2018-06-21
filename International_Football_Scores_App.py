import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.figure_factory as ff

app = dash.Dash()

server = app.server

#import the data into the script
df = pd.read_csv('Data/results.csv')
df_raw = df

#convert the date to datetime, and create a new column showing just the year
df['date'] = pd.to_datetime(df['date'])
df['year'] = df['date'].dt.year

#there is a lot of data so lets remove anything before 1975
df = df[df['date'].dt.year >= 1975]

#what we need to do here is plan for scores that are the sameself.
#to show them all properly, I will add small random value to the columns that hold the scores
#this will mean when you hover over, both will appear

#this adds a column with a random value
df['random'] = np.random.uniform(0.03,0,len(df))

#this copies the original columns
df['home_score1'] = df['home_score']
df['away_score1'] = df['away_score']

#this changes the existing columns and adds the value in the random column
df['home_score'] = df['home_score'] + df['random']
df['away_score'] = df['away_score'] + df['random']

#this will be the list of indicators that are available to select in drop downs
available_indicators_teams = np.sort(df['home_team'].unique())
available_indicators_homeaway = ['Home', 'Away', 'All']
available_indicators_tourny = np.sort(df['tournament'].unique())

#in here we start to define the outline of our app and get it define how it looks
#the order that it is in is how it will appear
#for example if the slider is above the dropdown it will appear above
app.layout = html.Div([
        html.Div([
            #adding a dropdown which we give an id and ask it to use the options we defined above. The 'value' is simply its starting value when you open the app.
            html.Div([
                dcc.Dropdown(
                    id='xaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators_teams],
                    value='England'
                ),
            ],
            #define its width and basic properties of how it looks
            style={'width': '75%', 'display': 'inline-block'}),

            #here we add another dropdown, it utilises the list we created above.
            html.Div([
                dcc.Dropdown(
                    id='yaxis-column',
                    options=[{'label': i, 'value': i} for i in available_indicators_homeaway],
                    value='Home'
                ),
            ],
            style={'width': '23%', 'float': 'right', 'display': 'inline-block'})
           #this style piece is assigning values for both dropdown lists, changing the colour to make it stand out,
        ], style={
            'borderBottom': 'thin lightgrey solid',
            'backgroundColor': 'rgb(250, 250, 250)',
            'padding': '10px 5px'
    }),
        #adding a slider as a nicer way to change the year we look at. We define some details here using the year column we created earlier.
        html.Div(dcc.Slider(
            id='year',
            min=df['year'].min(),
            max=df['year'].max(),
            value=df['year'].max(),
            step=None,
            marks={str(year): str(year) for year in df['year'].unique()}
        ), style={'width': '98%', 'padding': '0px 20px 20px 20px'}),

        #this is the main chart that will show the scores
        html.Div([
            dcc.Graph(
            id='result_scatter',
            hoverData={'points': [{'customdata':'Italy'}]}
            )
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
        #these charts will be on the side and there is two, they will show timeseries dataa
        html.Div([
            dcc.Graph(id='x-time-series'),
            dcc.Graph(id='y-time-series'),
        ], style={'display': 'inline-block', 'width': '49%'}),
        #this is for a table below the data that will additional information
        html.Div([
            dcc.Graph(id='table-data'),
        ], style={'display': 'inline-block', 'width': '98%'}),
        #this will show head to head information
        html.Div([
            dcc.Graph(id='head-to-head'),
        ], style={'display': 'inline-block', 'width': '98%'})
])
#this defines what we want to update (main chart) and what data will update it
@app.callback(
    dash.dependencies.Output('result_scatter', 'figure'),
    [dash.dependencies.Input('xaxis-column', 'value'),
     dash.dependencies.Input('yaxis-column', 'value'),
     dash.dependencies.Input('year', 'value')])
#this function will provide the informat to update the graph
def update_graph(xaxis_column_name, yaxis_column_name,
                 year_value):
    #ensures that the year we are showing matches the year we select
    dff = df[df['year'] == year_value]
    #loop to ascertain whether we are looking at Home or Away data. it assigns values accordingly
    while True:
        if yaxis_column_name == 'Home':
            goal1 = dff[dff['home_team'] == xaxis_column_name]['home_score']
            goal2 = dff.loc[dff['home_team'] == xaxis_column_name, 'away_score']
            name = dff[dff['home_team'] == xaxis_column_name]['away_team']
            custom = dff[dff['home_team'] == xaxis_column_name]['away_team']

            #this will help us create a dynamic diagonal line which will indicate win vs loss
            dff_g1 = dff[dff['home_team'].isin([xaxis_column_name])]
            dff_g2 = dff[dff['away_team'].isin([xaxis_column_name])]
            dff_goals = dff_g1.append(dff_g2, ignore_index=True)
            max_goals_amt = dff_goals[['home_score','away_score']].max(axis=1)
            break

        elif yaxis_column_name == 'All':
            #making two lists of where the selected team is in away or home, and then appending
            dff_1 = dff[dff['home_team'].isin([xaxis_column_name])]
            dff_2 = dff[dff['away_team'].isin([xaxis_column_name])]
            dff = dff_1.append(dff_2, ignore_index=True)

            #making the goals match where the selected team is for home and away, and appending the lists
            goal1 = dff[dff['home_team'] == xaxis_column_name]['home_score'].append(dff[dff['away_team'] == xaxis_column_name]['away_score'], ignore_index=True)
            goal2 = dff.loc[dff['home_team'] == xaxis_column_name, 'away_score'].append(dff.loc[dff['away_team'] == xaxis_column_name, 'home_score'], ignore_index=True)

            #to get the right name we have to do a a few things
            #first we are removing values where it equals the xaxis_column_name
            dff1 = dff[~dff[['home_team', 'away_team']].isin([xaxis_column_name])]

            #then we get all non-null values from both cols (data we want)
            home_null = dff1.loc[dff1['home_team'].notnull(), ['home_team']]
            away_null = dff1.loc[dff1['away_team'].notnull(), ['away_team']]

            #we then append to each other and fill the na values, custom is the same as name
            non_null = away_null.append(home_null, ignore_index = True)
            name = non_null['home_team'].fillna(non_null['away_team'])
            custom = name

            #this will help us create a dynamic diagonal line which will indicate win vs loss
            max_goals_amt = dff[['home_score','away_score']].max(axis=1)
            break
        else:
            goal1 = dff[dff['away_team'] == xaxis_column_name]['away_score']
            goal2 = dff.loc[dff['away_team'] == xaxis_column_name, 'home_score']
            name = dff[dff['away_team'] == xaxis_column_name]['home_team']
            custom = dff[dff['away_team'] == xaxis_column_name]['home_team']

            #this will help us create a dynamic diagonal line which will indicate win vs loss
            dff_g1 = dff[dff['home_team'].isin([xaxis_column_name])]
            dff_g2 = dff[dff['away_team'].isin([xaxis_column_name])]
            dff_goals = dff_g1.append(dff_g2, ignore_index=True)
            max_goals_amt = dff_goals[['home_score','away_score']].max(axis=1)
            break



    title_1 = '<b>Score Matrix showing {} games for {}</b><br> Change the dropdown\'s above to modify the data shown'.format(yaxis_column_name, xaxis_column_name)
    #here, the return will return the plot we are looking for
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
        #this gives information about more visual layouts like the hovermode and the title
        #the hovermode is basically the datapoint for what we are hovering over
        'layout': go.Layout(
            xaxis={
                'title': xaxis_column_name,
                'hoverformat' : '.0f'
            },
            yaxis={
                'title': 'Opponent',
                'hoverformat' : '.0f'
            },
            margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
            height=450,
            hovermode='closest',
            annotations =    [{ 'x': 0, 'y': 0.95, 'xanchor': 'left', 'yanchor': 'bottom',
                            'xref': 'paper', 'yref': 'paper', 'showarrow': False,
                            'align': 'left', 'bgcolor': 'rgba(255, 255, 255, 0.5)',
                            'text': title_1 }],
            shapes = [{
            'type': 'line',
            'x0': 0,
            'y0': 0,
            'x1': max_goals_amt.max(),
            'y1': max_goals_amt.max(),
            'line': {
                'color': 'rgb(180, 180, 180)',
                'width': 4,
                'dash': 'dashdot',
            },
        }]

        )
    }
#this function creates one of the timeseries graphs
def create_time_series_x(dff, dff_two, title, yaxis_column_name, xaxis_column_name, country_name):
    #loop to ascertain whether we are looking at Home or Away data. it assigns values accordingly
    while True:
        if yaxis_column_name == 'Home':
            goal1 = dff_two[dff_two['home_team'] == country_name]['home_score']
            goal2 = dff_two.loc[dff_two['home_team'] == country_name, 'away_score']
            name = dff_two[dff_two['home_team'] == country_name]['away_team']
            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break

        elif yaxis_column_name == 'All':
            #making two lists of where the selected team is in away or home, and then appending
            dff_1 = dff_two[dff_two['home_team'].isin([country_name])]
            dff_2 = dff_two[dff_two['away_team'].isin([country_name])]
            dff = dff_1.append(dff_2, ignore_index=True)
            dff = dff.sort_values('date')

            #making the goals match where the selected team is for home and away, and appending the lists
            goal1 = dff[dff['home_team'] == country_name][['home_score','date']].append(dff[dff['away_team'] == country_name][['away_score','date']], ignore_index=True)
            goal2 = dff.loc[dff['home_team'] == country_name, ('away_score','date')].append(dff.loc[dff['away_team'] == country_name, ('home_score','date')], ignore_index=True)

            #sortig the values by date
            goal1 = goal1.sort_values('date')
            goal2 = goal2.sort_values('date')

            #filling na's to make it into a series
            goal1 = goal1['away_score'].fillna(goal1['home_score'])
            goal2 = goal2['away_score'].fillna(goal2['home_score'])

            #to get the right name we have to do a a few things
            #first we are removing values where it equals the xaxis_column_name
            dff1 = dff[~dff[['home_team', 'away_team', 'date']].isin([country_name])]

            #then we get all non-null values from both cols (data we want)
            home_null = dff1.loc[dff1['home_team'].notnull(), ('home_team','date')]
            away_null = dff1.loc[dff1['away_team'].notnull(), ('away_team','date')]

            #we then append to each other and fill the na values, custom is the same as name
            non_null = away_null.append(home_null, ignore_index = True)
            non_null = non_null.sort_values('date')
            name = non_null['home_team'].fillna(non_null['away_team'])

            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break
        else:
            goal1 = dff_two[dff_two['away_team'] == country_name]['away_score']
            goal2 = dff_two.loc[dff_two['away_team'] == country_name, 'home_score']
            name = dff_two[dff_two['away_team'] == country_name]['home_team']
            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break
    #this returns the graph we are looking for
    return {
        'data': [go.Scatter(
            x=dff['date'],
            y=goal_net,
            text=name,
            mode='lines+markers',
            marker=dict(
                size = 8,
                opacity = 0.9,
                color = goal_colour,
                line = dict(width = 0.5, color = 'black'
                )
            )
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
#this is the same as the above but for the other time series graph
#it shows the same information but for th other team
def create_time_series_y(dff, dff_two, title, yaxis_column_name, xaxis_column_name):
    #loop to ascertain whether we are looking at Home or Away data. it assigns values accordingly
    while True:
        if yaxis_column_name == 'Home':
            goal1 = dff_two[dff_two['home_team'] == xaxis_column_name]['home_score']
            goal2 = dff_two.loc[dff_two['home_team'] == xaxis_column_name, 'away_score']
            name = dff_two[dff_two['home_team'] == xaxis_column_name]['away_team']
            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break

        elif yaxis_column_name == 'All':
            #making two lists of where the selected team is in away or home, and then appending
            dff_1 = dff_two[dff_two['home_team'].isin([xaxis_column_name])]
            dff_2 = dff_two[dff_two['away_team'].isin([xaxis_column_name])]
            dff = dff_1.append(dff_2, ignore_index=True)
            dff = dff.sort_values('date')

            #making the goals match where the selected team is for home and away, and appending the lists
            goal1 = dff[dff['home_team'] == xaxis_column_name][['home_score','date']].append(dff[dff['away_team'] == xaxis_column_name][['away_score','date']], ignore_index=True)
            goal2 = dff.loc[dff['home_team'] == xaxis_column_name, ('away_score','date')].append(dff.loc[dff['away_team'] == xaxis_column_name, ('home_score','date')], ignore_index=True)

            #sortig the values by date
            goal1 = goal1.sort_values('date')
            goal2 = goal2.sort_values('date')

            #filling na's to make it into a series
            goal1 = goal1['away_score'].fillna(goal1['home_score'])
            goal2 = goal2['away_score'].fillna(goal2['home_score'])

            #to get the right name we have to do a a few things
            #first we are removing values where it equals the xaxis_column_name
            dff1 = dff[~dff[['home_team', 'away_team', 'date']].isin([xaxis_column_name])]

            #then we get all non-null values from both cols (data we want)
            home_null = dff1.loc[dff1['home_team'].notnull(), ('home_team','date')]
            away_null = dff1.loc[dff1['away_team'].notnull(), ('away_team','date')]

            #we then append to each other and fill the na values, custom is the same as name
            non_null = away_null.append(home_null, ignore_index = True)
            non_null = non_null.sort_values('date')
            name = non_null['home_team'].fillna(non_null['away_team'])

            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break

        else:
            goal1 = dff_two[dff_two['away_team'] == xaxis_column_name]['away_score']
            goal2 = dff_two.loc[dff_two['away_team'] == xaxis_column_name, 'home_score']
            name = dff_two[dff_two['away_team'] == xaxis_column_name]['home_team']
            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break
    #this returns the grah we are looking for
    return {
        'data': [go.Scatter(
            x=dff['date'],
            y=goal_net,
            text=name,
            mode='lines+markers',
            marker=dict(
                size = 8,
                opacity = 0.9,
                color = goal_colour,
                line = dict(width = 0.5, color = 'black'
                )
            )
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

def create_hth(dff, xaxis_column_name, yaxis_column_name, title):
    #loop to ascertain whether we are looking at Home or Away data. it assigns values accordingly

    while True:
        if yaxis_column_name == 'Home':
            goal1 = dff[dff['home_team'] == xaxis_column_name]['home_score']
            goal2 = dff.loc[dff['home_team'] == xaxis_column_name, 'away_score']
            name = dff[dff['home_team'] == xaxis_column_name]['date']
            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break

        elif yaxis_column_name == 'All':
            #making two lists of where the selected team is in away or home, and then appending
            dff_1 = dff[dff['home_team'].isin([xaxis_column_name])]
            dff_2 = dff[dff['away_team'].isin([xaxis_column_name])]
            dff = dff_1.append(dff_2, ignore_index=True)
            dff = dff.sort_values('date')

            #making the goals match where the selected team is for home and away, and appending the lists
            goal1 = dff[dff['home_team'] == xaxis_column_name][['home_score','date']].append(dff[dff['away_team'] == xaxis_column_name][['away_score','date']], ignore_index=True)
            goal2 = dff.loc[dff['home_team'] == xaxis_column_name, ('away_score','date')].append(dff.loc[dff['away_team'] == xaxis_column_name, ('home_score','date')], ignore_index=True)

            #sortig the values by date
            goal1 = goal1.sort_values('date')
            goal2 = goal2.sort_values('date')

            #filling na's to make it into a series
            goal1 = goal1['away_score'].fillna(goal1['home_score'])
            goal2 = goal2['away_score'].fillna(goal2['home_score'])

            name = dff['date']

            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break

        else:
            goal1 = dff[dff['away_team'] == xaxis_column_name]['away_score']
            goal2 = dff.loc[dff['away_team'] == xaxis_column_name, 'home_score']
            name = dff[dff['away_team'] == xaxis_column_name]['date']
            goal_net = goal1-goal2
            goal_colour = goal2-goal1
            break


    #this returns the grah we are looking for
    return {
        'data': [go.Scatter(
            x=dff['date'],
            y=goal_net,
            text=name,
            mode='lines+markers',
            marker=dict(
                size = 8,
                opacity = 0.9,
                color = goal_colour,
                line = dict(width = 0.5, color = 'black'
                )
            )
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


#callback shows what we want to update and the data that will update it
@app.callback(
    dash.dependencies.Output('x-time-series', 'figure'),
    [dash.dependencies.Input('result_scatter', 'hoverData'),
     dash.dependencies.Input('year', 'value'),
     dash.dependencies.Input('yaxis-column', 'value'),
     dash.dependencies.Input('xaxis-column', 'value')])
def update_y_timeseries(hoverData, year_value, yaxis_column_name, xaxis_column_name):
    #this function will update one timeseries graph and feeds it the information to update

    #filter by the year we are looking at
    dff = df[df['year'] == year_value]
    dff_two = df[df['year'] == year_value]

    #filter by the country we are looking at
    country_name = xaxis_column_name

    #another loop to deal with Home vs Away
    while True:
        if yaxis_column_name == 'Home':
            dff = dff[dff['home_team'] == country_name]
            break
        elif yaxis_column_name =='All':
            dff_1 = dff[dff['home_team'].isin([xaxis_column_name])]
            dff_2 = dff[dff['away_team'].isin([xaxis_column_name])]
            dff = dff_1.append(dff_2, ignore_index=True)
            dff = dff.sort_values('date')
            break
        else:
            dff = dff[dff['away_team'] == country_name]
            break
    #giving it a nice adaptive title
    title = '<b>{} {} Results in {}</b><br>Net Goals - Above Zero Equals a Win, Below Equals a Loss'.format(country_name, yaxis_column_name, year_value)
    return create_time_series_y(dff, dff_two, title, yaxis_column_name, xaxis_column_name)


#same as the other chart above, differences have been commented
@app.callback(
    dash.dependencies.Output('y-time-series', 'figure'),
    [dash.dependencies.Input('result_scatter', 'hoverData'),
     dash.dependencies.Input('year', 'value'),
     dash.dependencies.Input('yaxis-column', 'value'),
     dash.dependencies.Input('xaxis-column', 'value')])
def update_x_timeseries(hoverData, year_value, yaxis_column_name, xaxis_column_name):
    dff = df[df['year'] == year_value]
    dff_two = df[df['year'] == year_value]
    #difference here is that we use the hoverdata to select the information that is shown
    #this means that as we move through the graph the info updates
    country_name = hoverData['points'][0]['customdata']

    #filter dataframe based on the axis input
    while True:
        if yaxis_column_name == 'Home':
            dff = dff[dff['home_team'] == country_name]
            break
        elif yaxis_column_name == 'All':
            dff_1 = dff[dff['home_team'].isin([xaxis_column_name])]
            dff_2 = dff[dff['away_team'].isin([xaxis_column_name])]
            dff = dff_1.append(dff_2, ignore_index=True)
            dff = dff.sort_values('date')
            break
        else:
            dff = dff[dff['away_team'] == country_name]
            break

    title = '<b>{} {} Results in {}</b><br>Net Goals - Above Zero Equals a Win, Below Equals a Loss'.format(country_name,yaxis_column_name, year_value)
    return create_time_series_x(dff, dff_two, title, yaxis_column_name, xaxis_column_name, country_name)


@app.callback(
    dash.dependencies.Output('head-to-head', 'figure'),
    [dash.dependencies.Input('result_scatter', 'hoverData'),
     dash.dependencies.Input('xaxis-column', 'value'),
     dash.dependencies.Input('yaxis-column', 'value')])
def update_hth_graph(hoverData, xaxis_column_name, yaxis_column_name):

    country_name = hoverData['points'][0]['customdata']

    #filter the dataframe where the xaxis_column_name and country name is in away or home team
    dff = df_raw[df_raw['home_team'].isin([xaxis_column_name, country_name])]
    dff = dff[dff['away_team'].isin([xaxis_column_name, country_name])]

    #give simple title
    title = '<b>Graph shows {} head to head games for {} versus {}</b><br> A result above 0 shows a win for the user selected team'.format(yaxis_column_name, xaxis_column_name, country_name)

    return create_hth(dff, xaxis_column_name, yaxis_column_name, title)


#finally a table to update that gives more information
@app.callback(
    dash.dependencies.Output('table-data', 'figure'),
    [dash.dependencies.Input('result_scatter', 'hoverData'),
     dash.dependencies.Input('year', 'value'),
     dash.dependencies.Input('yaxis-column', 'value'),
     dash.dependencies.Input('xaxis-column', 'value')])
def update_table_data(hoverData, year_value, yaxis_column_name, xaxis_column_name):
    #this table also uses hoverdata and gives more information about the team selected and the one we hover over
    dff = df[df['year'] == year_value]
    country_name = hoverData['points'][0]['customdata']
    #these columns are not needed so lets remove them
    dff.drop(['neutral', 'year','random', 'home_score', 'away_score'], axis=1, inplace=True)
    #loop to handle Home vs Away
    while True:
        if yaxis_column_name == 'Home':
            dff = dff[dff['home_team'].isin([xaxis_column_name])]
            dff.rename({'home_score1': 'Home Score', 'away_score1': 'Away Score',
                        'date': 'Date', 'home_team': 'Home Team', 'away_team': 'Away Team',
                        'tournament':'Tournament', 'city': 'City', 'country': 'Country'}, axis=1, inplace=True)
            break
        elif yaxis_column_name == 'All':
            dff_1 = dff[dff['home_team'].isin([xaxis_column_name])]
            dff_2 = dff[dff['away_team'].isin([xaxis_column_name])]
            dff = dff_1.append(dff_2, ignore_index=True)
            dff = dff.sort_values('date')
            dff.rename({'home_score1': 'Home Score', 'away_score1': 'Away Score',
                        'date': 'Date', 'home_team': 'Home Team', 'away_team': 'Away Team',
                        'tournament':'Tournament', 'city': 'City', 'country': 'Country'}, axis=1, inplace=True)
            break
        else:
            dff = dff[dff['away_team'].isin([xaxis_column_name])]
            dff.rename({'home_score1': 'Home Score', 'away_score1': 'Away Score',
                        'date': 'Date', 'home_team': 'Home Team', 'away_team': 'Away Team',
                        'tournament':'Tournament', 'city': 'City', 'country': 'Country'}, axis=1, inplace=True)
            break
    #title that will update as the graph does
    title = '<b>Table shows all {} games for {} in {}</b><br>'.format(yaxis_column_name, xaxis_column_name, year_value)
    #create the table
    new_table_figure = ff.create_table(dff)
    #update margins
    new_table_figure.layout.margin.update({'t':75, 'l':5})
    #assign it the title
    new_table_figure.layout.update({'title': title})
    #change the font size slightly
    for i in range(len(new_table_figure.layout.annotations)):
        new_table_figure.layout.annotations[i].font.size = 11

    return new_table_figure


if __name__ == '__main__':
    app.run_server()



#TO DO
#ability to select opponent team
#get data from an API
#filter on tournament data
#regression
