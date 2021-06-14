# Import required libraries
from datetime import date
import pandas as pd
import numpy as np
import json

# import dash app related packages
from flask import Flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objs as go
import copy

# import helper functions
from src.visualization.visualize_transactions import executed_transactions_time_series, executed_transactions_heatmap_summary
from src.data.welfare_baseline import read_NTC_file, NTC_preparation

# Multi-dropdown options
app = dash.Dash(__name__)


# set layout
layout = dict(
    autosize=True,
    # automargin=True,
    margin=dict(
        l=30,
        r=30,
        b=20,
        t=40
    ),
    legend=dict(font=dict(size=10), orientation='h'),
    plot_bgcolor='white'
)

# helper functions


def df_to_plotly(df):

    diff = df.values.tolist()

    return {'z': diff,
            'x': df.columns.tolist(),
            'y': df.index.tolist()}


def format_thousands(number_string):

    n = 3
    rest = len(number_string) % 3
    split_number = [number_string[:rest]] if rest != 0 else []
    split_number = split_number + [number_string[rest+i:rest+i+n]
                                   for i in range(0, len(number_string)-rest, n)]
    return ','.join(split_number)


# load NTC
NTC = read_NTC_file("../data/external/NTC_DEandCH_2019.csv")
NTC = NTC_preparation(NTC)

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id='aggregate_data'),
        html.Div(
            [
                html.Div(
                    [
                        html.H2(
                            'Lead Time Reductions in the Cross-border Intraday Power Market Trading',

                        ),
                        html.P(
                            'Price, Volumes, Revenue and Flows Analysis for 2019 DE EPEX Intraday-order book contracts closing within 30 to 60 mins before delivery',
                        )
                    ],

                    className='eight columns'
                )
            ],
            id="header",
            className='row',
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            'Choose month period',
                            className="control_label"
                        ),
                        dcc.RangeSlider(
                            id='year_slider',
                            min=0,
                            max=11,
                            marks={
                                0: 'Jan',
                                1: 'Feb',
                                2: 'Mar',
                                3: 'Apr',
                                4: 'May',
                                5: 'Jun',
                                6: 'Jul',
                                7: 'Aug',
                                8: 'Sep',
                                9: 'Oct',
                                10: 'Nov',
                                11: 'Dec',
                            },
                            value=[4, 6],
                            className="dcc_control"
                        ),
                        html.P(
                            'Vary the closing price of the contracts wrt to Hystorical Price',
                            className="control_label"
                        ),
                        dcc.Slider(
                            id='closing_price',
                            min=0,
                            max=10,
                            marks={
                                0: '0 %',
                                1: '10 %',
                                2: '20 %',
                                3: '30 %',
                                4: '40 %',
                                5: '50 %',
                                6: '60 %',
                                7: '70 %',
                                8: '80 %',
                                9: '90 %',
                                10: '100 %',

                            },
                            value=5,
                            className="dcc_control"
                        ),
                        html.P(
                            'Choose day to analyse:',
                            className="control_label"
                        ),
                        dcc.DatePickerSingle(
                            id='my-date-picker-single',
                            min_date_allowed=date(2019, 1, 1),
                            max_date_allowed=date(2019, 10, 20),
                            initial_visible_month=date(2019, 10, 1),
                            date=date(2019, 4, 25)
                        ),
                        html.P("Daily Additional Energy Traded Volumes Flows"),
                        dcc.Graph(id='piePlotVolume')
                    ],
                    className="pretty_container four columns"
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P(
                                            "Additional No. of Contract Closed"),
                                        html.H6(
                                            id="contractsClosed",
                                            className="info_text"
                                        )
                                    ],
                                    id="cC",
                                    className="pretty_container"
                                ),

                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.P(
                                                    "Welfare Gain CH [EUR]"),
                                                html.H6(
                                                    id="welfarech",
                                                    className="info_text"
                                                )
                                            ],
                                            id="wch",
                                            className="pretty_container"
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "Welfare Gain DE [EUR]"),
                                                html.H6(
                                                    id="welfarede",
                                                    className="info_text"
                                                    # TO DO: format the output with commas toallow better reading of millions
                                                )
                                            ],
                                            id="wde",
                                            className="pretty_container"
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    'Daily Quantity Overview',
                                                    className="control_quantity"
                                                ),
                                                dcc.RadioItems(
                                                    id='monthly_plot_type',
                                                    options=[
                                                        {'label': 'Daily Volumes ',
                                                         'value': 'daily_volume'},
                                                        {'label': 'Daily Avg. Price',
                                                         'value': 'daily_avg_price'},
                                                        {'label': 'Daily Maximum Price ',
                                                         'value': 'daily_max_price'}
                                                    ],
                                                    value='daily_volume',
                                                    labelStyle={
                                                        'display': 'inline-block'},
                                                    className="dcc_control"
                                                ),
                                            ],
                                            id="quantity_controller",
                                            className="pretty_container"
                                        ),
                                    ],
                                    id="tripleContainer",
                                )

                            ],
                            id="infoContainer",
                            className="row"
                        ),
                        # here a bar graph showing the additional total energy traded per month is shown: one for CH-DE flow and another for DE-CH flows
                        html.Div(
                            [html.H5("Monthly Statistics"),
                                dcc.Graph(
                                    id='energyTraded',
                            )
                            ],
                            id="countGraphContainer",
                            className="pretty_container"
                        )
                    ],
                    id="rightCol",
                    className="eight columns"
                )
            ],
            className="row"
        ),
        html.Div(
            [
                # heatmap comparison / net transfer capacity available and used / weekly average hydro prices
                html.Div(
                    [
                        html.H5("DE-CH Heatmap of hourly price differences "),
                        dcc.Graph(id='heatmap-comparison')
                    ],
                    className='pretty_container six columns',
                ),
                # daily price and moving average price variation comparison of before and after
                html.Div(
                    [
                        html.H5("Daily Price Movements"),
                        dcc.Graph(id='daily-time')
                    ],
                    className='pretty_container six columns',
                ),
            ],
            className='row'
        ),
        html.Div(
            [
                # plot of used net transfer capacity
                html.Div(
                    [
                        html.H5("Daily CH-DE Net Transfer Capacity Usage"),
                        dcc.Graph(id='net-transfer-capacity')
                    ],
                    className='pretty_container seven columns',
                ),
                # plot of CO2 emission savings
                html.Div(
                    [
                        dcc.Graph(id='hourly-bid-ask')
                    ],
                    className='pretty_container five columns',
                ),
            ],
            className='row'
        ),
    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)


# Helper functions


# Create callbacks
@app.callback(
    Output('piePlotVolume', 'figure'),
    Input('my-date-picker-single', 'date'))
def update_pieplot(date_value):

    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df_transactions = pd.read_csv(
            f'../data/processed/EPEX_spot_continous_baseline_pipeline_2019_14-03-2021 21:00:40/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv'
        )

        data = [dict(
            type='pie',
            labels=['CH - DE Flows', 'DE - CH Flows'],
            values=[df_transactions['Executed Volume']
                    [df_transactions['match_binary_outcome'] == 1].sum(), 100],
            name='CH-DE Daily Volume Exchnages',
            hole=0.5,
            hoverinfo="text+value+percent",
            textinfo="label+percent+name",
            autosize=False,
            height=20,
            width=10
        )]

        figure = dict(data=data, layout=layout)

    return figure


@app.callback(
    Output('net-transfer-capacity', 'figure'),
    Input('my-date-picker-single', 'date'))
def update_net_transfer_capacity(date_value):

    if date_value is not None:

        d_hours = dict(zip(range(24), [0]*24))

        date_object = date.fromisoformat(date_value)
        NTC_selection = NTC[(NTC['start_time'].dt.day == date_object.day) & (
            NTC['start_time'].dt.month == date_object.month)]

        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df_transactions = pd.read_csv(
            f'../data/processed/EPEX_spot_continous_baseline_pipeline_2019_14-03-2021 21:00:40/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv'
        )

        mask = df_transactions['match_binary_outcome'] == 1
        df_transactions_filtered = df_transactions[mask]
        times = pd.to_datetime(
            df_transactions_filtered['End Validity Date'])

        gb = df_transactions_filtered['Executed Volume'].groupby(
            times.dt.hour)

        ntc_gb = NTC_selection['CH to DE_Actual value (MW)'].groupby(
            NTC_selection['start_time'].dt.hour)

        d_hours_new = dict(zip(list(gb.groups.keys()), gb.sum()))
        d_hours.update(d_hours_new)
        figure = go.Figure(data=[go.Bar(name='Used Net Transfer Capacity MWh',
                                        x=list(d_hours.keys()),
                                        y=list(d_hours.values())),
                                 go.Bar(name='Available Net Transfer Capacity MWh',
                                        x=list(ntc_gb.groups.keys()),
                                        y=list(ntc_gb.mean()))],
                           layout=layout)

        return figure


@ app.callback(
    Output('heatmap-comparison', 'figure'),
    [Input('my-date-picker-single', 'date'),
     Input('closing_price', 'value')])
def update_hetamap(date_value, price):

    marks_price = {
        0: 0,
        1: 0.1,
        2: 0.2,
        3: 0.3,
        4: 0.4,
        5: 0.5,
        6: 0.6,
        7: 0.7,
        8: 0.8,
        9: 0.9,
        10: 1,
    }
    p = marks_price[price]

    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df_transactions = pd.read_csv(
            f'../data/processed/EPEX_spot_continous_baseline_pipeline_2019_14-03-2021 21:00:40/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv'
        )

        daily_execution_price_stat, daily_execution_volume_stat, daily_execution_price_stat_marginal = executed_transactions_heatmap_summary(
            df_transactions, plot=False, return_updated_transactions=True)

        df_plot = (daily_execution_price_stat_marginal -
                   daily_execution_price_stat)/daily_execution_price_stat

        figure = go.Figure(data=go.Heatmap(df_to_plotly(df_plot),
                                           hovertemplate='Max ΔPrice wrt History: %{z:.2%}<br>Statistic: %{x}<br>Hour: %{y}<extra></extra>',
                                           colorbar={
            "title": 'Max ΔPrice wrt History', 'tickformat': '%'}
        )
        )

    return figure


@ app.callback(
    Output('daily-time', 'figure'),
    [Input('my-date-picker-single', 'date'),
     Input('closing_price', 'value')])
def update_output_table(date_value, price):

    marks_price = {
        0: 0,
        1: 0.1,
        2: 0.2,
        3: 0.3,
        4: 0.4,
        5: 0.5,
        6: 0.6,
        7: 0.7,
        8: 0.8,
        9: 0.9,
        10: 1,
    }
    p = marks_price[price]

    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        month = str(date_object.month) if len(
            str(date_object.month)) > 1 else '0'+str(date_object.month)

        day = str(date_object.day) if len(
            str(date_object.day)) > 1 else '0'+str(date_object.day)

        # load and read corresponding file
        df_transactions = pd.read_csv(
            f'../data/processed/EPEX_spot_continous_baseline_pipeline_2019_14-03-2021 21:00:40/2019-{month}/Updated Transactions/DE_2019{month}{day}.csv'
        )

        time, outputseries = executed_transactions_time_series(
            df_transactions, plot=False, output_series_='exec_price_updated_transactions_comparison', rolling_time='1H', new_data_type=False)

        data = [
            dict(
                type='scatter',
                mode='lines',
                name='Historical Execution Price €',
                x=time,
                y=outputseries[0],
                line=dict(
                    shape="spline",
                    smoothing=3,
                    width=1,
                    color='#fac1b7'
                )
            ),
            dict(
                type='scatter',
                mode='lines',
                name='A posteriori Execution Price €',
                x=time,
                y=outputseries[0]-p*(outputseries[1]-outputseries[0]),
                line=dict(
                    shape="spline",
                    smoothing=3,
                    width=1,
                    color='#849E68'
                )
            )
        ]

        figure = dict(data=data, layout=layout)

    return figure


@ app.callback(
    [Output('energyTraded', 'figure'),
     Output('contractsClosed', 'children'),
     Output('welfarech', 'children'),
     Output('welfarede', 'children')],
    [Input('year_slider', 'value'),
     Input('closing_price', 'value'),
     Input('monthly_plot_type', 'value')])
def update_volume_traded(month_numbers, price, quantity):

    # which month to show
    range_months = [month_numbers[0]+1, month_numbers[1]+2]
    marks_price = {
        0: 0,
        1: 0.1,
        2: 0.2,
        3: 0.3,
        4: 0.4,
        5: 0.5,
        6: 0.6,
        7: 0.7,
        8: 0.8,
        9: 0.9,
        10: 1,
    }
    p = marks_price[price]

    # which quanity to show
    quantity_dict = {'daily_volume': ['Total Volume Traded', 'Total Volume Traded CH-DE'],
                     'daily_avg_price': ['Avg Historical Price', 'Avg a Posteriori Price'],
                     'daily_max_price': ['Max Historical Price', 'Max a Posteriori Price']}
    name_quantity_dict = {'daily_volume': ['Historical Volume Traded [MWh]', 'Potential Additional Volume Traded CH-DE [MWh]'],
                          'daily_avg_price': ['Avg Daily Historical Price [€]', 'Avg Daily a Posteriori Price [€]'],
                          'daily_max_price': ['Max Daily Historical Price [€]', 'Max Daily a Posteriori Price [€]']}

    q = quantity_dict[quantity]
    name_q = name_quantity_dict[quantity]

    p_q = 0 if quantity == 'daily_volume' else p

    # load and read corresponding files
    df_summary = pd.read_csv(
        '../data/processed/summary_analysis_baseline_window_interest_2019_14-03-2021 21:00:40/2019_14-03-2021 21:00:40_summary.csv')
    time_ = pd.to_datetime(df_summary['time']).dt.month
    df_s = df_summary[(time_ > range_months[0]) & (time_ < range_months[1])]

    data = [
        dict(
            type='scatter',
            mode='lines',
            name=name_q[0],
            x=df_s['time'],
            y=df_s[q[0]],
            line=dict(
                shape="spline",
                smoothing=1,
                width=1,
                color='#fac1b7'
            ),
        ),
        dict(
            type='scatter',
            mode='lines',
            name=name_q[1],
            x=df_s['time'],
            y=df_s[q[1]]+p_q*(df_s[q[0]]-df_s[q[1]]),
            line=dict(
                shape="spline",
                smoothing=1,
                width=1,
                color='#849E68'
            ),
        )]

    figure = dict(data=data, layout=layout)

    # update fiches
    contracts = df_s['Additional Contracts Closed']

    diff_welf = df_s['CH-DE Revenue Max']-df_s['CH-DE Revenue Min']
    welfCH = df_s['CH-DE Revenue Min'] + p*diff_welf
    welfDE = df_s['CH-DE Revenue Max']-welfCH

    return figure, format_thousands(str(contracts.sum())), format_thousands(str(welfCH.sum()).split('.')[0]), format_thousands(str(welfDE.sum()).split('.')[0])


# Main
if __name__ == '__main__':
    app.run_server(debug=True)
